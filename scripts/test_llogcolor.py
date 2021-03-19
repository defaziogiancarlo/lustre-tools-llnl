'''
A test suite for comparing the text output
of llogcolor versions.

It is set up to work for both python2 and python3.

The pager is skipped for these tests, and the
color control codes go strait to a file, so they get saved.

There are a bunch of input, and corresponding output files.
'''

import filecmp
import sys
import tempfile

import pytest

if '3.6' in sys.version:
    import llogcolor3 as llogcolor
elif '2.7' in sys.version:
    import llogcolor2 as llogcolor

#### paths to input logs ###

# small and simple log file, all of the same thread ID
in_simple = '/home/defazio1/lustre-tools-llnl/scripts/color_samples/sample_logs'


### paths to output logs ###

# [-P, -C, in_simple]
out_P_C_simple = '/home/defazio1/lustre-tools-llnl/scripts/color_samples/sample_logs'

def cmp_stdout_to_ref(test_args, reference):
    '''
    Compare stdout to reference file.
    run llogcolor with test_args and write
    the output to a temporary file.
    Then compare that file to a reference file.
    Return True if the files match and False otherwise.
    '''

    # stdout will be changed to the temporary file
    # for when llogcolor outputs stuff
    # so save the real stdout now
    real_stdout = sys.stdout

    # create a temporary file
    # and set aim stdout at it
    fd, filename = tempfile.mkstemp()
    f = open(filename, 'wb')
    sys.stdout = f

    # run llogcolor with test_args and save the return value
    ret_val = llogcolor.main(test_args=test_args)


    # put stdout back to normal
    sys.stdout = real_stdout
    print(ret_val)
    # not sure if this is neccesary, but want it
    # it all written befor the compare
    f.close()

    files_match = filecmp.cmp(reference, filename)
    print(files_match)
    #f.close()

    success = ((ret_val is None) or (ret_val == 0)) and files_match
    return success

def test_P_C_simple():
    '''
    read a log file in, and just send it unmodified to
    stdout
    '''

    # no pager, no color
    test_args = ['-P', '-C', in_simple]
    reference = out_P_C_simple

    assert cmp_stdout_to_ref(test_args, reference)





# read in several files
# read in 0 files
# check that highlighting a specific pid works
# read files with lines that aren't matched by the log file regex
# I'm not really sure if it's supposed to be writing to files, but check that
# and if it does, check that the files are created/deleted correctly
# give it file names that don't exist or have bad permissions
# can I test the case where sys.stout is not a TTY
