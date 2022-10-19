"""
General housekeeping utilities.
Functions:
manage_args - Command line argument handler.
quit_gui -  Error-free and informative exit from the program.
"""
# Copyright (C) 2022 C.S. Echt under GNU General Public License'

# Standard library imports
import argparse
import sys

# Third party imports.
import matplotlib.pyplot as plt

# Local application imports
import plot_utils
from __main__ import __doc__


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

    about_text = (f'{__doc__}\n'
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

    return args.test, args.utc


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
    """

    print('\n*** User quit the program. ***\n')

    # pylint: disable=broad-except
    try:
        plt.close('all')
        mainloop.update_idletasks()
        mainloop.after(200)
        mainloop.destroy()
    except Exception as err:
        print(f'An error occurred: {err}')
        sys.exit('Program exit with unexpected condition.')

    return keybind
