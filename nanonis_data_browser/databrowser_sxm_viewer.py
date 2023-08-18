### Load libaries
import sys
import ipywidgets as ipw
import checkbox
import likebutton
import tagging
from helpers import fname_generator, tempdir_maker

# Libraries for plotting
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

# Libraries for data handling
sys.path.append('K:/Labs205/labs/THz-STM/Software/spmpy')
from spmpy_terry import spm
import spmpy_terry as spmpy

from IPython.display import Image, display

import importlib
importlib.reload(checkbox)
checkbox = checkbox.checkbox
importlib.reload(likebutton)
likebutton = likebutton.likebutton
importlib.reload(tagging)
tagging = tagging.tagging



### databrowser_sxm_viewer

class databrowser_sxm_viewer():
    """
    Small SXM Viewer for the Data Browser

    'parameter_print_names' is a list of strings that will be used to print the parameters in the parameter area.
    'prerender' is a boolean that determines if the image is prerendered or not.
    """
    def __init__(self,data_id:str,db,**kwargs):

        self.data_id = data_id
        self.db = db
        self.sxm = db.db_get_data(self.data_id)

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
        self.channel_selector = ipw.Dropdown(options=[],description='Channel',disabled=False,layout=ipw.Layout(width='200px'))

        self.get_current_display_properties()
        self.channel_selector.observe(self.update_plot, names='value')

        # Displays
        self.outsxm = ipw.Output()
        self.parameter_area = ipw.HTML(value='',layout=ipw.Layout(width='200px',height='100px'))

        # Create Layout
        self.widgets = ipw.VBox([ipw.HBox([self.button_checkbox,self.button_like,self.open_viewer,self.tag_widgets]),
                                 ipw.HBox([self.outsxm,
                                           ipw.VBox([self.channel_selector,self.parameter_area])])])


    ### Database Interaction ###

    def get_current_display_properties(self):
        """
        Updates the current display_properties of the SXM image with the data_id in the widgets.

        Accessed properties:
        self.selector_sxm_channel.options
        self.selector_sxm_channel.value
        self.sxm_direction
        self.sxm_flatten
        self.sxm_offset
        self.sxm_scale
        """

        # self.selector_sxm_channel.options
        self.channel_selector.options = self.db.db_get(self.data_id,'channel_names')
        
        # self.selector_sxm_channel.value
        current_channel = self.db.db_get(self.data_id,'current_channel')
        if current_channel == None:
            current_channel = self.db.db_get(self.data_id,'fchannel')
            if current_channel == None:
                current_channel = self.channel_selector.options[0]
                print('databrowser_sxm_viewer.get_current_display_properties: Error: fchannel == None for ' + self.data_id)
            self.db.db_write(self.data_id,'current_channel',current_channel)
        self.channel_selector.value = current_channel

        # self.sxm_direction
        self.sxm_direction = self.db.db_get(self.data_id,'current_direction')
        if self.sxm_direction == None:
            self.sxm_direction = 'forward'
            self.db.db_write(self.data_id,'current_direction',self.sxm_direction)
        
        # self.sxm_flatten
        self.sxm_flatten = self.db.db_get(self.data_id,'current_flatten')
        if self.sxm_flatten == None:
            self.sxm_flatten = 'False'
            self.db.db_write(self.data_id,'current_flatten',self.sxm_flatten)
        
        # self.sxm_offset
        self.sxm_offset = self.db.db_get(self.data_id,'current_offset')
        if self.sxm_offset == None:
            self.sxm_offset = 0.0
            self.db.db_write(self.data_id,'current_offset',self.sxm_offset)

        # self.sxm_scale
        self.sxm_scale = self.db.db_get(self.data_id,'current_scale')
        if self.sxm_scale == None:
            self.sxm_scale = 'Linear'
            self.db.db_write(self.data_id,'current_scale',self.sxm_scale)

    def write_display_properties(self):
        """
        Writes the current display_properties of the SXM image with the data_id in the widgets to the database.

        Accessed properties:
        self.selector_sxm_channel.value
        """

        # self.selector_sxm_channel.value
        self.db.db_write(self.data_id,'current_channel',self.channel_selector.value)

    ### Callbacks ###

    def open_with_specific_viewer(self,b):
        self.db.open_with_viewer_data_id = self.data_id

    def update_plot(self,b):
        self.plot_sxm()
        self.parameter_print()
        #self.write_display_properties()

    ### Plotting ###

    def parameter_print(self):
        
        # default: print
        if self.parameter_print_names == None:
            pass
        else:
            pass

        parameter_list_str = ''
        

        fb_enable = self.sxm.get_param('z-controller>controller status')
        fb_ctrl = self.sxm.get_param('z-controller>controller name')
        bias = self.sxm.get_param('V')
        set_point = self.sxm.get_param('setpoint')
        height = self.sxm.get_param('height')
        width = self.sxm.get_param('width')
        angle = self.sxm.get_param('angle')
        z_offset = self.sxm.get_param('z_offset')
        comment = self.sxm.get_param('Comment')
    
        channels_in_sxm = self.sxm.channels
        parameter_list_str += 'channels: '
        for channel in channels_in_sxm:
            parameter_list_str += channel + ', '
        parameter_list_str += "\n"

        if fb_enable == 'OFF':
            pass
            #parameter_list_str += 'Feedback: OFF, z-offset: %s' % z_offset

        if np.abs(bias[0])<0.1:
            bias = list(bias)
            bias[0] = bias[0]*1000
            bias[1] = 'mV'
            bias = tuple(bias)


        parameter_list_str +=('I = %.0f%s\n' % set_point) 
        parameter_list_str +=('bias = %.0f%s\n' % bias)
        parameter_list_str +=('size: %.1f%s x %.1f%s (%.0f%s)\n' % (width+height+angle))
        parameter_list_str +=('comment: %s\n' % comment)
        #parameter_list_str +=('path: %s\n' % sxm.path)

        # Update self.parameter_area.value
        self.parameter_area.value = parameter_list_str

    def plot_sxm(self):
        run_plot = False
        if self.prerender == True:
            prerendered = self.db.db_get(self.data_id,'prerender')
            if prerendered==None:
                run_plot = True
            else:
                # Load plot from prerender if channel exists
                if self.channel_selector.value in prerendered.keys():
                    # Load plot from prerender
                    prerender_path = prerendered[self.channel_selector.value]
                    with self.outsxm:
                        self.outsxm.clear_output(wait=True)
                        display(Image(filename=prerender_path))
                else:
                    run_plot = True
        else:
            # Do plot
            run_plot = True

        if run_plot == True:
            # Plot Parameters
            direction = 'forward'
            direction = self.sxm_direction
            flatten = False
            flatten = self.sxm_flatten
            offset = 0
            offset = self.sxm_offset
            sxm_scale = 'Linear'
            self.sxm_scale = sxm_scale

            # Get the data
            (chData,chUnit) = self.sxm.get_channel(self.channel_selector.value,direction=direction,flatten=False,offset=offset)

            # Plot Parameters
            width = self.sxm.get_param('width')
            height = self.sxm.get_param('height')
            pix_y,pix_x = np.shape(chData)
            ImgOrigin = 'lower'
            if self.sxm.get_param('scan_dir') == 'down':
                ImgOrigin = 'upper'
            cmap = 'gray'
            sxm_scale = 'Linear'

            # Plot
            self.outsxm.clear_output(wait=True)
            fig_sxm, ax_sxm= plt.subplots(1,1,figsize=(2,2))

            # Plotting
            if sxm_scale == 'Log':
                im = ax_sxm.imshow(np.abs(chData), aspect = 'equal', extent = [0,width[0],0,height[0]], cmap = cmap, norm=LogNorm(), origin = ImgOrigin)
            else:
                im = ax_sxm.imshow(chData, aspect = 'equal',extent = [0,width[0],0,height[0]], cmap = cmap, origin = ImgOrigin)

            # TODO: if clim: plt.clim(clim)
                
            #im.axes.set_xticks([0,width[0]])
            #im.axes.set_xticklabels([0,np.round(width[0],2)])
            #im.axes.set_yticks([0,height[0]])
            #im.axes.set_yticklabels([0,np.round(height[0],2)])

            #plt.xlabel('x (%s)' % width[1])
            #plt.ylabel('y (%s)' % height[1])

            #cbar = plt.colorbar(im,fraction=0.046, pad=0.02, format='%.2g',shrink = 0.5,aspect=10)
            #cbar.set_label('%s (%s)' % (self.selector_channel.value,chUnit))
            plt.title(str(self.data_id),fontsize=8)

            if self.prerender == True:

                # Save plot as png to tempdir
                tempdir = tempdir_maker(self.db)
                new_filename = fname_generator(tempdir,'temp_sxm_', 'png')
                prerender_path = tempdir+'/'+new_filename
                fig_sxm.savefig(prerender_path, dpi=100, bbox_inches='tight')

                # Save path to prerender
                current_prerender = self.db.db_get(self.data_id,'prerender')
                if current_prerender == None:
                    current_prerender = {}

                current_prerender.update({self.channel_selector.value:prerender_path})
                self.db.db_write(self.data_id,'prerender',current_prerender)

            with self.outsxm:
                plt.show()
        
    
