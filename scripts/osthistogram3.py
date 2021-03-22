# Copyright (c) 2011, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
# Written by Christopher J. Morrone <morrone2@llnl.gov>
# LLNL-CODE-468512
#
# This file is part of lustre-tools-llnl.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License (as published by the
# Free Software Foundation) version 2, dated June 1991.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# terms and conditions of the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import argparse
import glob
import subprocess
import sys

def tally_file_stripe_info(filename, bin_dict):
    try:
        lfs = subprocess.run(['lfs', 'getstripe', '-q', filename],
                               stdout=subprocess.PIPE)
    except:
        print('Unable to execute "lfs".', file=sys.stderr)
        return 3
    for line in lfs.stdout:
        args = line.split()
        if len(args) != 4:
            continue
        if args[0] == 'obdidx':
            continue
        obdidx = int(args[0])
        if obdidx not in bin_dict:
            bin_dict[obdidx] = 0
        bin_dict[obdidx] += 1



parser = argparse.ArgumentParser(
    description=(
        "A tool to analyze a directory of files and "
        "report a hostogram of the striped assigne to each ost."
    )
)
parser.add_argument(
    'files',
    nargs="*",
    help="the input files, defaults to stdin if none specified",
)

def main():
    args = parser.parse_args()
    bins = {}
    if not args.files:
        # read file names from stdin
        for f in sys.stdin:
            tally_file_stripe_info(f.strip(), bins)
    else:
        for arg in sys.argv[1:]:
            if arg == '-':
                # read file names from stdin
                for f in sys.stdin:
                    tally_file_stripe_info(f.strip(), bins)
            else:
                for f in glob.glob(arg):
                    tally_file_stripe_info(f, bins)

    biggest = max(bins.values())
    if biggest < 66:
        scaler = 1
    else:
        scaler = biggest / 66.0
    keys = bins.keys()
    keys.sort()
    for key in keys:
        print "%-6d %-5d " % (key, bins[key]),
        print("-" * int(bins[key] / scaler))
    return 0

if __name__ == '__main__':
    sys.exit(main())
