# Copyright 2018 Regents of the University of Colorado. All Rights Reserved.
# Released under the MIT license.
# This software was developed at the University of Colorado's Laboratory for Atmospheric and Space Physics.
# Verify current version before use at: https://github.com/MAVENSDC/PyTplot

import os
import pickle
import numpy as np
from pytplot import data_quants, tplot_opt_glob
from .options import options 
from .store_data import store_data
from .tplot_options import tplot_options
from scipy.io import readsav


def tplot_restore(filename):
    """
    This function will restore tplot variables that have been saved with the "tplot_save" command.
    
    .. note::
        This function is compatible with the IDL tplot_save routine.  
        If you have a ".tplot" file generated from IDL, this procedure will restore the data contained in the file.
        Not all plot options will transfer over at this time.   
    
    Parameters:
        filename : str
            The file name and full path generated by the "tplot_save" command.  
            
    Returns:
        None
    
    Examples:
        >>> # Restore the saved data from the tplot_save example
        >>> import pytplot
        >>> pytplot.restore('C:/temp/variable1.pytplot')

    """
    
    #Error check
    if not (os.path.isfile(filename)):
        print("Not a valid file name")
        return
    
    #Check if the restored file was an IDL file
    
    if filename.endswith('.tplot'):
        temp_tplot = readsav(filename)
        for i in range(len(temp_tplot['dq'])):
            data_name = temp_tplot['dq'][i][0].decode("utf-8")
            temp_x_data = temp_tplot['dq'][i][1][0][0]
            #Pandas reads in data the other way I guess
            if len(temp_tplot['dq'][i][1][0][2].shape) == 2:
                temp_y_data = np.transpose(temp_tplot['dq'][i][1][0][2])
            else:
                temp_y_data = temp_tplot['dq'][i][1][0][2]
            
            
            #If there are more than 4 fields, that means it is a spectrogram 
            if len(temp_tplot['dq'][i][1][0]) > 4:
                temp_v_data = temp_tplot['dq'][i][1][0][4]
                
                #Change from little endian to big endian, since pandas apparently hates little endian
                #We might want to move this into the store_data procedure eventually
                if (temp_x_data.dtype.byteorder == '>'):
                    temp_x_data = temp_x_data.byteswap().newbyteorder()
                if (temp_y_data.dtype.byteorder == '>'):
                    temp_y_data = temp_y_data.byteswap().newbyteorder()
                if (temp_v_data.dtype.byteorder == '>'):
                    temp_v_data = temp_v_data.byteswap().newbyteorder()
                
                store_data(data_name, data={'x':temp_x_data, 'y':temp_y_data, 'v':temp_v_data})
            else:
                #Change from little endian to big endian, since pandas apparently hates little endian
                #We might want to move this into the store_data procedure eventually
                if (temp_x_data.dtype.byteorder == '>'):
                    temp_x_data = temp_x_data.byteswap().newbyteorder()
                if (temp_y_data.dtype.byteorder == '>'):
                    temp_y_data = temp_y_data.byteswap().newbyteorder()
                store_data(data_name, data={'x':temp_x_data, 'y':temp_y_data})
            
            if temp_tplot['dq'][i][3].dtype.names is not None:
                for option_name in temp_tplot['dq'][i][3].dtype.names:
                    options(data_name, option_name, temp_tplot['dq'][i][3][option_name][0])
            
            data_quants[data_name].trange =  temp_tplot['dq'][i][4].tolist()
            data_quants[data_name].dtype =  temp_tplot['dq'][i][5]
            data_quants[data_name].create_time =  temp_tplot['dq'][i][6]
        
            for option_name in temp_tplot['tv'][0][0].dtype.names:
                if option_name == 'TRANGE':
                    tplot_options('x_range', temp_tplot['tv'][0][0][option_name][0])
                if option_name == 'WSIZE':
                    tplot_options('wsize', temp_tplot['tv'][0][0][option_name][0])
                if option_name == 'VAR_LABEL':
                    tplot_options('var_label', temp_tplot['tv'][0][0][option_name][0])
            if 'P' in temp_tplot['tv'][0][1].tolist():
                for option_name in temp_tplot['tv'][0][1]['P'][0].dtype.names:
                    if option_name == 'TITLE':
                        tplot_options('title', temp_tplot['tv'][0][1]['P'][0][option_name][0])
                
        #temp_tplot['tv'][0][1] is all of the "settings" variables
            #temp_tplot['tv'][0][1]['D'][0] is "device" options
            #temp_tplot['tv'][0][1]['P'][0] is "plot" options
            #temp_tplot['tv'][0][1]['X'][0] is x axis options
            #temp_tplot['tv'][0][1]['Y'][0] is y axis options
        ####################################################################
    else:
        temp = pickle.load(open(filename,"rb"))
        num_data_quants = temp[0]
        for i in range(0, num_data_quants):
            data_quants[temp[i+1].name] = temp[i+1]
        tplot_opt_glob = temp[num_data_quants+1]
    
    return