import pyqtgraph as pg
import numpy as np
import pytplot
from pyqtgraph.Qt import QtGui, QtCore


def get_data(names):
    # Just grab variables that are spectrograms.
    valid_vars = list()
    for n in names:
        if pytplot.data_quants[n].spec_bins is not None:
            valid_vars.append(n)
    return valid_vars


def get_plot_labels(names):
    # Get labels and axis types for plots.
    plot_labels = {}
    for n in names:
        if pytplot.data_quants[n].spec_bins is not None:
            zlabel = pytplot.data_quants[n].zaxis_opt['axis_label']
            ztype = pytplot.data_quants[n].zaxis_opt['z_axis_type']
            ytype = pytplot.data_quants[n].yaxis_opt['y_axis_type']
            xtype_interactive = pytplot.data_quants[n].interactive_xaxis_opt['xi_axis_type']
            ytype_interactive = pytplot.data_quants[n].interactive_yaxis_opt['yi_axis_type']
            plot_labels[n] = [zlabel, ytype, ztype, xtype_interactive, ytype_interactive]
    return plot_labels


def get_bins(var):
    # Get bins to be plotted.
    bins = list()
    for name, values in pytplot.data_quants[var].spec_bins.iteritems():
        # name = variable name
        # value = data in variable name
        bins.append(values.values[0])
    return bins


def get_z_t_values(var):
    # Get data to be plotted and time data for indexing.
    time_values = list()
    z_values = list()
    for r, rows in pytplot.data_quants[var].data.iterrows():
        # r = time
        # rows = the flux at each time, where each row signifies a different time
        time_values.append(r)
        z_values.append(rows.values)
    return time_values, z_values


def set_x_range(var, x_axis_log, plot):
    # Check if plot's x range has been set by user. If not, range is automatically set.
    if 'xi_range' in pytplot.data_quants[var].interactive_xaxis_opt:
        if x_axis_log:
            plot.setXRange(np.log10(pytplot.data_quants[var].interactive_xaxis_opt['xi_range'][0]),
                           np.log10(pytplot.data_quants[var].interactive_xaxis_opt['xi_range'][1]),
                           padding=0)
        elif not x_axis_log:
            plot.setXRange(pytplot.data_quants[var].interactive_xaxis_opt['xi_range'][0],
                           pytplot.data_quants[var].interactive_xaxis_opt['xi_range'][1], padding=0)


def set_y_range(var, y_axis_log, plot):
    # Check if plot's y range has been set by user. If not, range is automatically set.
    if 'yi_range' in pytplot.data_quants[var].interactive_yaxis_opt:
        if y_axis_log:
            plot.setYRange(np.log10(pytplot.data_quants[var].interactive_yaxis_opt['yi_range'][0]),
                           np.log10(pytplot.data_quants[var].interactive_yaxis_opt['yi_range'][1]),
                           padding=0)
        elif not y_axis_log:
            plot.setYRange(pytplot.data_quants[var].interactive_yaxis_opt['yi_range'][0],
                           pytplot.data_quants[var].interactive_yaxis_opt['yi_range'][1], padding=0)


def interactive2dplot():
    """ If the interactive option is set to True in tplot, this function will take in the stored tplot variables
    and create a 2D interactive window that will pop up when any one of the tplot variables is plotted (so long
    as at least one of the tplot variables is a spectrogram). If the mouse hovers over a spectrogram plot, data
    for that point in time on the spectrogram plot will be plotted in the 2D interactive window. If the mouse
    hovers over a non-spectrogram plot, the 2D interactive window returns an empty plot. """

    # Grab names of data loaded in as tplot variables.
    names = list(pytplot.data_quants.keys())
    # Get data we'll actually work with here.
    valid_variables = get_data(names)

    # Don't plot anything unless we have spectrograms with which to work.
    if valid_variables:
        # Get z label
        labels = get_plot_labels(names)

        # Put together data in easy-to-access format for plots.
        data = {}
        for name in valid_variables:
            bins = get_bins(name)
            time_values, z_values = get_z_t_values(name)
            data[name] = [bins, z_values, time_values]

        # Set up the 2D interactive plot
        pytplot.interactive_window = pg.GraphicsWindow()
        pytplot.interactive_window.resize(1000, 600)
        pytplot.interactive_window.setWindowTitle('Interactive Window')
        plot = pytplot.interactive_window.addPlot(title='2D Interactive Plot', row=0, col=0)
        # Make it so that whenever this first starts up, you just have an empty plot
        plot_data = plot.plot([], [])

        # The following update function is passed to change_hover_time in the HoverTime class
        # defined in __init__.py. For reference, "t" essentially originates inside of
        # TVarFigure(1D/Spec/Alt/Map), inside the _mousemoved function. It calls
        # "self._mouseMovedFunction(int(mousePoint.x()))" and that is called every time the mouse is
        # moved by Qt. Therefore, it gives the location of the mouse on the x axis. In tplot,
        # mouse_moved_event is set to pytplot.hover_time.change_hover_time, so the mouseMovedFunction
        # is pytplot.hover_time.change_hover_time. Thus, whenever change_hover_time is called, it
        # calls every other function that is registered. Since the below function update() is
        # registered as a listener, it'll update whenever hover_time is updated.
        # to the HoverTime class with "t" as the input.

        # TL;DR, t comes from getting the mouse location in pyqtgraph every time the mouse is moved
        # and the below function will update the plot's position as the mouse is moved.
        def update(t, name):
            if name in valid_variables:
                # When hovering over a spectrogram plot...
                # First, get the time closest to the x position the mouse is over.
                time_array = np.array(data[name][2])
                array = np.asarray(time_array)
                idx = (np.abs(array - t)).argmin()
                # If user indicated they wanted the interactive plot's axes to be logged, log 'em.
                # But first make sure that values in x and y are loggable!
                x_axis = False
                y_axis = False
                # Checking x axis
                if np.nanmin(data[name][0][:]) < 0:
                    print('Negative data is incompatible with log plotting.')
                elif np.nanmin(data[name][0][:]) >= 0 and labels[name][3] == 'log':
                    x_axis = True
                # Checking y axis
                if np.nanmin(list(data[name][1][idx])) < 0:
                    print('Negative data is incompatible with log plotting')
                elif np.nanmin(list(data[name][1][idx])) >= 0 and labels[name][4] == 'log':
                    y_axis = True
                # Set plot labels
                plot.setLabel('bottom', '{} bins'.format(labels[name][0]))
                plot.setLabel('left', '{}'.format(labels[name][0]))
                plot.setLogMode(x=x_axis, y=y_axis)
                # Update x and y range if user modified it
                set_x_range(name, x_axis, plot)
                set_y_range(name, y_axis, plot)
                # Plot data based on time we're hovering over
                plot_data.setData(data[name][0][:], list(data[name][1][idx]))
            else:
                # Cover the situation where you hover over a non-spectrogram plot.
                plot.setLogMode(False, False)
                plot.setLabel('bottom', '')
                plot.setLabel('left', '')
                plot_data.setData([], [])

        # Make the above function called whenever hover_time is updated.
        pytplot.hover_time.register_listener(update)
