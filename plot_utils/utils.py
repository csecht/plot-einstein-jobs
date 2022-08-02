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
import __main__
import plot_utils


def manage_args() -> bool:
    """Allow handling of command line arguments.

    :return: True if --test argument used (default: False).
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provide description, version, GNU license',
                        action='store_true',
                        default=False)
    parser.add_argument('--test',
                        help='Plot test_arg data instead of your job_log data.',
                        action='store_true',
                        default=False,
                        )

    args = parser.parse_args()

    if args.about:
        print(__main__.__doc__)
        print(f'{"Author:".ljust(13)}', plot_utils.__author__)
        print(f'{"Version:".ljust(13)}', plot_utils.__version__)
        print(f'{"Status:".ljust(13)}', plot_utils.__dev_status__)
        print(f'{"URL:".ljust(13)}', plot_utils.URL)
        print(plot_utils.__copyright__)
        print(plot_utils.LICENSE)
        sys.exit(0)

    return args.test


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
