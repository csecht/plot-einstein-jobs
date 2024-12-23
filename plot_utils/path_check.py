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
from plot_utils import URL
from plot_utils.utils import MY_OS

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

        sys.exit(f'The test data file, {TESTFILE} was not found.'
                  ' Was it moved or renamed?\n'
                  f'It can be downloaded from {URL}')

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

                sys.exit(f"The custom path, {custom_path}, is not working.\n")

    # Supported system platforms have already been verified in plot_utils __init__.py.
    elif not Path.is_file(default_datapath[MY_OS]):
        badpath_msg = (
            '\nThe job_log data file is not in its expected default path:\n'
            f'     {default_datapath[MY_OS]}\n'
            'You can enter a custom path for your job_log file in'
            f" the configuration file: {CFGFILE}.")
        sys.exit(badpath_msg)

    validate_datafile(default_datapath[MY_OS])
    return default_datapath[MY_OS]


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


def valid_path_to(relative_path: str) -> Path:
    """
    Get correct path to program's directory/file structure
    depending on whether program invocation is a standalone app or
    the command line. Works with symlinks. Allows command line
    using any path; does not need to be from parent directory.
    _MEIPASS var is used by distribution programs from
    PyInstaller --onefile; e.g. for images dir.

    :param relative_path: Program's local dir/file name, as string.
    :return: Absolute path as pathlib Path object.
    """
    # Modified from: https://stackoverflow.com/questions/7674790/
    #    bundling-data-files-with-pyinstaller-onefile and PyInstaller manual.
    if getattr(sys, 'frozen', False):  # hasattr(sys, '_MEIPASS'):
        base_path = getattr(sys, '_MEIPASS', Path(Path(__file__).resolve()).parent)
        valid_path = Path(base_path) / relative_path
    else:
        valid_path = Path(Path(__file__).parent, f'../{relative_path}').resolve()
    return valid_path
