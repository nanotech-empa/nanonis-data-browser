### Load libaries
import ipywidgets as ipw
import checkbox
import likebutton
import tagging
from helpers import fname_generator, tempdir_maker



# Reloads the modules if they have been changed
import importlib
importlib.reload(checkbox)
checkbox = checkbox.checkbox
importlib.reload(likebutton)
likebutton = likebutton.likebutton
importlib.reload(tagging)
tagging = tagging.tagging




# Libraries for plotting
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from IPython.display import Image, display

### databrowser_dat_viewer

class databrowser_dat_viewer():
    """
    Small DAT Viewer for the Data Browser
    """
    def __init__(self,data_id:str,db,**kwargs):

        self.data_id = data_id
        self.db = db
        self.dat = db.db_get_data(self.data_id)

        # **kwargs
        if 'parameter_print_names' in kwargs:
            self.parameter_print_names = kwargs['parameter_print_names']
        else:
            self.parameter_print_names = None

        if 'prerender' in kwargs:
            self.prerender = kwargs['prerender']
        else:
            self.prerender = False

        # Create widgets
        self.create_widgets()
        self.update_plot(None)


    def create_widgets(self):
        
        # Menu Options
        self.checkbox = checkbox(self.data_id,self.db)
        self.button_checkbox = self.checkbox.button_checkbox
        self.likebox = likebutton(self.data_id,self.db)
        self.button_like = self.likebox.button_like
        self.open_viewer = ipw.Button(description='',icon='eye',tooltip='Open in Viewer',layout=ipw.Layout(width='40px'))
        self.open_viewer.on_click(self.open_with_specific_viewer)
        self.tagging = tagging(self.data_id,self.db)
        self.tag_widgets = self.tagging.tag_widgets

        # Display Options
        self.selector_xchannel = ipw.Dropdown(options=[],description='Channel X',disabled=False,layout=ipw.Layout(width='150px'))
        self.selector_ychannel = ipw.Dropdown(options=[],description='Channel Y',disabled=False,layout=ipw.Layout(width='150px'))

        self.get_current_display_properties()
        self.selector_xchannel.observe(self.update_plot, names='value')
        self.selector_ychannel.observe(self.update_plot, names='value')

        # Displays
        self.outdat = ipw.Output()
        self.parameter_area = ipw.HTML(value='',layout=ipw.Layout(width='200px',height='100px'))

        # Create Layout
        self.widgets = ipw.VBox([ipw.HBox([self.button_checkbox,self.button_like,self.open_viewer,self.tag_widgets]),
                                 ipw.HBox([self.outdat,
                                           ipw.VBox([self.selector_xchannel,self.selector_ychannel,self.parameter_area])])])

    ### Database Interaction ###

    def get_current_display_properties(self):
        """
        Updates the current display_properties of the DAT image with the data_id in the widgets.
        
        Accessed button properties:
        self.selector_xchannel.options
        self.selector_xchannel.value 
        self.selector_ychannel.options
        self.selector_ychannel.value

        Accessed database properties:
        self.db.db_get(self.data_id,'current_xchannel')
        self.db.db_get(self.data_id,'current_ychannel')
        self.db.db_get(self.data_id,'fxchannel')
        self.db.db_get(self.data_id,'fychannel')
        """
        
        # self.selector_xchannel.options
        self.selector_xchannel.options = self.db.db_get(self.data_id,'channel_names')

        # self.selector_xchannel.value
        current_xchannel = self.db.db_get(self.data_id,'current_xchannel')
        if current_xchannel == None:
            current_xchannel = self.db.db_get(self.data_id,'fxchannel')
            if current_xchannel == None:
                print('databrowser_dat_viewer.get_current_display_properties: Error: No fxchannel found in database.')
                current_xchannel = self.selector_xchannel.options[0]
            self.db.db_write(self.data_id,'current_xchannel',current_xchannel)
        self.selector_xchannel.value = current_xchannel

        # self.selector_ychannel.options
        self.selector_ychannel.options = self.db.db_get(self.data_id,'channel_names')

        # self.selector_ychannel.value
        current_ychannel = self.db.db_get(self.data_id,'current_ychannel')
        if current_ychannel == None:
            current_ychannel = self.db.db_get(self.data_id,'fychannel')
            if current_ychannel == None:
                print('databrowser_dat_viewer.get_current_display_properties: Error: No fychannel found in database.')
                current_ychannel = self.selector_ychannel.options[0]
            self.db.db_write(self.data_id,'current_ychannel',current_ychannel)
        self.selector_ychannel.value = current_ychannel

    def write_display_properties(self):
        """
        Writes the current display_properties of the SXM image with the data_id in the widgets to the database.

        Accessed button properties:
        self.selector_xchannel.value
        self.selector_ychannel.value

        Accessed database properties:
        self.db.db_write(self.data_id,'current_xchannel')
        self.db.db_write(self.data_id,'current_ychannel')
        """

        # self.selector_xchannel.value
        self.db.db_write(self.data_id,'current_xchannel',self.selector_xchannel.value)

        # self.selector_ychannel.value
        self.db.db_write(self.data_id,'current_ychannel',self.selector_ychannel.value)

    ### Callbacks ###

    def open_with_specific_viewer(self,b):
        self.db.open_with_viewer_data_id = self.data_id

    def update_plot(self,b):
        self.plot_dat()
        self.parameter_print()
        self.write_display_properties()

    ### Plotting ###

    def parameter_print(self):

        # Update self.parameter_area.value
        self.parameter_area.value = ''
        
    def plot_dat(self,**kwargs):
        """
        Plot the selected data using the chosen settings.
        
        Optional arguments:
        prerender_only (bool): If True, only prerender the image and do not display it (requires optional arguments xchannel and ychannel)

        """

        if 'prerender_only' in kwargs:
            prerender_only = kwargs['prerender_only']
        else:
            prerender_only = False
        if 'xchannel' in kwargs:
            prerender_xchannel = kwargs['xchannel']
        else:
            if prerender_only == True:
                print('databrowser_dat_viewer.plot_dat: Error: prerender_only is True but xchannel not specified.')
                prerender_only = False
        if 'ychannel' in kwargs:
            prerender_ychannel = kwargs['ychannel']
        else:
            if prerender_only == True:
                print('databrowser_dat_viewer.plot_dat: Error: prerender_only is True but ychannel not specified.')
                prerender_only = False

        
        run_plot = False
        if self.prerender == True:
            prerendered = self.db.db_get(self.data_id,'prerender')
            if prerendered == None:
                run_plot = True
            else:
                prerendered_key = "("+self.selector_xchannel.value+","+self.selector_ychannel.value+")"
                if prerendered_key in prerendered.keys():
                    # Load image_path from prerender dictionary
                    prerender_path = prerendered[prerendered_key]
                    with self.outdat:
                        self.outdat.clear_output(wait=True)
                        display(Image(filename=prerender_path))
                else:
                    run_plot = True
        else:
            run_plot = True

        if run_plot == True:

            # Set up the plot figure and axes

            self.fig_combined, self.ax_dat = plt.subplots(1,1,figsize=(2,2))
            self.outdat.clear_output(wait=True)
            
            # Get parameters from the GUI elements
            selector_xchannel_value = self.selector_xchannel.value
            selector_ychannel_value = self.selector_ychannel.value

            # Define other parameters
            direction = 'forward'

            # Plot
            if selector_xchannel_value in self.db.db_get(self.data_id,'channel_names'):
                if selector_ychannel_value in self.db.db_get(self.data_id,'channel_names'):
                    # Get data
                    (dat_x,x_unit) = self.db.db_get_data(self.data_id).get_channel(selector_xchannel_value,direction)
                    (dat_y,y_unit) = self.db.db_get_data(self.data_id).get_channel(selector_ychannel_value,direction)
                            
                    # Calculatation options for dat_x and dat_y
                    line1, = self.ax_dat.plot(
                        dat_x,
                        dat_y,
                        label=self.data_id)
                else:
                    print('Y channel ',selector_xchannel_value,' in ',self.data_id, ' not found')
            else:
                print('X channel ',selector_ychannel_value,' in ',self.data_id, ' not found')
            
            plt.title(str(self.data_id),fontsize=8)

            # Create prerender image and save path to database
            if self.prerender == True:

                # Save plot as png to tempdir
                tempdir = tempdir_maker(self.db)
                new_filename = fname_generator(tempdir,'temp_dat_', 'png')
                prerender_path = tempdir+'/'+new_filename
                self.fig_combined.savefig(prerender_path, dpi=100, bbox_inches='tight')

                # Save prerender_path to database
                current_prerender = self.db.db_get(self.data_id,'prerender')
                if current_prerender == None:
                    current_prerender = {}

                prerender_key = "("+selector_xchannel_value+","+selector_ychannel_value+")"
                current_prerender.update({prerender_key:prerender_path})
                self.db.db_write(self.data_id,'prerender',current_prerender)
                
            #self.out_com.clear_output()
            with self.outdat:
                plt.show()
        
