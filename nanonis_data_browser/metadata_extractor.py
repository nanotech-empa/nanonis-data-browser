### Import Libraries
import sys
import numpy as np

# Import spmpy
sys.path.append('K:/Labs205/labs/THz-STM/Software/spmpy')
from spmpy_terry import spm

class metadata:
    def __init__(self):
        self.all_metadata_keys = []
        self.metadata_keys = spm.ParamNickname + ['z-controller>controller name',]
        self.default_metadata_keys_sxm = ['z-controller>controller status','V','setpoint','height','width','angle','z_offset','comments']
        self.default_metadata_keys_dat = ['Z-Ctrl hold','setpoint_spec','V_spec','lockin_amplitude','lockin_phase','lockin_frequency','comment_spec']
    
    def metadata_print(self,db,data_id,keys):
        """
        Create metadata string for a given data_id and keys
        """
        # Get data from data_id
        spm_data = db.db_get_data(data_id)

        # Get metadata using SPMPY class

        meta_strs = []

        for key in keys:
            if key == 'path':
                meta_strs.append('path: %s' % self.path)  
            if key == 'z-controller>controller status':
                fb_enable = self.get_param('z-controller>controller status')
                if fb_enable == 'OFF':
                    meta_strs.append('constant height')

            if key == 'V':
                pass

            value = self.get_param(key)
            meta_strs += '%s: %s\n' % (key,value)

        return meta_strs




    # print essential parameters for plotting  
    def print_params(self, show = True):
    
        # import numpy as np
        
        label = []
        
        if self.type == 'scan':
            fb_enable = self.get_param('z-controller>controller status')
            
            bias = self.get_param('V')
            set_point = self.get_param('setpoint')
            height = self.get_param('height')
            width = self.get_param('width')
            angle = self.get_param('angle')
            z_offset = self.get_param('z_offset')
            comment = self.get_param('comments')
        
            if fb_enable == 'OFF':
                label.append('constant height')
                label.append('z-offset: %.3f%s' % z_offset)
                
            if np.abs(bias[0])<0.1:
                bias = list(bias)
                bias[0] = bias[0]*1000
                bias[1] = 'mV'
                bias = tuple(bias)
                
            label.append('I = %.0f%s' % set_point)    
            label.append('bias = %.2f%s' % bias)
            label.append('size: %.1f%s x %.1f%s (%.0f%s)' % (width+height+angle))
            label.append('comment: %s' % comment)
            
            
        elif self.type == 'spec':
            
            fb_enable = self.get_param('Z-Ctrl hold')
            set_point = self.get_param('setpoint_spec')
            bias = self.get_param('V_spec')
            #lockin_status = self.get_param('Lock-in>Lock-in status')
            lockin_amplitude = self.get_param('lockin_amplitude')
            lockin_phase= self.get_param('lockin_phase')
            lockin_frequency= self.get_param('lockin_frequency')
            comment = self.get_param('comment_spec')
            
                               
            #if lockin_status == 'ON':
            label.append('lockin: A = %.0f%s (θ = %.0f%s, f = %.0f%s)' % (lockin_amplitude+lockin_phase+lockin_frequency))
                 
            
            if fb_enable == 'FALSE':
                label.append('feedback on')
                
            elif fb_enable == 'TRUE':
                label.append('feedback off')
           
 
            label.append('setpoint: I = %.0f%s, V = %.1f%s' % (set_point+bias))    
            
            label.append('comment: %s' % comment)
    
        label.append('path: %s' % self.path)  
        label = '\n'.join(label)
        
        if show:
            print(label)
        
        return label