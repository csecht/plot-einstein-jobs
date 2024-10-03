"""
General housekeeping utilities.
Functions:
manage_args - Command line argument handler.
quit_gui -  Error-free and informative exit from the program.
"""
# Copyright (C) 2022 C.S. Echt under GNU General Public License'

# Standard library imports
import argparse
import logging
import platform
import sys
from datetime import datetime

# Third party imports.
import matplotlib.pyplot as plt

# Local application imports
import plot_utils
from plot_utils import path_check

MY_OS = sys.platform[:3]
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """
    Changes an unhandled exception to go to stdout rather than
    stderr. Ignores KeyboardInterrupt so a console program can exit
    with Ctrl + C. Relies entirely on python's logging module for
    formatting the exception. Sources:
    https://stackoverflow.com/questions/6234405/
    logging-uncaught-exceptions-in-python/16993115#16993115
    https://stackoverflow.com/questions/43941276/
    python-tkinter-and-imported-classes-logging-uncaught-exceptions/
    44004413#44004413

    Usage: For developers; use in mainloop,
     - sys.excepthook = utils.handle_exception
     - app.report_callback_exception = utils.handle_exception

    Args:
        exc_type: The type of the BaseException class.
        exc_value: The value of the BaseException instance.
        exc_traceback: The traceback object.

    Returns: None

    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception",
                 exc_info=(exc_type, exc_value, exc_traceback))


def check_platform() -> None:
    if MY_OS not in 'lin, win, dar':
        print(f'Platform <{sys.platform}> is not supported.\n'
              'Windows, Linux, and MacOS (darwin) are supported.')
        sys.exit(1)

    # Need to account for scaling in Windows10 and earlier releases.
    if MY_OS == 'win':
        from ctypes import windll

        if platform.release() < '10':
            windll.user32.SetProcessDPIAware()
        else:
            windll.shcore.SetProcessDpiAwareness(1)


def manage_args() -> tuple:
    """
    Allow handling of command line arguments. The --about information
    can also be accessed from the GUI as a pop-up window.

    :return: Tuple of booleans for --test and --utc options (default: False).
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provide description, version, GNU license',
                        action='store_true',
                        default=False)
    parser.add_argument('--test',
                        help='Plot sample test data instead of your job_log data.',
                        action='store_true',
                        default=False,
                        )
    parser.add_argument('--utc',
                        help='Plot UTC datetime instead of local datetime.',
                        action='store_true',
                        default=False,
                        )

    args = parser.parse_args()

    about_text = (f'{sys.modules["__main__"].__doc__}\n'
                  f'{"Author:".ljust(13)}{plot_utils.__author__}\n'
                  f'{"Version:".ljust(13)}{plot_utils.__version__}\n'
                  f'{"Status:".ljust(13)}{plot_utils.__status__}\n'
                  f'{"URL:".ljust(13)}{plot_utils.URL}\n'
                  f'{plot_utils.__copyright__}'
                  f'{plot_utils.__license__}\n')

    if args.about:
        print('====================== ABOUT START ====================')
        print(about_text)
        print('====================== ABOUT END ====================')

        sys.exit(0)

    if args.test:
        data_path = path_check.set_datapath(use_test_file=True)
    else:
        data_path = path_check.set_datapath()

    return args.test, args.utc, data_path


def quit_gui(mainloop, keybind=None) -> None:
    """
    Error-free and informative exit from the program.
    Called from widget or keybindings.
    Explicitly closes all Matplotlib objects and their parent tk window
    when the user closes the plot window with the system's built-in
    close window icon ("X") or key command. This is required to cleanly
    exit and close the tk thread running Matplotlib.

    :param mainloop: The main tk.Tk() window running in the mainloop.
    :param keybind: Implicit keyboard event passed from bind().
    :return: None
    """

    print('\n*** User quit the program. ***\n')

    plt.close('all')
    mainloop.update_idletasks()
    mainloop.after(200)
    mainloop.destroy()

    return keybind


def utc_offset_sec() -> float:
    """Return offset of UTC time from local time, as float seconds."""
    local_tz = datetime.now().astimezone().tzinfo
    offset_sec = (datetime.now(local_tz)
                  .utcoffset()
                  .total_seconds())
    return offset_sec
