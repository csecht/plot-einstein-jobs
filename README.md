# Project: plot-einstein@home

## plot_jobs.py

The Python script, plot_jobs.py, uses Matplotlib to draw plots from data  in the Einstein@Home
BOINC client job log file. Task times vs. datetime, task counts/day vs.
datetime, and task frequency (Hz) vs. task time (sec) can be plotted for
various E@H Projects recorded in a job log. A job log file can store
records of reported tasks for up to about three years of full-time work.

### Usage:
From within the program's folder, use one of these commands,
       depending on your system:

            python plot_jobs.py
            py plot_jobs.py
            ./plot_jobs.py
            python3 plot_jobs.py
Basic help: `python plot_jobs.py --help`

Information: `python plot_jobs.py --about`

Plot sample data: `python plot_jobs.py --test`

NOTE: Depending on your system, there may be a slight lag when switching
      between plots, so be patient and avoid the urge to start clicking
      around to speed things up. For the typical job log, hundreds of
      thousands to millions of data points can be plotted.

Using the navigation bar, plots can be zoomed-in, panned, restored to
previous views, and copied to PNG files.
When no navigation bar buttons are active, clicking on a cluster or
single data point shows task names near the click coordinates.
The "Log counts" button shows summary counts of all tasks, by Project.

The default configuration reads the job_log_einstein.phys.uwm.edu.txt
file in its default BOINC location. If you have changed the default
location, or want to plot data from an archived job_logs, then
enter a custom full file path in the provided plot_cfg.txt file.

### Requirements:
Python 3.7 or later, plus Matplotlib, Pandas, and Numpy.
This program was developed in Python 3.8-3.9.

For quick installation of the required Python PIP packages:
from the downloaded GitHub repository folder, run this command

    pip install -r requirements.txt
Alternative commands (system dependent):

    python -m pip install -r requirements.txt
    python3 -m pip install -r requirements.txt
    py -m pip install -r requirements.txt

### Screenshots:
![plot all sample data](images/test_start.png)

Opening window using the sample data option.

![plot log GW data](images/gw_all.png)

Plot of all gravitational wave tasks, by sub-series, over time.

![plot GW freq](images/gw_freq.png)

Plot of gravitational wave task frequencies vs. task times.

![plot zoom and pick](images/gwfreq+zoom+pick.png)

Zoom-in on lowest frequency group of tasks, then click in bottom cluster to obtain details of tasks near those plot coordinates.

### Keyboard shortcuts for navigation bar buttons and actions

| Action     | Key                      | Description                                                                |
|------------|--------------------------|----------------------------------------------------------------------------|
| fullscreen | f, ctrl+f                | toggle full screen display of plot window                                  |
| pan        | p                        | toggle click & drag to shift plot area, rt-click & drag zooms x and y axis |
| zoom       | o                        | toggle mouse rectangle draw to zoom in on a plot area                      |
| prior view | left arrow, c, backspace | back to previous custom view                                               |
| next view  | right arrow, v           | forward to next custom view                                                |
| home       | h, r, home               | return to original view                                                    |
| save       | s, ctrl+s                | save current view as PNG file                                              |
| quit       | ctrl+w, cmd+w, q         | close the plot window                                                      |
| grid       | g                        | cycle grid lines show/hide                                                 |
| grid_minor | G                        | cycle grid lines show/hide                                                 |
| yscale     | l                        | toggle scaling of y-axes ('log'/'linear')                                  |
| xscale     | k, L                     | toggle scaling of x-axes ('log'/'linear')                                  |

When no navigation bar buttons are active, clicking on task points displays task details.