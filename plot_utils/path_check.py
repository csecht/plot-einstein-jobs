"""
Establish paths for data files.
Functions:
set_datapath - Return Path of text file to be read into a DataFrame.
Constants:
CFGFILE - the configuration file for setting a custom data file path.
TESTFILE - Path to the sample data file to test the program's functions.
MY_OS - the system platform in use.

"""
# Copyright (C) 2021 C. Echt under GNU General Public License'

import sys
from pathlib import Path

import plot_utils

CFGFILE = Path('plot_cfg.txt').resolve()
TESTFILE = Path('plot_utils/testdata.txt')
MY_OS = sys.platform[:3]


def set_datapath(use_test_file=False) -> Path:
    """
    Set the Path() for a data text file to be read into a DataFrame.

    :param use_test_file: True sets the data file path to read the
        sample data file provided with this distribution. The default
        False sets path to a BOINC E@H job_log file, either default path
        or a user-defined custom path.
    :return: pathlib Path object.
    """
    if use_test_file and Path.is_file(TESTFILE):
        return TESTFILE
    elif not Path.is_file(TESTFILE):
        notest = (f'The sample data file, {TESTFILE} was not found.'
                  ' Was it moved or renamed?\n'
                  f'It can be downloaded from {plot_utils.URL}')
        sys.exit(notest)

    if Path.is_file(CFGFILE):
        cfg_text = Path(CFGFILE).read_text()
        for line in cfg_text.splitlines():
            if '#' not in line and 'custom_path' in line:
                parts = line.split()
                del parts[0]
                custom_path = " ".join(parts)
                if Path.is_file(Path(custom_path)):
                    return Path(custom_path)
                else:
                    errmsg = f"The custom path, {custom_path}, is not working.\n"
                    sys.exit(errmsg)

    default_logpath = {
        'win': Path('/ProgramData/BOINC/job_log_einstein.phys.uwm.edu.txt'),
        'lin': Path('/var/lib/boinc/job_log_einstein.phys.uwm.edu.txt'),
        'dar': Path('/Library/Application Support/BOINC Data/job_log_einstein.phys.uwm.edu.txt')
    }

    if MY_OS in default_logpath:
        if not Path.is_file(default_logpath[MY_OS]):
            badpath_msg = (
                '\nThe file is not in its expected default path: '
                f'{default_logpath[MY_OS]}\n'
                'You should enter your custom path for the job_log file in'
                f" the configuration file: {CFGFILE}.")
            sys.exit(badpath_msg)
        else:
            return default_logpath[MY_OS]
