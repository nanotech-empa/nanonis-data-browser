"""
Author:         Lysander Huberich
Description:    Viewer for .sxm files
"""

### Imports ###

import ipywidgets as ipw
import os
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pyperclip
from IPython.display import display, clear_output

import importlib
import tagging
importlib.reload(tagging)
tagging = tagging.tagging
import likebutton
importlib.reload(likebutton)
likebutton = likebutton.likebutton
import helpers
importlib.reload(helpers)
fname_generator = helpers.fname_generator
copy_to_clipboard = helpers.copy_to_clipboard




### sxm_viewer class ###

class sxm_viewer():

    """
    Output:
        self.sxm_viewer_widgets

    sxm_viewer:
        TODO: Adjustable color bar
        TODO: Plane correction Y/N.
        TODO: Display possible positions on sxm image.
        TODO: update sxm_select_channel and sxm_select, when plot_sxm is called
    """

    def __init__(self,db):

        self.db = db

        # Is there data to display?
        if len(list(self.db.db_prop['data_prop'].keys())) == 0:
            self.sxm_viewer_widgets = ipw.VBox([ipw.HTML(value="sxm_viewer.__init__: db.db_data['data_prop'] is empty. No database initalized?")])
            return
        
        # Is there any sxm file in the database?
        self.data_ids_sxm, file_type_found = self.db.file_type_finder('sxm')
        if not file_type_found:
            self.sxm_viewer_widgets = ipw.VBox([ipw.HTML(value="sxm_viewer.__init__: No .sxm file found in database.")])
            return
        
        # Check if there is a sxm_viewer_value in the database otherwise set it to the first sxm file
        sxm_viewer_value = self.db.db_get([],'sxm_viewer_value',super_prop=True)
        if sxm_viewer_value == None:
            self.data_id = self.data_ids_sxm[0]
            print('sxm_viewer.__init__: No sxm_viewer_value found in database. Setting it to the first .sxm file in the database.')
        else:  
            self.data_id = sxm_viewer_value
        

        # Create Widgets
        self.create_widgets()

    def create_widgets(self):

        ### Viewer Options

        self.layout1 = ipw.Layout(width='200px')
        
        self.sxm_select_html = ipw.HTML(value="Viewer Options")
        self.sxm_select = ipw.Select(options=self.data_ids_sxm,value=self.data_id,description='Select .sxm',disabled=False,layout=ipw.Layout(height='200px',width='200px'))
        self.selector_sxm_channel = ipw.Dropdown(options=[],description='channel',disabled=False,layout=self.layout1)
        self.sxm_direction = ipw.Dropdown(options=['forward','backwards'],value='forward',description='Direction',disabled=False,layout=self.layout1)
        self.sxm_flatten = ipw.Dropdown(options=['False','True'],value='False',description='Flatten',disabled=False,layout=self.layout1)
        self.sxm_offset = ipw.FloatText(value=0.0,description='Offset',disabled=False,layout=self.layout1)
        self.sxm_scale = ipw.Dropdown(options=['Linear','Log'],value='Linear',description='Scale',disabled=False,layout=self.layout1)
        self.sxm_show_params = ipw.Dropdown(options=['Show','Dont show'],value='Dont show',description='Show Params',disabled=False,layout=self.layout1)

        self.get_current_display_properties()

        observed_widgets = [
            self.sxm_select,
            self.selector_sxm_channel,
            self.sxm_direction,
            self.sxm_scale,
            self.sxm_flatten,
            self.sxm_offset,
            self.sxm_show_params
        ]
        for widget in observed_widgets:
            widget.observe(self.on_submit, names='value')

        self.sxm_options = ipw.VBox(observed_widgets)

        ### Return Options
        self.layout_button = ipw.Layout(width='40px')

        # Like Button
        self.likebutton = likebutton(self.data_id,self.db)
        self.like_button_out = self.likebutton.output
        
        self.tagging = tagging(self.data_id,self.db)
        self.tag_widgets = self.tagging.output

        self.button_return_data = ipw.Button(description='',icon='angle-double-right',disabled=False,tooltip='Return loaded spm(data) in globals as sxm_loaded', layout=self.layout_button)
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
        self.button_header_display = ipw.Button(description='',icon='info-circle',disabled=False,tooltip='Display header information',layout=self.layout_button)
        self.header_visibility = False
        self.button_header_display.on_click(self.header_visibility_change)

        # Settings Options
        self.layout_settings_visible = ipw.Layout(visibility='visible',width='150px',height='30px')
        self.layout_settings_hidden = ipw.Layout(visibility='hidden',width='1px',height='1px')
        self.dpi_slider = ipw.FloatText(value=300,step=1,description='dpi',disabled=False,layout=self.layout_settings_hidden)
        self.save_file_format = ipw.Dropdown(options=['png','svg'],value='png',description='Format',disabled=False,layout=self.layout_settings_hidden)
        self.overwrite = ipw.Dropdown(options=['False','True'],value='False',description='Overwrite File',disabled=False,layout=self.layout_settings_hidden)
        self.fig_size_x = ipw.FloatText(value=7,step=0.1,description='fig size x',disabled=False,layout=self.layout_settings_hidden)
        self.fig_size_y = ipw.FloatText(value=7,step=0.1,description='fig size y',disabled=False,layout=self.layout_settings_hidden)
        for widget in [self.fig_size_x,self.fig_size_y]:
            widget.observe(self.on_submit, names='value')

        # Layout Return Options
        self.return_options_group = ipw.VBox([ipw.HBox([self.like_button_out,
                                                        self.button_return_data,
                                                        self.button_return_figure,
                                                        self.button_save_figure,
                                                        self.button_clipboard,
                                                        self.button_settings,
                                                        self.button_header_display
                                                        ]),
                                                        ipw.VBox([self.dpi_slider,self.save_file_format,self.overwrite,self.fig_size_x,self.fig_size_y]),
                                                        ipw.HBox([self.tag_widgets])    
                                         ])

        # Plot Output
        self.outsxm = ipw.Output()

        # Header Output
        self.header_layout_visible = ipw.Layout(visibility='visible',width='420px',height='400px')
        self.header_layout_hidden = ipw.Layout(visibility='hidden',width='1px',height='1px')
        self.outheader = ipw.Output(layout=self.header_layout_hidden)
        self.on_submit(None)

        # Create the layout:
        self.sxm_viewer_widgets = ipw.VBox([self.return_options_group,ipw.HBox([self.sxm_options,self.outsxm,self.outheader])])
        
    ### Plotting functions

    def on_submit(self, change):
        # Write display properties to database

        # Call plot function
        if self.sxm_select.value == ():
            None
        else:
            self.write_current_display_properties()
            self.update_tagging()
            self.update_like()
            data_id = self.sxm_select.value
            sxm_channel = self.selector_sxm_channel.value
            direction = self.sxm_direction.value
            flatten=self.sxm_flatten.value
            offset=self.sxm_offset.value
            outsxm = self.outsxm
            scale = self.sxm_scale.value
            sxm_show_params = self.sxm_show_params.value
            self.fig_sxm = self.plot_sxm_viewer(data_id,sxm_channel,direction,flatten,offset,outsxm,scale,sxm_show_params)
            self.generate_header()

    def plot_sxm_viewer(self,data_id,sxm_channel,direction,flatten,offset,outsxm,scale,sxm_show_params):


        # Get the data
        sxm = self.db.db_data[data_id]


        (chData,chUnit) = sxm.get_channel(sxm_channel,direction=direction,flatten=flatten,offset=offset)

        # Plot Parameters
        width = sxm.get_param('width')
        height = sxm.get_param('height')
        ImgOrigin = 'lower'
        if sxm.get_param('scan_dir') == 'down':
            ImgOrigin = 'upper'
        cmap = 'gray'

        # Plot
        outsxm.clear_output(wait=True)
        fig_sxm, ax_sxm= plt.subplots(1,1,figsize=(7,7))

        # Plotting
        if scale == 'Log':
            im = ax_sxm.imshow(np.abs(chData), aspect = 'equal', extent = [0,width[0],0,height[0]], cmap = cmap, norm=LogNorm(), origin = ImgOrigin)
        else:
            im = ax_sxm.imshow(chData, aspect = 'equal',extent = [0,width[0],0,height[0]], cmap = cmap, origin = ImgOrigin)

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
            plt.title(title + '\n', loc='left', fontsize=8)


        outsxm.clear_output(wait=True)
        with outsxm:
            plt.show()
        
        return fig_sxm



    ### Callback functions

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

    def return_data(self, change):
        """
        Copy code to clipboard to access current spm(data) in the database
        """
        # Get data_if from widgets
        self.data_id = self.sxm_select.value

        # Create output string
        s = 'data = app.db.db_get_data("'+str(self.data_id)+'")'

        # Copy to clipboard
        pyperclip.copy(s)

        # Print to console
        print('sxm_viewer.return_data: database access code copied to clipboard')

    def return_figure(self, change):
        """
        Copy code to clipboard to access current matplotlib.figure()
        """

        # Get new name for link_property
        link_property_name = 'fig'

        # Check if link_property_name is already in use, then iterate with _1, _2, ...
        link_property_name = self.db.check_link_property_name(link_property_name)

                # Save figure to database element
        self.db.db_write([],link_property_name,self.fig_combined,link_prop=True,write_display_property=True)

        # Create output string
        s = 'fig = app.db.db_get("link","'+str(link_property_name)+'",link_prop=True)'

        # Copy to clipboard
        pyperclip.copy(s)

        print('sxm_viewer.return_figure(): figure saved in database and access code copied to clipboard')

    def save_figure(self, change):
        """
        Saves the figure as selected file format
        """
        proposed_filebase = self.db.db_get(self.data_id,"filename_full").split('.')[0]
        file_ending = self.save_file_format.value
        if self.overwrite.value == 'True':
            new_filename = proposed_filebase+'.'+file_ending
        else:
            new_filename = fname_generator(self.db.directory,proposed_filebase,file_ending)
        self.fig_sxm.savefig(new_filename,dpi=self.dpi_slider.value)
        print('figure saved as '+new_filename)

    def copy_to_clipboard(self, change):
        if self.save_file_format.value == 'png':
            copy_to_clipboard(self.fig_sxm, self.save_file_format.value, self.dpi_slider.value)
            print('figure copied as .png to clipboard')
        if self.save_file_format.value == 'svg':
            print('copying .svg to clipboard is not yet implemented')

    ### Update Functions ###

    def update_tagging(self):
        """ Replaces the tagging widget with a new one corresponding to the current active data_ids"""
        all_active_data_ids = self.sxm_select.value
        self.tagging.update_data_id(all_active_data_ids)

    def update_like(self):
        """Updates the likebutton with the current active data_ids"""
        all_active_data_ids = self.sxm_select.value
        self.likebutton.update_data_id(all_active_data_ids)

    ### Helper functions
    
    def external_open(self,data_id):
        print('sxm_viewer.external_open(',data_id,') called')
        if data_id in self.data_ids_sxm:
            self.data_id = data_id
            self.sxm_select.value = data_id
            self.get_current_display_properties()
            self.on_submit(None)
        else:
            print('sxm_viewer.external_open(data_id) called with data_id not in data_ids_sxm')

    ### Read and Write display properties to database
    
    def get_current_display_properties(self):
        """
        Updates the current display_properties of the SXM image with the data_id in the widgets.

        Accessed properties:
        self.selector_sxm_channel.options
        self.selector_sxm_channel.value
        self.sxm_direction.value
        self.sxm_flatten.value
        self.sxm_offset.value
        self.sxm_scale.value
        self.sxm_show_params.value
        """

        # self.selector_sxm_channel.options
        self.selector_sxm_channel.options = self.db.db_get(self.data_ids_sxm[0],'channel_names')
        # self.selector_sxm_channel.value
        current_channel = self.db.db_get(self.data_id,'current_channel')
        if current_channel == None:
            current_channel = self.db.db_get(self.data_id,'fchannel')
            self.db.db_write(self.data_id,'current_channel',current_channel)
        self.selector_sxm_channel.value = current_channel
        # self.sxm_direction.value
        sxm_direction = self.db.db_get(self.data_id,'current_direction')
        if sxm_direction == None:
            sxm_direction = 'forward'
            self.db.db_write(self.data_id,'current_direction',sxm_direction)
        self.sxm_direction.value = sxm_direction
        # self.sxm_flatten.value
        sxm_flatten = self.db.db_get(self.data_id,'current_flatten')
        if sxm_flatten == None:
            sxm_flatten = 'False'
            self.db.db_write(self.data_id,'current_flatten',sxm_flatten)
        self.sxm_flatten.value = sxm_flatten
        # self.sxm_offset.value
        sxm_offset = self.db.db_get(self.data_id,'current_offset')
        if sxm_offset == None:
            sxm_offset = 0.0
            self.db.db_write(self.data_id,'current_offset',sxm_offset)
        self.sxm_offset.value = sxm_offset
        # self.sxm_scale.value
        sxm_scale = self.db.db_get(self.data_id,'current_scale')
        if sxm_scale == None:
            sxm_scale = 'Linear'
            self.db.db_write(self.data_id,'current_scale',sxm_scale)
        self.sxm_scale.value = sxm_scale
        # self.sxm_show_params.value
        sxm_show_params = self.db.db_get(self.data_id,'current_show_params')
        if sxm_show_params == None:
            sxm_show_params = 'Dont show'
            self.db.db_write(self.data_id,'current_show_params',sxm_show_params)
        self.sxm_show_params.value = sxm_show_params

    def write_current_display_properties(self):
        """
        Writes the current display_properties of the SXM image with the data_id in the widgets to the database.

        Accessed properties:
        self.selector_sxm_channel.value
        self.sxm_direction.value
        self.sxm_flatten.value
        self.sxm_offset.value
        self.sxm_scale.value
        self.sxm_show_params.value
        """

        # self.sxm_select.value
        self.db.db_write([],'sxm_viewer_value',self.sxm_select.value,super_prop=True)
        # self.selector_sxm_channel.value
        self.db.db_write(self.data_id,'current_channel',self.selector_sxm_channel.value)
        # self.sxm_direction.value
        self.db.db_write(self.data_id,'current_direction',self.sxm_direction.value)
        # self.sxm_flatten.value
        self.db.db_write(self.data_id,'current_flatten',self.sxm_flatten.value)
        # self.sxm_offset.value
        self.db.db_write(self.data_id,'current_offset',self.sxm_offset.value)
        # self.sxm_scale.value
        self.db.db_write(self.data_id,'current_scale',self.sxm_scale.value)
        # self.sxm_show_params.value
        self.db.db_write(self.data_id,'current_show_params',self.sxm_show_params.value)

    ### Generate header output ###
    def header_visibility_change(self, change):
        """
        Toggle the visibility of the header output
        """
        if self.header_visibility == False:
            self.header_visibility = True
            self.outheader.layout = self.header_layout_visible
        else:
            self.header_visibility = False
            self.outheader.layout = self.header_layout_hidden

    def generate_header(self):
        """Generates the header output for the current data_id and dispalys it as HTML table in self.outheader"""

        # Get the data_id
        self.data_id = self.sxm_select.value

        # Get the data
        sxm = self.db.db_get_data(self.data_id)

        # Get the header
        sxm_header = sxm.header

        # Generate the table
        table_html = '<div style="max-width: 400px; max-height: 400px; overflow: auto;">'
        table_html += f'<h2 style="font-size: 12px;">Header Information</h2>'
        table_html += f"<table style='font-size: 10px; line-height: 8px;'>"
        for key, value in sxm_header.items():
            table_html += f"<tr><td><b>{key}</b></td><td>{value}</td></tr>"
        table_html += "</table>"
        table_html += '</div>'

        # Display the table
        with self.outheader:
            clear_output(wait=True)
            display(ipw.HTML(table_html))
