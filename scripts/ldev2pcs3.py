#!/usr/bin/env python2

import argparse
import re
import sys
import subprocess


skip_pattern = re.compile('^\s*(#.*)?\n?$')
def should_skip(line):
    """Returns true is the line contains only a comment or whitespace"""
    if skip_pattern.match(line):
        return True
    return False

# Assume line in ldev looks like this for zfs:
#  jet1   jet2   lquake-MGS0000  zfs:jet1-1/mgs
def process_ldev_line(line):

    fields = line.split()
    if len(fields) != 4:
        sys.stderr.write('Wrong number of fields in line: '+line+'\n')
        sys.exit(1)
    node1, node2, lustre_service_name, zfs_dataset = fields
    nodes = [node1, node2]

    if zfs_dataset[:4] != 'zfs:':
        sys.stderr.write('Fourth field is not prefixed with "zfs:"\n')
        sys.exit(1)
    zfs_dataset = zfs_dataset[4:]

    if 'MGS' in lustre_service_name and lustre_service_name != 'MGS':
        sys.stderr.write('WARNING: Target name "'+lustre_service_name+'" is not valid, using "MGS" instead\n')
        lustre_service_name = 'MGS'

    for node in nodes:
        if node not in all_nodes:
            all_nodes.append(node)
    zpool = zfs_dataset.split('/')[0]

    if zpool in all_zpools:
        # Sanity check
        if not set(all_zpools[zpool]).issuperset(set(nodes)):
            sys.stderr.write('zpool "'+zpool+'" already instantiated on incompatible set of nodes\n')
            sys.exit(1)
    elif zpool not in all_zpools:
        # Add zpool resource
        all_zpools[zpool] = nodes
        zpool_order.append(zpool)

    all_lustre_services[lustre_service_name] = (zpool, zfs_dataset)
    lustre_service_order.append(lustre_service_name)

def deduce_cluster_name():
    """Deduce the name of the cluster from the name of one node.

    Strip the trailing digits off the end of the node name, and that probably
    gives us the name of the cluster.  At least at LLNL."""
    global all_nodes

    node = all_nodes[0]

    return node.rstrip('0123456789')

def run(cmd, args):
    print(cmd)

    if args.dry_run:
        return

    try:
        rc = subprocess.call(cmd, shell=True)
        if rc < 0:
            print(f"Child was terminated by signal {-rc}", file=sys.stderr)
        elif rc > 0:
            print(f"Error: {rc}", file=sys.stderr)
    except OSError as e:
        print("Execution failed: {e}", file=sys.stderr)

def configure_location(resource, nodes, fixed_score_string=None):
    if fixed_score_string is None:
        score = len(nodes)*10
    else:
        score = fixed_score_string
    for node in nodes:
        id = resource + '_' + node
        cmd = 'pcs constraint location add ' + id + ' ' + resource
        cmd += ' ' + node + ' ' + str(score)
        cmd += ' ' + 'resource-discovery=exclusive'
        run(cmd, args)
        if fixed_score_string is None:
            score -= 10

def configure(args):
    cmd = 'pcs cluster setup --force --local'
    cmd += ' --name ' + args.cluster_name
    cmd += ' ' + args.mgmt_node
    run(cmd, args)
    run('pcs cluster start', args)
    run('pcs property set symmetric-cluster=false', args)
    run('pcs property set stonith-action=off', args)
    run('pcs property set batch-limit=100', args)
    run('pcs property set cluster-recheck-interval=60', args)

    node_str = ','.join(all_nodes)
    cmd = 'pcs stonith create fence_pm fence_powerman'
    cmd += ' ipaddr=' + args.fence_ipaddr
    cmd += ' ipport=' + args.fence_ipport
    cmd += ' pcmk_host_check=static-list pcmk_host_list="' + node_str + '"'
    run(cmd, args)
    run('pcs constraint location fence_pm prefers ' + args.mgmt_node, args)

    for node in all_nodes:
        run('pcs resource create ' + node + ' ocf:pacemaker:remote' +
            ' server=e' + node + ' reconnect_interval=60', args)
        run('pcs constraint location ' + node +
            'prefers ' + args.mgmt_node, args)

    for zpool in zpool_order:
        # Handle a zpool name that conflicts with a node name
        if zpool in all_nodes:
            zpool_resource = zpool + '_zpool'
        else:
            zpool_resource = zpool
        nodes = all_zpools[zpool]
        cmd = 'pcs resource create ' + zpool_resource + ' ocf:llnl:zpool'
        cmd += ' import_options="-f -N -d /dev/disk/by-vdev"'
        cmd += ' pool=' + zpool
        cmd += ' op start timeout=805'
        run(cmd, args)

        # We want suspended pools to immediately fail over to the other node.
        run('pcs resource meta ' + zpool_resource +
            ' migration-threshold=1', args)

        configure_location(zpool_resource, nodes)

    # Make sure that the MGS is the first service, so we can easily add order
    # constraint for the MGS before all other services.
    i = lustre_service_order.index('MGS')
    mgs = lustre_service_order.pop(i)
    lustre_service_order.insert(0, mgs)

    for service in lustre_service_order:
        zpool=all_lustre_services[service][0]
        # Handle a zpool name that conflicts with a node name
        if zpool in all_nodes:
            zpool_resource = zpool+'_zpool'
        else:
            zpool_resource = zpool
        dataset=all_lustre_services[service][1]
        nodes = all_zpools[zpool]
        cmd = 'pcs resource create ' +service + 'ocf:llnl:lustre'
        cmd += ' dataset=' + dataset + ' mountpoint=/mnt/lustre/' + service
        run(cmd, args)
        if service != 'MGS':
            run('pcs constraint order MGS then ' + service + ' kind=Optional')
        run('pcs constraint order ' + zpool_resource +
            ' then ' + service, args)
        cmd = ('pcs constraint colocation add ' + service +
               'with ' + zpool_resource + 'score=INFINITY')
        run(cmd, args)
        configure_location(service, nodes)

description="""
Input an ldev.conf file to generate
the complimentary Pacemaker cib.xml file.
""".strip()

parser = argparse.ArgumentParser(description=
parser.add_argument(
    'infile',
    nargs='?',
    type=argparse.FileType('r'),
    default=sys.stdin,
    help='ldev.conf file name (default=stdin)',
)
parser.add_argument(
    '--mgmt-node',
    help= (
        'Hostname of management node '
        '(by default uses hostname of current node)'
    )
)
parser.add_argument(
    '--cluster-name',
    help= (
        'Name of the cluster '
        '(by default guessed from a random hostname in infile)'
    )
)
parser.add_argument(
    '--fence-ipaddr',
    default='localhost',
    help='Powerman server IP address (for fence_powerman, default localhost)'
)
parser.add_argument(
    '--fence-ipport',
    default='10101',
    help='Powerman server port number (for fence_powerman, default 10101)'
)
parser.add_argument(
    '--dry-run',
    action='store_true'
)

def main():

    all_nodes = []
    all_zpools = {}
    zpool_order = []
    all_lustre_services = {}
    lustre_service_order = []
    args = parser.parse_args()

    # turn it into a list, even if there is only one node
    if args.mgmt_node is None:
        import socket
        args.mgmt_node = socket.gethostname()

    for line in args.infile:
        if should_skip(line):
            continue
        process_ldev_line(line, all_nodes, all_zpools, all_lustre_services)

    if args.cluster_name is None:
        args.cluster_name = deduce_cluster_name()

    configure(args)

if __name__ == "__main__":
    main()
