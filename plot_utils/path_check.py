from pathlib import Path
import sys

CFGFILE = Path('plot_cfg.txt').resolve()
TESTFILE = Path('plot_utils/testdata.txt')
MY_OS = sys.platform[:3]


def set_datapath(do_test=None) -> Path:
    """
    Set the Path() for a data text file to be read into a DataFrame.

    :param do_test: Any value, but expecting descriptive 'do test' to
        indicate that the non-default path should be set to read the
        sample data file provided with the distribution. The default
        path is the BOINC E@H job_log file.
    :return: pathlib Path object.
    """
    if do_test:
        if Path.is_file(TESTFILE):
            return TESTFILE

    if Path.is_file(CFGFILE):
        cfg_text = Path(CFGFILE).read_text()
        for line in cfg_text.splitlines():
            if '#' not in line and 'custom_path' in line:
                parts = line.split()
                del parts[0]
                custom_path = " ".join(parts)

                return Path(custom_path)

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
