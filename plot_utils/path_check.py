"""
Establish paths and validity for data files.
Functions:
set_datapath - Return Path of text file to be read into a DataFrame.
validate_datafile - Check that file starts with timestamp; exit if not.

Constants:
CFGFILE - the configuration file for setting a custom data file path.
TESTFILE - Path to the sample data file to test the program's functions.
"""
# Copyright (C) 2021-2022 C. Echt under GNU General Public License'

# Standard library imports
import sys
from pathlib import Path
from re import match

# Local application imports
import plot_utils  # Need URL from __init__.py
from plot_utils import platform_check as chk

CFGFILE = Path('plot_cfg.txt').resolve()
TESTFILE = Path('plot_utils/testdata.txt')


def set_datapath(use_test_file=False) -> Path:
    """
    Set the Path() for a data text file to be read into a DataFrame.

    :param use_test_file: True sets the data file path to read the
        sample data file provided with this distribution. The default
        False sets path to a BOINC E@H job_log file, either default path
        or a user-defined custom path.
    :return: pathlib Path object.
    """

    default_datapath = {
        'win': Path('/ProgramData/BOINC/job_log_einstein.phys.uwm.edu.txt'),
        'lin': Path('/var/lib/boinc/job_log_einstein.phys.uwm.edu.txt'),
        'dar': Path('/Library/Application Support/BOINC Data/job_log_einstein.phys.uwm.edu.txt')
    }

    if use_test_file:
        if Path.is_file(TESTFILE):
            validate_datafile(TESTFILE)
            return TESTFILE

        notest = (f'The sample data file, {TESTFILE} was not found.'
                  ' Was it moved or renamed?\n'
                  f'It can be downloaded from {plot_utils.URL}')
        sys.exit(notest)

    elif Path.is_file(CFGFILE):
        cfg_text = Path(CFGFILE).read_text()
        for line in cfg_text.splitlines():
            if '#' not in line and 'custom_path' in line:
                print('Now reading the file from the configured custom path.')
                parts = line.split()
                del parts[0]
                custom_path = " ".join(parts)
                if Path.is_file(Path(custom_path)):
                    return Path(custom_path)

                errmsg = f"The custom path, {custom_path}, is not working.\n"
                sys.exit(errmsg)

    # Supported system platforms have already been verified in plot_utils __init__.py.
    elif not Path.is_file(default_datapath[chk.MY_OS]):
        badpath_msg = (
            '\nThe job_log data file is not in its expected default path:\n'
            f'     {default_datapath[chk.MY_OS]}\n'
            'You can enter a custom path for your job_log file in'
            f" the configuration file: {CFGFILE}.")
        sys.exit(badpath_msg)

    validate_datafile(default_datapath[chk.MY_OS])
    return default_datapath[chk.MY_OS]


def validate_datafile(filepath: Path) -> None:
    """
    Verify that the job log data file has the expected data format.
    Check only the timestamp on the file's first line.

    :return: None
    """

    # Expected first line of the plot log file has this structure:
    # 1555763244 ue 3228.229683 ct 132.696900 fe 525000000000000 nm LATeah1049R_180.0_0_0.0_49704725_1 et 808.042782 es 0
    with open(filepath, encoding='utf-8') as file:
        # At the start of the 1st line, look for a 10-digit timestamp + 1 space.
        if not match(r'\d{10}\s', file.readline(11)):
            sys.exit(f'*** Sorry, but the job log file {filepath}\n'
                     '    does not contain usable data. ***\n'
                     '    The first line should start with a'
                     ' BOINC reporting timestamp of 10 digits (Epoch seconds).')
