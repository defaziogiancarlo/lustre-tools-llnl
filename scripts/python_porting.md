# Notes and Issues on porting from Python 2 to 3

The following scripts are listed as *yes* in the *keep*
column of the conversion ticket.

The plan is to create a branch (currently called `python3`)
that's set up for converting and testing each script, and
another that has just the conversion
results. That is, the python2 and testing infrastucture removed.

The cleaner branch will then be used for pull requests back
to the llnl main branch.

The scripts to be ported (this list could change) are \
[ldev2pcs](https://github.com/LLNL/lustre-tools-llnl/blob/master/scripts/ldev2pcs) \
[lflush](https://github.com/LLNL/lustre-tools-llnl/blob/master/scripts/lflush) \
[llogcolor](https://github.com/LLNL/lustre-tools-llnl/blob/master/scripts/llogcolor) \
[zfsobj2fid](https://github.com/LLNL/lustre-tools-llnl/blob/master/scripts/zfsobj2fid) \
[zpool](https://github.com/LLNL/lustre-tools-llnl/blob/master/scripts/zpool) \
and... \
[lustre?](https://github.com/LLNL/lustre-tools-llnl/blob/master/scripts/lustre)

## General Notes on the porting process
The only deprecated library is [optparse](https://docs.python.org/2.7/library/optparse.html).
Fortunately, a replacement, [argparse](https://docs.python.org/3.6/library/argparse.html) exists and
is pretty similar to `optparse`.

Some of the more annoying issues so far have been due to
the changes made regarding strings and bytes from python2 to python3.

Theres a style guide for LC new python at confluence+LC STAFF+python+style+guide
The important stuff is:
- compatible with version 3.6+
- use the checks \
  [black](https://github.com/psf/black) \
  [flake8](https://flake8.pycqa.org/en/latest/) \
  [bandit](https://bandit.readthedocs.io/en/latest/)

Also, there aren't any tests that I know of, so some amount of testing
needs to be done to ensure the new versions function like the old ones.

As for how to test, many of these scripts are meant to be used
from the command line and parse their arguments with `optparse` (or `argparse`).
It's possible to script this by making a slight modification, where a list of strings,
instead of `sys.argv` is given to the parser.

For the testing branch, I've removed the `#!` from the files and created a
<scrip\_name>2.py and <script\_name>3.py or each, and am using conda to change
between python environments. Then a check is done based on the interpreter version
to import the python version 2 or 3 script. Then, in both cases, I can run the test
script with `pytest` and the correct version will be tested based on the conda environment.

Also, everyting should be tested on lustre 2.12 and 2.14.
Another issue is that I'm testing on my personal computer, eventually I'll need to test on the llnl
systems. The python2 version I got from conda doesn't match what llnl has right now.

## Comments and TODOs for each script

### ldev2pcs

### lflush

### llogcolor

For some tests I'm redirecting output to files and checking against
what I think is a known good output. Sending output to a file prevent the
terminal color codes from being eaten by the terminal before I can see them.
Although speeking of seeing, the colors look the same between versions.

I've converted `optparse` to `argparse` and also from
[os.path](https://docs.python.org/3.6/library/os.path.html)
to [pathlib](https://docs.python.org/3.6/library/pathlib.html) for file and directory
path operations.

#### outstanding issues
Issue with bytes vs. strings. This might be due to how I'm testing,
which involves redirecting `sys.stdout` to a file opened in binary mode.

When no file is given, python2 version echos input with I press `enter`,
python3 version does not.
I don't know if this really matters, I don't think it's meant to be used with manual
input. Both versions work with multiple files, or with stdin redirection from a file.

Some ideas for more tests:
- read in several files
- read in 0 files
- check that highlighting a specific pid works
- read files with lines that aren't matched by the log file regex
- I'm not really sure if it's supposed to be writing to files, but check that
- and if it does, check that the files are created/deleted correctly
- give it file names that don't exist or have bad permissions
- can I test the case where sys.stout is not a TTY
### zfsobj2fid

Very short, I've added `argparse` based argument parsing.

#### outstanding issues
I need to get some examples of zfs object with lustre fids in them
to be able to know if the functionality is being changed or not.

### zpool

### lustre
