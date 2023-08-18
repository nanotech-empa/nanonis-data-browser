"""
Author:         Lysander Huberich
Description:    Viewer for .dat files 
IDEAS:          Mark x,y with the curser in the image
                Show metadata
"""

### Imports ###
import ipywidgets as ipw
import os
import importlib
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pylab as pl
from matplotlib.colors import LogNorm
from scipy.interpolate import UnivariateSpline
import pyperclip
from IPython.display import display, clear_output

# Import spmpy
sys.path.append('K:/Labs205/labs/THz-STM/Software/spmpy')
import spmpy_terry as spmpy   # <--- spmpy has other methods

# Import custom modules
import tagging
importlib.reload(tagging)
tagging = tagging.tagging
import likebutton
importlib.reload(likebutton)
likebutton = likebutton.likebutton
import checkbox
importlib.reload(checkbox)
checkbox = checkbox.checkbox
importlib.reload(spmpy)
from helpers import fname_generator,copy_to_clipboard,tempdir_maker


### dat_viewer class ###

class dat_viewer():

    """
    Output:
        self.dat_viewer_widgets
    """

    def __init__(self,db,**kwargs):
        """
        IDEA: Combine dat_viewer with databrowser_dat_viewer and independent prerender
        Optional Keywords:
            mode: str ['dat_viewer','dat_viewer_mini','prerender']
                'dat_viewer':      Full dat viewer
                'dat_viewer_mini': Mini dat viewer for the databrowers
                'prerender':       Prerender the dat_viewer_mini
                'render':          Plot the dat_viewer and return figure
            data_id: str or list[str] required if mode == 'dat_viewer_mini' or mode == 'prerender'
        """

        self.db = db

        # Parse optional keywords
        if 'mode' in kwargs: 
            self.mode = kwargs['mode']
        else:
            self.mode = 'dat_viewer'

        if 'data_id' in kwargs:
            self.data_id = kwargs['data_id']
        else:
            if self.mode == 'dat_viewer_mini' or self.mode == 'prerender' or self.mode == 'render':
                print('dat_viewer.__init__: selected mode is',self.mode,'but no data_id was given.')
                return
        
        # self.mode == 'dat_viewer_mini'
        if self.mode == 'dat_viewer_mini':
            if 'parameter_print_names' in kwargs:
                self.parameter_print_names = kwargs['parameter_print_names']
            else:
                self.parameter_print_names = None

            if 'prerender' in kwargs:
                self.prerender = kwargs['prerender']
            else:
                self.prerender = False

        # self.mode == 'dat_viewer'
        if self.mode == 'dat_viewer':
            # Is there data to display?
            if len(list(self.db.db_prop['data_prop'].keys())) == 0:
                self.dat_viewer_widgets = ipw.HTML(value="dat_viewer.__init__: db.db_data['data_prop'] is empty. No database initalized?")
                return
            
            # Is there any dat file in the database?
            self.all_data_ids_dat, file_type_found_dat = self.db.file_type_finder('dat')
            if not file_type_found_dat:
                self.dat_viewer_widgets = ipw.HTML(value="dat_viewer.__init__: No .dat file found in database.")
                return
            
            # Is there any sxm file in the database?
            self.all_data_ids_sxm, file_type_found_sxm = self.db.file_type_finder('sxm')
            
            # Check if there is a dat_viewer_value in the database otherwise set it to the first dat file
            dat_viewer_value = self.db.db_get([],'dat_viewer_value',super_prop=True)
            if dat_viewer_value == None:
                self.data_id = self.all_data_ids_dat[0]
                # TODO: db.db_write([],'dat_viewer_value',self.data_id,super_prop=True)
            else:
                self.data_id = dat_viewer_value

            # Initialize the widgets
            self.create_widgets()
        
        if self.mode == 'render':
            pass


    def create_widgets(self):
        
        ## Create widget layout defaults
        self.layout_visible = ipw.Layout(width='200px')
        self.layout_hidden = ipw.Layout(height='0px',width='0px',visibility='hidden')
        

        ## .dat file viewer options: First y axis
        self.dat_select1 = ipw.SelectMultiple(options=self.all_data_ids_dat,description='Select .dat', disabled=False,layout=ipw.Layout(height='200px',width='200px'))
        self.selector_xchannel1 = ipw.Dropdown(options=[],description='x channel',disabled=False,layout=self.layout_visible)
        self.selector_ychannel1 = ipw.Dropdown(options=[],description='y channel',disabled=False,layout=self.layout_visible)
        self.direction1 = ipw.Dropdown(options=['forward','backwards'],value='forward',description='Direction:',disabled=False,layout=self.layout_visible)
        self.display_legend = ipw.Dropdown(options=['Show','Dont show'],value='Show',description='Legend',disabled=False,layout=self.layout_visible)
        calc_options = ['Y(X)','Y(X) _ spline','dY/dX _ spline','dY/dX _ grad']
        self.selector_calc_options1 = ipw.Dropdown(options=calc_options,description='calc options',disabled=False,layout=self.layout_visible)
        self.spline_smoothness1 = ipw.FloatText(value=9e-10,step=1e-10,description='spline',disabled=False,layout=self.layout_hidden)

        ## .dat file viewer options: First y axis only
        self.multi_y_plot = ipw.Dropdown(options=['Single','Multi'],value='Single',description='Multiplot Y',disabled=False,layout=self.layout_visible)
        self.multi_y_plot.observe(self.multi_y_plot_visibility_change, names='value')
        self.modify_legend = ipw.Button(description='Modify Legend',icon='fa-navicon',disabled=False,tooltip='Modify legend. Needs to be in the form data_id: mylabel',layout=self.layout_visible)
        self.modify_legend_show = False
        self.modify_legend.on_click(self.modify_legend_visibility_change)
        self.modify_legend_textarea = ipw.Textarea(value='',placeholder='Legend',description='',disabled=False,layout=self.layout_hidden)
        self.modify_legend_sumbit= ipw.Button(description='',icon='fa-plus-square-o',disabled=False,tooltip='Update legend',layout=self.layout_hidden)
        self.modify_legend_sumbit.on_click(self.modify_legend_sumbit_click)
        self.modify_legend_sumbit_value = False

        self.dat_viewer_options1 = ipw.VBox([self.dat_select1,
                                        self.selector_xchannel1,
                                        self.selector_ychannel1,
                                        self.selector_calc_options1,
                                        self.spline_smoothness1,
                                        self.direction1,
                                        self.display_legend,
                                        self.multi_y_plot,
                                        self.modify_legend,
                                        self.modify_legend_textarea,
                                        self.modify_legend_sumbit])

        ## .dat file viewer options: Second y axis
        self.dat_select2 = ipw.SelectMultiple(options=self.all_data_ids_dat,description='Select .dat', disabled=False,layout=self.layout_hidden)
        self.selector_ychannel2 = ipw.Dropdown(options=[],description='y2 channel',disabled=False,layout=self.layout_hidden)
        self.direction2 = ipw.Dropdown(options=['forward','backwards'],value='forward',description='Direction2:',disabled=False,layout=self.layout_hidden)
        self.selector_calc_options2 = ipw.Dropdown(options=calc_options,description='calc options2',disabled=False,layout=self.layout_hidden)
        self.spline_smoothness2 = ipw.FloatText(value=9e-10,step=1e-10,description='spline2',disabled=False,layout=self.layout_hidden)

        self.dat_viewer_options2 = ipw.VBox([self.dat_select2,
                                                self.selector_ychannel2,
                                                self.selector_calc_options2,
                                                self.spline_smoothness2,
                                                self.direction2])

        ## .sxm file viewer options
        self.sxm_select = ipw.Select(options=self.all_data_ids_sxm,description='Select .sxm',disabled=False,layout=self.layout_hidden)
        self.selector_sxm_channel = ipw.Dropdown(options=[],description='channel',disabled=False,layout=self.layout_hidden)
        self.sxm_direction = ipw.Dropdown(options=['forward','backwards'],value='forward',description='Direction',disabled=False,layout=self.layout_hidden)
        self.sxm_flatten = ipw.Dropdown(options=['False','True'],value='False',description='Flatten',disabled=False,layout=self.layout_hidden)
        self.sxm_offset = ipw.FloatText(value=0.0,description='Offset',disabled=False,layout=self.layout_hidden)
        self.sxm_scale = ipw.Dropdown(options=['Linear','Log'],value='Linear',description='Scale',disabled=False,layout=self.layout_hidden)
        self.sxm_show_params = ipw.Dropdown(options=['Show','Dont show'],value='Dont show',description='Show Params',disabled=False,layout=self.layout_hidden)
        self.positions = ipw.Dropdown(options=['Show','Dont show'],value='Dont show',description='Positions',disabled=False,layout=self.layout_hidden)

        self.sxm_viewer_options = ipw.VBox([self.sxm_select,
                                            self.selector_sxm_channel,
                                            self.sxm_direction,
                                            self.sxm_flatten,
                                            self.sxm_offset,
                                            self.sxm_scale,
                                            self.sxm_show_params,
                                            self.positions])


        ## Return Options
        self.layout_button = ipw.Layout(width='40px')
        
        
        self.likebutton = likebutton(self.data_id,self.db)
        self.like_button_out = self.likebutton.output
        self.tag_widgets = tagging(self.data_id,self.db).tag_widgets

        self.button_return_data = ipw.Button(description='',icon='angle-double-right',disabled=False,tooltip='Copy code to clipboard to access current dataset', layout=self.layout_button)
        self.button_return_data.on_click(self.return_data)
        self.button_return_figure = ipw.Button(description='',icon='mail-forward',disabled=False,tooltip='Copy code to clipboard to access current matplotlib.figure()',layout=self.layout_button)
        self.button_return_figure.on_click(self.return_figure)
        self.button_save_figure = ipw.Button(description='',icon='save',disabled=False,tooltip='Save figure',layout=self.layout_button)
        self.button_save_figure.on_click(self.save_figure)
        self.button_clipboard = ipw.Button(description='',icon='copy',disabled=False,tooltip='Copy figure to clipboard',layout=self.layout_button)
        self.button_clipboard.on_click(self.copy_to_clipboard)
        self.button_settings = ipw.Button(description='',icon='cog',disabled=False,tooltip='Settings',layout=self.layout_button)
        self.settings_visibility = False
        self.button_settings.on_click(self.settings_visibility_change)
        self.sxm_show = ipw.Button(description='',icon='photo',disabled=False,tooltip='Show .sxm file',layout=self.layout_button)
        self.sxm_show_value = False
        self.sxm_show.on_click(self.sxm_visibility_change)
        self.button_header_display = ipw.Button(description='',icon='info-circle',disabled=False,tooltip='Display header information',layout=self.layout_button)
        self.header_visibility = False
        self.button_header_display.on_click(self.header_visibility_change)
        self.save_fig_in_database_button = ipw.Button(description='',icon='database',disabled=False,tooltip='Save figure in database',layout=self.layout_button)
        self.save_fig_in_database_button.on_click(self.save_fig_in_database)

        # Settings Options
        self.layout_settings_visible = ipw.Layout(visibility='visible',width='150px',height='30px')
        self.layout_settings_hidden = ipw.Layout(visibility='hidden',width='0px',height='0px')
        self.dpi_slider = ipw.FloatText(value=300,step=1,description='dpi',disabled=False,layout=self.layout_settings_hidden)
        self.save_file_format = ipw.Dropdown(options=['png','svg'],value='png',description='Format',disabled=False,layout=self.layout_settings_hidden)
        self.overwrite = ipw.Dropdown(options=['False','True'],value='False',description='Overwrite File',disabled=False,layout=self.layout_settings_hidden)
        self.fig_size_x = ipw.FloatText(value=6,step=0.1,description='fig size x',disabled=False,layout=self.layout_settings_hidden)
        self.fig_size_y = ipw.FloatText(value=7,step=0.1,description='fig size y',disabled=False,layout=self.layout_settings_hidden)

        # Layout Return Options
        self.return_options_group = ipw.VBox([ipw.HBox([self.like_button_out,
                                                self.button_return_data,
                                                self.button_return_figure,
                                                self.button_save_figure,
                                                self.button_clipboard,
                                                self.button_settings,
                                                self.sxm_show,
                                                self.button_header_display,
                                                self.save_fig_in_database_button
                                                ]),
                                                ipw.VBox([self.dpi_slider,self.save_file_format,self.overwrite,self.fig_size_x,self.fig_size_y]),
                                                ipw.HBox([self.tag_widgets])    
                                    ])
        
        # Plot output
        self.out_com = ipw.Output()

        # Header Output
        self.header_layout_visible = ipw.Layout(visibility='visible',width='420px',height='400px')
        self.header_layout_hidden = ipw.Layout(visibility='hidden',width='1px',height='1px')
        self.out_header = ipw.Output(layout=self.header_layout_hidden)
        self.header_select = ipw.Dropdown(options=[],description='Header',disabled=False,layout=self.layout_hidden)
        # self.update_header_select()
        self.header_select.observe(self.update_header, names='value')
        self.header_widgets = ipw.VBox([self.header_select,self.out_header])


        # Update Properties
        self.update_plot(None)
        
        # Add event handlers
        event_handlers = [
            self.dat_select1,
            self.dat_select2,
            self.selector_xchannel1,
            self.selector_ychannel1,
            self.selector_ychannel2,
            self.direction1,
            self.direction2,
            self.display_legend,
            self.selector_calc_options1,
            self.selector_calc_options2,
            self.spline_smoothness1,
            self.spline_smoothness2,
            self.multi_y_plot,
            self.sxm_select,
            self.selector_sxm_channel,
            self.sxm_direction,
            self.sxm_flatten,
            self.sxm_offset,
            self.sxm_scale,
            self.sxm_show_params,
            self.positions,
            self.fig_size_x,
            self.fig_size_y
        ]

        for event_handler in event_handlers:
            event_handler.observe(self.update_plot, names='value')

        ### Create Layout
        self.dat_viewer_widgets = ipw.VBox([self.return_options_group,
                                            ipw.HBox([self.dat_viewer_options1,self.dat_viewer_options2,self.out_com,self.sxm_viewer_options,self.header_widgets])])

    ### Visibility Change Functions / Layout Control ###

    def sxm_visibility_change(self,change):
        """Changes visbiility of the .sxm file widgets"""
        print('dat_viewer.sxm_visibility_change(): called')
        if self.sxm_show_value == False:
            self.sxm_show_value = True
            self.sxm_show.tooltip = 'Hide .sxm file'
            self.sxm_select.layout = ipw.Layout(height='200px',width='200px')
            widgets_to_show = [
                self.selector_sxm_channel,
                self.sxm_direction,
                self.sxm_flatten,
                self.sxm_offset,
                self.sxm_scale,
                self.sxm_show_params,
                self.positions
            ]
            for widget in widgets_to_show:
                widget.layout = self.layout_visible
        else:
            widgets_to_hide = [
                self.sxm_select,
                self.selector_sxm_channel,
                self.sxm_direction,
                self.sxm_flatten,
                self.sxm_offset,
                self.sxm_scale,
                self.sxm_show_params,
                self.positions
            ]

            for widget in widgets_to_hide:
                widget.layout = self.layout_hidden

        self.update_plot(None)

    def multi_y_plot_visibility_change(self,change):
        """Changes visbiility of the second y axis widgets"""
        if self.multi_y_plot.value == 'Multi':
            self.dat_select2.layout = ipw.Layout(height='200px',width='200px')
            self.selector_ychannel2.layout = self.layout_visible
            self.direction2.layout = self.layout_visible
            self.selector_calc_options2.layout = self.layout_visible
        else:
            self.dat_select2.layout = self.layout_hidden
            self.selector_ychannel2.layout = self.layout_hidden
            self.direction2.layout = self.layout_hidden
            self.selector_calc_options2.layout = self.layout_hidden

    def spline_smoothness_vibility_change(self,dat_viewer_option_number:int,visibility:bool):
        """
        Changes the visibility of the spline smoothness widgets: self.spline_smoothness1 and self.spline_smoothness2
        Input:
            dat_viewer_option_number: int, 1 or 2
            visibility: bool, True or False
        """
        if dat_viewer_option_number == 1:
            if visibility == True:
                self.spline_smoothness1.layout = self.layout_visible
            else:
                self.spline_smoothness1.layout = self.layout_hidden
        if dat_viewer_option_number == 2:
            if visibility == True:
                self.spline_smoothness2.layout = self.layout_visible
            else:
                self.spline_smoothness2.layout = self.layout_hidden

    def modify_legend_sumbit_click(self,change):
        self.modify_legend_visibility_change(None)
        self.modify_legend_sumbit_value = True
        print('dat_viewer.modify_legend_sumbit_click(): not yet fully implemented')
        #self.update_plot(None)

    def modify_legend_visibility_change(self,change):
        if self.modify_legend_show == False:
            self.modify_legend_show = True
            self.modify_legend_textarea.layout = ipw.Layout(height='200px',width='200px',visibility='visible')
            self.modify_legend_sumbit.layout = ipw.Layout(width='40px',visibility='visible')
            self.update_plot(None)
        else:
            self.modify_legend_show = False
            self.modify_legend_textarea.layout = self.layout_hidden
            self.modify_legend_sumbit.layout = self.layout_hidden

    def settings_visibility_change(self, change):
        """
        Toggle the visibility of the settings options
        """
        if self.settings_visibility == False:
            self.settings_visibility = True
            self.dpi_slider.layout = self.layout_settings_visible
            self.save_file_format.layout = self.layout_settings_visible
            self.overwrite.layout = self.layout_settings_visible
            self.fig_size_x.layout = self.layout_settings_visible
            self.fig_size_y.layout = self.layout_settings_visible
        else:
            self.settings_visibility = False
            self.dpi_slider.layout = self.layout_settings_hidden
            self.save_file_format.layout = self.layout_settings_hidden
            self.overwrite.layout = self.layout_settings_hidden
            self.fig_size_x.layout = self.layout_settings_hidden
            self.fig_size_y.layout = self.layout_settings_hidden

    ### Call back functions ###

    def return_data(self, change):
        """
        Copy code to clipboard to access current spm(data) in the database
        """
        # Get data_ids from widgets
        self.data_ids = list(self.dat_select1.value)
        self.data_ids_2 = list(self.dat_select2.value)
        self.data_id_sxm = self.sxm_select.value

        # Collect all data_ids
        all_ids = []
        for id in self.data_ids+self.data_ids_2:
            all_ids.append(id)
        if self.sxm_show_value == True:
            all_ids.append(self.data_id_sxm)
        
        # Create output string
        if len(all_ids) == 1:
            s = 'data = app.db.db_get_data("'+str(all_ids[0])+'")'
        else:
            s = 'data = ['
            for id in all_ids:
                s = s + 'app.db.db_get_data("'+str(id)+'"),'
            s = s[:-1] + ']'

        # Copy to clipboard
        pyperclip.copy(s)

        print('dat_viewer.return_data(): database access code copied to clipboard')

    def return_figure(self, change):
        """
        Copy code to clipboard to access current matplotlib.figure()
        """
        # Get new name for link_property
        link_property_name = 'fig'

        # Check if link_property_name is already in use, then iterate with _1, _2, ...
        link_property_name = self.db.db_get_unused_link_property_name(link_property_name)

        # Save figure to database element
        self.db.db_write([],link_property_name,self.fig_combined,link_prop=True,write_display_property=True)

        # Create output string
        s = 'fig = app.db.db_get("link","'+str(link_property_name)+'",link_prop=True)'

        # Copy to clipboard
        pyperclip.copy(s)

        print('dat_viewer.return_figure(): figure save in database and access code copied to clipboard')
        
    def save_figure(self, change):
        """
        Saves the figure as selected file format
        """
        directory = os.getcwd()
        proposed_filebase = self.db.db_get(self.data_id,"filename_full").split('.')[0]
        file_ending = self.save_file_format.value
        if self.overwrite.value == 'True':
            new_filename = proposed_filebase+'.'+file_ending
        else:
            new_filename = self.db.fname_generator(directory,proposed_filebase,file_ending)
        self.fig_combined.savefig(new_filename,dpi=self.dpi_slider.value)
        print('figure saved as '+new_filename)

    def copy_to_clipboard(self, change):
        if self.save_file_format.value == 'png':
            copy_to_clipboard(self.fig_combined, self.save_file_format.value, self.dpi_slider.value)
            print('figure copied as .png to clipboard')
        
        if self.save_file_format.value == 'svg':
            print('copying .svg to clipboard is not yet implemented')
    
    def save_fig_in_database(self, change):
        print('dat_viewer.save_fig_in_database(): Not yet implemented... need save as stiched')

    ### Helper functions

    def external_open(self,data_id):
        print('dat_viewer.external_open(data_id) called')
        self.dat_select1.value = (data_id,)

        self.update_plot(None)

    ### Get and Write Display Properties ###
        
    def get_current_display_properties(self):
        
        """
        Gets current display properties from the database and updates/initializes the widgets.

        Accessed properties ~ display_property:
        self.dat_select1 ~ 'dat_viewer_value',super_prop=True
        self.selector_xchannel1 ~ 'current_xchannel'
        self.selector_ychannel1 ~ 'current_ychannel'
        self.direction1 ~ 'direction'
        self.selector_calc_options1 ~ 'calc_options'
        self.spline_smoothness1 ~ 'spline_smoothness'

        self.multi_y_plot ~ 'multi_y_plot_value',super_prop=True
        self.dat_select2 ~ 'dat_viewer_value2',super_prop=True
        self.selector_xchannel2 ~ 'current_xchannel'
        self.selector_ychannel2 ~ 'current_ychannel'
        self.direction2 ~ 'direction'
        self.selector_calc_options2 ~ 'calc_options'
        self.spline_smoothness2 ~ 'spline_smoothness'

        self.sxm_select ~ 'sxm_ref'
        self.selector_sxm_channel ~ 'current_channel'
        self.sxm_direction ~ 'direction'
        self.sxm_flatten ~ 'current_flatten'
        self.sxm_offset ~ 'current_offset'
        self.sxm_scale ~ 'current_scale'
        self.sxm_show_params ~ 'sxm_show_params'
        self.positions ~ 'current_show_positions'

        """

        # Updates the current display_properties of the current DAT file and the SXM image with the data_id in the widgets.
        
        # self.dat_select1.value
        if self.dat_select1.value == ():
            dat_viewer_value = self.db.db_get([],'dat_viewer_value',super_prop=True)
            if dat_viewer_value == None:
                self.data_ids = [self.all_data_ids_dat[0]]
            else:
                self.data_ids = dat_viewer_value
            self.dat_select1.value = tuple(self.data_ids)
        else:
            self.data_ids = list(self.dat_select1.value)
        
        # self.selector_xchannel1.options
        selector_xchannel1_value = self.selector_xchannel1.value
        all_xchannels1 = []
        for data_id in self.data_ids:
            for channel_name in self.db.db_get(data_id,'channel_names'):
                if channel_name not in all_xchannels1:
                    all_xchannels1.append(channel_name)
        self.selector_xchannel1.options = all_xchannels1

        # self.selector_xchannel1.value
        if selector_xchannel1_value in self.selector_xchannel1.options:
            self.selector_xchannel1.value = selector_xchannel1_value
        else:
            current_xchannel1 = self.db.db_get(self.data_ids[0],'current_xchannel')
            if current_xchannel1 == None:
                self.selector_xchannel1.value = self.db.db_get(self.data_ids[0],'fxchannel')
            else:
                self.selector_xchannel1.value = current_xchannel1

        # self.selector_ychannel1.options
        selector_ychannel1_value = self.selector_ychannel1.value
        all_ychannels1 = []
        for data_id in self.data_ids:
            for channel_name in self.db.db_get(data_id,'channel_names'):
                if channel_name not in all_ychannels1:
                    all_ychannels1.append(channel_name)
        self.selector_ychannel1.options = all_ychannels1
        
        # self.selector_ychannel1.value
        if selector_ychannel1_value in self.selector_ychannel1.options:
            self.selector_ychannel1.value = selector_ychannel1_value
        else:
            current_ychannel1 = self.db.db_get(self.data_ids[0],'current_ychannel')
            if current_ychannel1 == None:
                self.selector_ychannel1.value = self.db.db_get(self.data_ids[0],'fychannel')
            else:
                self.selector_ychannel1.value = current_ychannel1

        # self.direction1.value
        if self.direction1.value == []:
            direction1 = self.db.db_get(self.data_ids[0],'direction')
            if direction1 == None:
                direction1 = 'Forward'
            self.direction1.value = direction1
                
        # self.selector_calc_options1.value # calc_options = ['Y(X)','Y(X) _ spline','dY/dX _ spline','dY/dX _ grad']
        if self.selector_calc_options1.value == []:
            calc_options1 = self.db.db_get(self.data_ids[0],'calc_options')
            if calc_options1 == None:
                calc_options1 = 'Y(X)'
            self.selector_calc_options1.value = calc_options1
  
        # self.spline_smoothness1.value
        if self.spline_smoothness1.value == []:
            spline_smoothness1 = self.db.db_get(self.data_ids[0],'spline_smoothness')
            if spline_smoothness1 == None:
                spline_smoothness1 = 9e-10
            self.spline_smoothness1.value = spline_smoothness1
        
        # self.multi_y_plot.value
        multi_y_plot_value = self.db.db_get([],'multi_y_plot_value',super_prop=True)
        if multi_y_plot_value == None:
            multi_y_plot_value = 'Single'
        if multi_y_plot_value == 'Multi':
            self.multi_y_plot.value = multi_y_plot_value
        
        if self.multi_y_plot.value == 'Multi':
            # self.dat_select2.value
            if self.dat_select2.value == ():
                dat_viewer_value2 = self.db.db_get([],'dat_viewer_value2',super_prop=True)
                if dat_viewer_value2 == None:
                    self.data_ids_2 = [self.all_data_ids_dat[0]]
                else:
                    self.data_ids_2 = dat_viewer_value2
                self.dat_select2.value = tuple(self.data_ids_2)
            else:
                self.data_ids_2 = list(self.dat_select2.value)

            # self.selector_ychannel2.options
            selector_ychannel2_value = self.selector_ychannel2.value
            all_ychannels2 = []
            for data_id in self.data_ids_2:
                for channel_name in self.db.db_get(data_id,'channel_names'):
                    if channel_name not in all_ychannels2:
                        all_ychannels2.append(channel_name)
            self.selector_ychannel2.options = all_ychannels2
        
            # self.selector_ychannel2.value
            if selector_ychannel2_value in self.selector_ychannel2.options:
                self.selector_ychannel2.value = selector_ychannel2_value
            else:
                current_ychannel2 = self.db.db_get(self.data_ids_2[0],'current_ychannel')
                if current_ychannel2 == None:
                    self.selector_ychannel2.value = self.db.db_get(self.data_ids_2[0],'fychannel')
                else:
                    self.selector_ychannel2.value = current_ychannel2
            
            # self.direction2.value
            if self.direction2.value == []:
                direction2 = self.db.db_get(self.data_ids_2[0],'direction')
                if direction2 == None:
                    direction2 = 'Forward'
                self.direction2.value = direction2
                    
            # self.selector_calc_options2.value # calc_options = ['Y(X)','Y(X) _ spline','dY/dX _ spline','dY/dX _ grad']
            if self.selector_calc_options2.value == []:
                calc_options2 = self.db.db_get(self.data_ids_2[0],'calc_options')
                if calc_options2 == None:
                    calc_options2 = 'Y(X)'
                self.selector_calc_options2.value = calc_options2
  
            # self.spline_smoothness2.value
            if self.spline_smoothness2.value == []:
                spline_smoothness2 = self.db.db_get(self.data_ids_2[0],'spline_smoothness')
                if spline_smoothness2 == None:
                    spline_smoothness2 = 9e-10
                self.spline_smoothness2.value = spline_smoothness2
                
        # self.selector_sxm
        if self.sxm_show_value == True:
            
            if self.sxm_select.value == '':
                sxm_ref_value = self.db.db_get(self.data_ids[0],'sxm_ref')
                if sxm_ref_value == None:
                    self.data_id_sxm = self.all_data_ids_sxm[0]
                else:
                    self.data_id_sxm = sxm_ref_value
                self.sxm_select.value = self.data_id_sxm
            else:
                self.data_id_sxm = self.sxm_select.value

            # self.selector_sxm_channel.options
            sxm_channel_value = self.selector_sxm_channel.value
            self.selector_sxm_channel.options = self.db.db_get(self.data_id_sxm,'channel_names')

            # self.selector_sxm_channel.value

            if sxm_channel_value is not None and sxm_channel_value in self.selector_sxm_channel.options:
                self.selector_sxm_channel.value = sxm_channel_value
            else:
                current_channel = self.db.db_get(self.data_id_sxm, 'current_channel') or self.db.db_get(self.data_id_sxm, 'fchannel')
                self.selector_sxm_channel.value = current_channel

            # self.sxm_direction.value
            if self.sxm_direction.value == []:
                sxm_direction = self.db.db_get(self.data_id_sxm,'direction')
                if sxm_direction == None:
                    sxm_direction = 'Forward'
                self.sxm_direction.value = sxm_direction

            # self.sxm_flatten.value
            if self.sxm_flatten.value == []:
                sxm_flatten = self.db.db_get(self.data_id_sxm,'flatten')
                if sxm_flatten == None:
                    sxm_flatten = 'False'
                self.sxm_flatten.value = sxm_flatten

            # self.sxm_offset.value
            if self.sxm_offset.value == []:
                sxm_offset = self.db.db_get(self.data_id_sxm,'current_offset')
                if sxm_offset == None:
                    sxm_offset = 0.0
                self.sxm_offset.value = sxm_offset

            # self.sxm_scale.value
            if self.sxm_scale.value == []:
                sxm_scale = self.db.db_get(self.data_id_sxm,'current_scale')
                if sxm_scale == None:
                    sxm_scale = 'Linear'
                self.sxm_scale.value = sxm_scale

            # self.sxm_show_params.value
            if self.sxm_show_params.value == []:
                sxm_show_params = self.db.db_get(self.data_id_sxm,'current_show_params')
                if sxm_show_params == None:
                    sxm_show_params = 'Dont show'
                self.sxm_show_params.value = sxm_show_params
            
            # self.sxm_show_positions.value
            if self.positions.value == []:
                show_positions_value = self.db.db_get(self.data_ids[0],'current_show_positions')
                if show_positions_value == None:
                    show_positions_value = 'Dont show'
                self.positions.value = show_positions_value
    
    def write_current_display_properties(self):
        """
        Write the current display properties to the database.

        Accessed properties ~ display_property:
        self.dat_select1 ~ 'dat_viewer_value',super_prop=True
        self.selector_xchannel1 ~ 'current_xchannel'
        self.selector_ychannel1 ~ 'current_ychannel'
        self.direction1 ~ 'direction'
        self.selector_calc_options1 ~ 'calc_options'
        self.spline_smoothness1 ~ 'spline_smoothness'

        self.multi_y_plot ~ 'multi_y_plot_value',super_prop=True
        self.dat_select2 ~ 'dat_viewer_value2',super_prop=True
        self.selector_xchannel2 ~ 'current_xchannel'
        self.selector_ychannel2 ~ 'current_ychannel'
        self.direction2 ~ 'direction'
        self.selector_calc_options2 ~ 'calc_options'
        self.spline_smoothness2 ~ 'spline_smoothness'

        self.sxm_select ~ 'sxm_ref'
        self.selector_sxm_channel ~ 'current_channel'
        self.sxm_direction ~ 'direction'
        self.sxm_flatten ~ 'current_flatten'
        self.sxm_offset ~ 'current_offset'
        self.sxm_scale ~ 'current_scale'
        self.sxm_show_params ~ 'sxm_show_params'
        self.positions ~ 'current_show_positions'

        """
        if self.dat_select1.value != ():
            self.data_ids = list(self.dat_select1.value)
            self.db.db_write([],'dat_viewer_value',self.data_ids,super_prop=True)
            for data_id in self.data_ids:
                self.db.db_write(data_id,'current_xchannel',self.selector_xchannel1.value)
                self.db.db_write(data_id,'current_ychannel',self.selector_ychannel1.value)
                self.db.db_write(data_id,'direction',self.direction1.value)
                self.db.db_write(data_id,'calc_options',self.selector_calc_options1.value)
                self.db.db_write(data_id,'spline_smoothness',self.spline_smoothness1.value)
                self.db.db_write(data_id,'current_show_positions',self.positions.value)
                if self.sxm_show_value == True:
                    self.db.db_write(data_id,'sxm_ref',self.sxm_select.value)
        
        if self.dat_select2.value != ():
            self.data_ids_2 = list(self.dat_select2.value)
            self.db.db_write([],'dat_viewer_value_2',self.data_ids_2,super_prop=True)
            for data_id in self.data_ids_2:
                if data_id not in self.data_ids:
                    self.db.db_write(data_id,'current_xchannel',self.selector_xchannel1.value)
                    self.db.db_write(data_id,'current_ychannel',self.selector_ychannel2.value)
                    self.db.db_write(data_id,'direction',self.direction2.value)
                    self.db.db_write(data_id,'calc_options',self.selector_calc_options2.value)
                    self.db.db_write(data_id,'spline_smoothness',self.spline_smoothness2.value)
                    self.db.db_write(data_id,'current_show_positions',self.positions.value)
        
        if self.sxm_show_value == True:
            if self.sxm_select.value != []:
                self.data_id_sxm = self.sxm_select.value
                self.db.db_write(self.data_id_sxm,'current_channel',self.selector_sxm_channel.value)
                self.db.db_write(self.data_id_sxm,'current_direction',self.sxm_direction.value)
                self.db.db_write(self.data_id_sxm,'current_flatten',self.sxm_flatten.value)
                self.db.db_write(self.data_id_sxm,'current_offset',self.sxm_offset.value)
                self.db.db_write(self.data_id_sxm,'current_scale',self.sxm_scale.value)
                self.db.db_write(self.data_id_sxm,'current_show_params',self.sxm_show_params.value)

    ### Update Functions ###

    def update_tagging(self):
        """ Replaces the tagging widget with a new one corresponding to the current active data_ids"""
        all_active_data_ids = list(self.dat_select1.value) + list(self.dat_select2.value)
        self.tag_widgets = tagging(all_active_data_ids,self.db).tag_widgets

    def update_like(self):
        """Updates the likebutton with the current active data_ids"""
        all_active_data_ids = list(self.dat_select1.value) + list(self.dat_select2.value) + [self.sxm_select.value]
        self.likebutton.update_data_id(all_active_data_ids)

    ### Plotting Functions ###

    def update_plot(self,change):
        """
        Starts plotting function
        """
        self.get_current_display_properties()
        self.plot_combined()
        self.write_current_display_properties()
        self.update_tagging()
        self.update_like()
        self.update_header_select()

    def calc_options(self,calc_options_value:str,dat_x,dat_y,spline_smoothness_value):
        """
        Calculates the data based on the calc_options1_value
        calc_options = ['Y(X)','Y(X) _ spline','dY/dX _ spline','dY/dX _ grad']

        Input:
            calc_options_value: str, selected value from calc_options
            dat_x: np.array, x data
            dat_y: np.array, y data
            spline_smoothness_value: float, smoothness of spline

        Output:
            dat_x: np.array, x data
            dat_y: np.array, y data
            y_label_add = str, additional label for y axis
        """

        if calc_options_value == 'Y(X)':
            dat_x = dat_x
            dat_y = dat_y
            y_label_add = ''
        
        if calc_options_value == 'Y(X) _ spline':
            if dat_x[0] > dat_x[-1]:
                flipped = True
                dat_x = np.flip(dat_x)
                dat_y = np.flip(dat_y)
            else:
                flipped = False
            s = UnivariateSpline(dat_x, dat_y,s=spline_smoothness_value,k=5)
            xs = np.linspace(dat_x[0],dat_x[-1], len(dat_x))
            dat_x = xs
            dat_y = s(xs)
            if flipped == True:
                dat_x = np.flip(dat_x)
                dat_y = np.flip(dat_y)
            y_label_add = 'spline(Y(X))'

        
        if calc_options_value == 'dY/dX _ spline':
            if dat_x[0] > dat_x[-1]:
                flipped = True
                dat_x = np.flip(dat_x)
                dat_y = np.flip(dat_y)
            else:
                flipped = False
            spl = UnivariateSpline(dat_x, dat_y,s=spline_smoothness_value,k=5)
            xs = np.linspace(dat_x[0],dat_x[-1], len(dat_x))
            y_grad = np.gradient(spl(xs),xs)
            dat_x = xs
            dat_y = y_grad
            if flipped == True:
                dat_x = np.flip(dat_x)
                dat_y = np.flip(dat_y)
            y_label_add = 'dspline(Y(X))/dX'
        
        if calc_options_value == 'dY/dX _ grad':
            dat_x = dat_x
            dat_y = np.gradient(dat_y,dat_x)
            y_label_add = 'dY(X)/dX'

        return dat_x,dat_y,y_label_add

    def plot_combined(self):

        """Plot the selected data using the chosen settings."""

        

        # Set up the plot figure and axes
        if self.sxm_show_value == True:
            fig_size_x = self.fig_size_x.value*2 # default: fig_size_x = 12
            fig_size_y = self.fig_size_y.value # default: fig_size_y = 7
            self.fig_combined, (self.ax_dat, self.ax_sxm) = plt.subplots(1, 2,figsize=(fig_size_x,fig_size_y))
        else:
            fig_size_x = self.fig_size_x.value # default: fig_size_x = 6
            fig_size_y = self.fig_size_y.value # default: fig_size_y = 7
            self.fig_combined, self.ax_dat = plt.subplots(1,1,figsize=(fig_size_x,fig_size_y))
        self.out_com.clear_output(wait=True)
        
        # Get the data ids and parameters from the GUI elements
        self.data_ids = list(self.dat_select1.value)
        self.data_ids_2 = list(self.dat_select2.value)
        self.data_id_sxm = self.sxm_select.value

        selector_xchannel1_value = self.selector_xchannel1.value
        selector_ychannel1_value = self.selector_ychannel1.value 
        direction1_value = self.direction1.value
        calc_options1_value = self.selector_calc_options1.value
        spline_smoothness1_value = self.spline_smoothness1.value

        selector_ychannel2_value = self.selector_ychannel2.value
        direction2_value = self.direction2.value
        calc_options2_value = self.selector_calc_options2.value
        spline_smoothness2_value = self.spline_smoothness2.value
       
        # Colors
        self.colormap = pl.cm.rainbow(np.linspace(0,1,len(self.data_ids)+len(self.data_ids_2)))
        colormap_counter = 0
        all_plotted_dat_data_ids = []
        all_plotted_dat_data_ids_colors = []
        all_plotted_dat_data_ids_labels = []
        all_plotted_dat_handles_labels = []

        if self.data_ids:
            for data_id in self.data_ids:
                if selector_xchannel1_value in self.db.db_get(data_id,'channel_names'):
                    if selector_ychannel1_value in self.db.db_get(data_id,'channel_names'):
                        # Get data
                        (dat_x,x_unit) = self.db.db_get_data(data_id).get_channel(selector_xchannel1_value,direction1_value)
                        (dat_y,y_unit) = self.db.db_get_data(data_id).get_channel(selector_ychannel1_value,direction1_value)
                        
                        # Calculatation options for dat_x and dat_y
                        if calc_options1_value in ("Y(X) _ spline", "dY/dX _ spline"):
                            self.spline_smoothness_vibility_change(1,True)
                        else:
                            self.spline_smoothness_vibility_change(1,False)
                        dat_x,dat_y,y_label_add = self.calc_options(calc_options1_value,dat_x,dat_y,spline_smoothness1_value)

                        line1, = self.ax_dat.plot(
                            dat_x,
                            dat_y,
                            color=self.colormap[colormap_counter],
                            label=data_id)
                        all_plotted_dat_handles_labels.append((line1,data_id))
                        
                        all_plotted_dat_data_ids.append(data_id)
                        all_plotted_dat_data_ids_colors.append(self.colormap[colormap_counter])
                        all_plotted_dat_data_ids_labels.append(data_id)

                        colormap_counter += 1
                        
                    else:
                        print('Y channel ',selector_ychannel1_value,' in ',data_id, ' not found')
                else:
                    print('X channel ',selector_xchannel1_value,' in ',data_id, ' not found')
            # self.ax_dat.set(xlabel=self.selector_xchannel.value, ylabel=self.selector_ychannel.value + ylabel_add)
        
        # multi_y_plot: Add second y axis
        self.multi_y_plot_was_active = False
        if self.multi_y_plot.value == 'Multi':
            self.ax_dat2 = self.ax_dat.twinx()
            self.multi_y_plot_was_active = True
            if self.data_ids_2 != []:
                for data_id in self.data_ids_2:
                    if selector_xchannel1_value in self.db.db_get(data_id,'channel_names'):
                        if selector_ychannel2_value in self.db.db_get(data_id,'channel_names'):
                            # Get data
                            (dat_x,x_unit) = self.db.db_get_data(data_id).get_channel(selector_xchannel1_value,direction2_value)
                            (dat_y,y_unit) = self.db.db_get_data(data_id).get_channel(selector_ychannel2_value,direction2_value)
                            
                            # Calculatation options for dat_x and dat_y
                            if calc_options2_value == 'Y(X) _ spline' or calc_options2_value == 'dY/dX _ spline':
                                self.spline_smoothness_vibility_change(2,True)
                            else:
                                self.spline_smoothness_vibility_change(2,False)
                            dat_x,dat_y,y_label_add = self.calc_options(self.selector_calc_options2.value,dat_x,dat_y,spline_smoothness2_value)

                            line2, = self.ax_dat2.plot(
                                dat_x,
                                dat_y,
                                color=self.colormap[colormap_counter],
                                label=data_id+'_y2')
                            
                            all_plotted_dat_data_ids.append(data_id)
                            all_plotted_dat_data_ids_colors.append(self.colormap[colormap_counter])
                            all_plotted_dat_data_ids_labels.append(data_id)
                            all_plotted_dat_handles_labels.append((line2,data_id+'_y2'))

                            colormap_counter += 1

                        else:
                            print('Y channel ',self.selector_ychannel2.value,' in ',data_id, ' not found')
                    else:
                        print('X channel ',self.selector_xchannel1.value,' in ',data_id, ' not found')

        # Switch back to single y axis
        if self.multi_y_plot.value == 'Single':
            if self.multi_y_plot_was_active == True:
                self.ax_dat2.remove()
                self.spline_smoothness_vibility_change(2,False)


        # Plot STM 

        if self.sxm_show_value == True and self.data_id_sxm != '':

            # Get the parameters
            sxm_channel = self.selector_sxm_channel.value
            sxm_direction = self.sxm_direction.value
            sxm_flatten = self.sxm_flatten.value
            sxm_offset = self.sxm_offset.value
            sxm_scale = self.sxm_scale.value
            sxm_show_params = self.sxm_show_params.value
            sxm_show_positions = self.positions.value


            # Get the data
            sxm = self.db.db_data[self.data_id_sxm]
            (chData,chUnit) = sxm.get_channel(sxm_channel,direction=sxm_direction,flatten=sxm_flatten,offset=sxm_offset)

            # Plot Parameters
            width = sxm.get_param('width')
            height = sxm.get_param('height')
            ImgOrigin = 'lower'
            if sxm.get_param('scan_dir') == 'down':
                ImgOrigin = 'upper'
            cmap = 'gray'

            # Plotting
            if sxm_scale == 'Log':
                im = self.ax_sxm.imshow(np.abs(chData), aspect = 'equal', extent = [0,width[0],0,height[0]], cmap = cmap, norm=LogNorm(), origin = ImgOrigin)
            else:
                im = self.ax_sxm.imshow(chData, aspect = 'equal',extent = [0,width[0],0,height[0]], cmap = cmap, origin = ImgOrigin)

            # TODO: if clim: plt.clim(clim)
    
            im.axes.set_xticks([0,width[0]])
            im.axes.set_xticklabels([0,np.round(width[0],2)])
            im.axes.set_yticks([0,height[0]])
            im.axes.set_yticklabels([0,np.round(height[0],2)])

            plt.xlabel('x (%s)' % width[1])
            plt.ylabel('y (%s)' % height[1])

            cbar = plt.colorbar(im,fraction=0.046, pad=0.02, format='%.2g',shrink = 0.5,aspect=10)
            cbar.set_label('%s (%s)' % (sxm_channel,chUnit))
        
            if sxm_show_params == 'Show':
                title = sxm.print_params(show = False)
                self.ax_sxm.set_title(title + '\n', loc='left', fontsize=8)
                #plt.title(title + '\n', loc='left', fontsize=8)

            if self.positions.value == 'Show':
                print('ERROR when trying to display multiple positions')
                for (s,c) in zip(all_plotted_dat_data_ids,all_plotted_dat_data_ids_colors):
                    # print('all_plotted_dat_data_ids',all_plotted_dat_data_ids)
                    # print('type(all_plotted_dat_data_ids)',type(all_plotted_dat_data_ids))
                    # print('all_plotted_dat_data_ids_colors',all_plotted_dat_data_ids_colors)
                    # print('type(all_plotted_dat_data_ids_colors)',type(all_plotted_dat_data_ids_colors))
                    (x,y) = spmpy.relative_position(sxm,self.db.db_data[s])
                    self.ax_sxm.plot(x,y,'o',color = c)

        if self.display_legend.value == 'Show':
            handles = []
            labels = []
            for handle_label in all_plotted_dat_handles_labels:
                handles.append(handle_label[0])
                labels.append(handle_label[1])
            self.ax_dat.legend([handles,labels])

        if self.display_legend.value == 'Show':
            handles1, labels1 = self.ax_dat.get_legend_handles_labels()
            if self.multi_y_plot.value == 'Multi':
                handles2, labels2 = self.ax_dat2.get_legend_handles_labels()
                handles = handles1 + handles2
                labels = labels1 + labels2
            else:
                handles = handles1
                labels = labels1
            self.legend = self.ax_dat.legend(handles, labels)

            self.legend_str = ""
            self.legend_pairs = []
            for handle, label in zip(handles, labels):
                self.legend_str += f"{label}: {handle.get_label()}\n"
                self.legend_pairs.append((label, handle))
            # print('self.legend_str created')
            

        if self.modify_legend_sumbit_value == True:
            print('self.modify_legend_sumbit_value',self.modify_legend_sumbit_value)
            
            self.modify_legend_sumbit_value = False

        if self.modify_legend_show == True and self.modify_legend_sumbit_value == False:
            self.modify_legend_textarea.value = self.legend_str
        
        if self.modify_legend_sumbit_value == False:
            self.modify_legend_textarea.value = self.legend_str

        #self.out_com.clear_output()
        with self.out_com:
            plt.show()

    ### Generate header output ###

    def header_visibility_change(self, change):
        """Toggle the visibility of the header output"""
        if self.header_visibility == False:
            self.header_visibility = True
            self.header_select.layout = self.layout_visible
            self.out_header.layout = self.header_layout_visible
        else:
            self.header_visibility = False
            self.header_select.layout = self.layout_hidden
            self.out_header.layout = self.header_layout_hidden

    def update_header_select(self):
        """Updates the selected data_id in the header dropdown widget"""
        
        if self.sxm_show_value == True:
            all_active_data_ids = list(self.dat_select1.value) + list(self.dat_select2.value) + [self.sxm_select.value]
        else:
            all_active_data_ids = list(self.dat_select1.value) + list(self.dat_select2.value)
        self.header_select.options = all_active_data_ids
        self.header_select.value = all_active_data_ids[0]

    def update_header(self,change):
        """Updates the header output"""
        self.generate_header()

    def generate_header(self):
        """Generates the header output for the current data_id and dispalys it as HTML table in self.outheader"""

        # Get the data_id
        selected_data_id = self.header_select.value

        # Get the data
        data = self.db.db_get_data(selected_data_id)

        # Get the header
        data_header = data.header

        # Generate the table
        table_html = '<div style="max-width: 400px; max-height: 400px; overflow: auto;">'
        table_html += f'<h2 style="font-size: 12px;">Header Information</h2>'
        table_html += f"<table style='font-size: 10px; line-height: 8px;'>"
        for key, value in data_header.items():
            table_html += f"<tr><td><b>{key}</b></td><td>{value}</td></tr>"
        table_html += "</table>"
        table_html += '</div>'

        # Display the table
        with self.out_header:
            clear_output(wait=True)
            display(ipw.HTML(table_html))
    
