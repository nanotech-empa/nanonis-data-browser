"""
Author:         Lysander Huberich
Description:    database manager class for python based Nanonis data browser

"""

### Load libraries
import os
import pickle
import sys
sys.path.append('K:/Labs205/labs/THz-STM/Software/spmpy')
from spmpy_terry import spm
import spmpy_terry as spmpy
from helpers import fname_generator
import datetime


class db_manager():
    """
    db_manager is a class for managing the database.


    Functionality:

    
    Class Variables:
        db_data = {fname1:fdata1,...}
        db_prop = {data_prop:{fname1:{display_property1:display_property_value1,...,meta_property1:meta_property_value1,...},...,},
                   stitch:{stitched_id1:{stitched_property1:stitched_property_value1,...},...},
                   super:{super_display_property1:super_display_property_value1,...}
                   link:{link_property1:link_property_value1,...}}

    """
    def __init__(self):
        
        # global directory

        self.db_data = {}
        self.db_prop = {'data_prop':{},'stitch':{},'super':{},'link':{}}
        self.database_loaded = False
        self.database_saved = False
        self.database_file = '_database.pickle'
        self.database_path_latest = None
        self.database_overwrite_save = None
        self.database_save_with_data = None
        self.directory = None

        # External shared variables
        self.open_with_viewer_data_id = None

        # db_prop keys
        self.db_meta_keys = ['filename_full','filename_ending','file_size','file_modified_date']
        self.super_keys = [("data_id_time_sorted",None),("sxm_viewer_value",None),("dat_viewer_value",None),('dat_viewer_value_2',None),('sxm_show_value',None),('db_save_time',None),('multi_y_plot_value',None)]
        self.stitch_keys = [("file_modified_date")]

        # Standard display properties
        self.display_properties_all = [("liked",False),("group",None),("checked",False),("tags",[]),("channel_names",[]),("prerender",None)]
        self.display_properties_dat = [("current_xchannel",None),("current_ychannel",None),("fxchannel",None),("fychannel",None),("direction",None),("calc_options",None),('spline_smoothness',None),
                                       ('sxm_ref',None),('current_show_positions',None)]
        self.display_properties_sxm = [("current_channel",None),("fchannel",None),("current_direction",None),("current_flatten",None),("current_offset",None),("current_scale",None),("current_show_params",None)]

    def create(self,directory:str,force_new_import:bool):
        """
        This function creates a database from a directory of files.

        Input:
            directory (str): directory of files to be loaded (folder_path)
            force_new_import (bool): if True, all files are reloaded, if False, trying to load database first
        
        """
        self.directory = directory
        # Create super properties
        self.create_super_properties()

        # Create file index
        db_meta_new = self.file_indexing(directory)
        self.data_checks(db_meta_new)

        # Should the database be loaded
        if force_new_import == False:
            # Check for database in directory
            if os.path.isfile(directory+'\\'+self.database_file):
                db_prop_loaded, db_data_loaded = db_manager.load_db(self,directory)
                """
                TODO:
                    # Self consistency check
                    # Can files be found in directory?
                    # Are all files in db_prop contained in db_data?
                    # Check for inconsistencies between file index db_meta_new and loaded database db_prop_loaded
                    # Create db_meta from db_prop['data_prop']
                """
                db_meta_loaded = self.db_meta_from_db_prop(db_prop_loaded)

                if len(db_meta_loaded) > len(db_meta_new):
                    print('db_manager.create: More files loaded than in directory.')
                    force_new_import = True
                else:
                    new_data_bool,file_incombability_bool,db_meta_new_elements = self.metadata_comparision(db_meta_loaded,db_meta_new)

                    if file_incombability_bool == True:
                        print('db_manager.create: File incompatibility detected. Importing from directory.')
                        force_new_import = True
                    else:
                        if new_data_bool == True:
                            print('db_manager.create: New files in directory.')
                            print('db_manager.create:',db_meta_new_elements)
                            force_new_import = False
                            self.add_new_elements(directory,db_meta_new_elements)
                        else:
                            print('db_manager.create: No new files in directory.')
                            force_new_import = False
                            self.db_data = db_data_loaded
                            self.db_prop = db_prop_loaded
                            self.update_db_data(directory=self.directory)
                            self.database_loaded = True
            else:
                print('db_manager.create: No pickle files found. Importing from directory.')
                force_new_import = True
        else:
            print('db_manager.create: force_new_import is True. Forcing new import from directory.')
        
        if force_new_import == True:
            self.__init__()
            self.directory = directory
            self.create_super_properties()
            self.add_new_elements(directory,db_meta_new)

    def add_new_elements(self,directory,db_meta_new_elements):
        """
        This function adds new files to db_prop and db_data.

        Input:
            db_meta_new_elements (list): list of dictionaries with file metadata with self.db_meta_keys as keys
        """
        print('db_manager.add_new_elements: Adding new elements to database.')

        # Write metadata from db_meta_new_elements to db_prop
        for d_meta_new_element in db_meta_new_elements:
            data_id = d_meta_new_element['filename_full']
            write_data_id = True
            for key in self.db_meta_keys:
                self.db_write(data_id,key,d_meta_new_element[key],write_data_id=write_data_id,write_display_property=True)
                write_data_id = False
        
        # Add new elements to db_data
        self.update_db_data(directory)

        # Update display_properties in db_prop
        self.create_standard_display_properties()
        self.update_standard_display_properties()
        
        # Update super_properties in db_prop
        self.update_super_properties()
        
    def update(self,directory:str):
        """
        This function updates the database from the directory of files.
        """
        # Create file index
        db_meta_new = self.file_indexing(directory)
        db_meta_internal = self.db_meta_from_db_prop(self.db_prop)

        new_data_bool,file_incombability_bool,db_meta_new_elements = self.metadata_comparision(db_meta_internal,db_meta_new)
    
        if file_incombability_bool == True:
            print('db_manager.update: File incompatibility detected.')
            # Save current database
            print('db_manager.update: !!! Saving current database.... Not implemented yet.')
            # Create new database
            force_new_import = True
        
        if new_data_bool == True:
            print('db_manager.update: New files in directory.')
            self.add_new_elements(directory,db_meta_new_elements)
            self.database_saved = False
        
        if new_data_bool == False:
            print('db_manager.update: No new files in directory.')
        
        return new_data_bool

    def db_meta_from_db_prop(self,db_prop):
        """
        Create db_meta from db_prop

        Output:
            db_meta with self.db_meta_keys
        """
        db_meta = [] # local
        for fname in db_prop['data_prop'].keys():
            d_meta = {}
            for key in self.db_meta_keys:
                d_meta.update({key:self.db_get(fname,key,db_prop=db_prop)})
            db_meta.append(d_meta)
        return db_meta

    def metadata_comparision(self,db_meta_old,db_meta_new):
        """
        Compare metadata in db_meta_old and db_meta_new.
        If new elements in db_meta_new is found, return new_data_bool = True and db_meta_new_elements.
        If file incompatibilities are found, return file_incombability_bool = True.

        Input:
            db_meta_old: db_meta with self.db_meta_keys
            db_meta_new: db_meta with self.db_meta_keys
        Output:
            new_data_bool: boolean, True if new data is found
            file_incombability_bool: boolean, True if the metadata of the files in the directory are not compatible with the metadata of the elements in data_meta_dic
            data_meta_dic_new_elements: dictionary of data metadata [{filename_full, filename_ending, file_size, file_modified_date},...] of the new elements in data_meta_dic_new not contained in data_meta_dic
        """
        # Output variables
        db_meta_new_elements = []
        new_data_bool = False
        file_incombability_bool = False

        print('db_manager.metadata_comparision: comparing meta_data')

        filenames_new_elements = []
        for i in range(0,len(db_meta_new)):
            filenames_new_elements.append(db_meta_new[i]['filename_full'])
        
        filenames_old_elements = []
        for i in range(0,len(db_meta_old)):
            filenames_old_elements.append(db_meta_old[i]['filename_full'])
        
        for i in range(0,len(filenames_new_elements)):
            try:
                index_old_element = filenames_old_elements.index(filenames_new_elements[i])
                if db_meta_old[index_old_element]['file_modified_date'] == db_meta_new[i]['file_modified_date']and db_meta_old[index_old_element]['file_size'] == db_meta_new[i]['file_size']:
                    pass
                else:
                    print('db_manager.metadata_comparison: WARNING: metadata is different for same filename',db_meta_new[i]['filename_full'])
                    file_incombability_bool = True
                    new_data_bool = False
                    db_meta_new_elements = []
                    return new_data_bool, file_incombability_bool, db_meta_new_elements
            except ValueError:
                new_data_bool = True
                db_meta_new_elements.append(db_meta_new[i])
                print('db_manager.metadata_comparision: new data found: ',db_meta_new[i]['filename_full'])
        return new_data_bool,file_incombability_bool,db_meta_new_elements
    
    def file_indexing(self,directory):
        ''' 
        This function returns a reverse time-sorted list of dict of files db_meta with meta-data in specified directory
        db_meta=[{filename_full, filename_ending, file_size, file_modified_date},...]
        
        Input:
            global directory
        Output:
            db_meta: reverse time-sorted dict of files with meta-data [{filename_full, filename_ending, file_size, file_modified_date},...]

        Example:
            db_meta = db_manager.file_indexing(directory)
        '''
        db_meta = []
        files = os.listdir(directory)
        files.sort(key=lambda x: os.path.getctime(os.path.join(directory, x)))
        files.reverse()

        for file in files:
            if file.endswith('.sxm') or file.endswith('.dat'):
                db_meta.append({"path":directory+'\\'+file,
                                "filename_full":file,
                                "filename_ending":file.split('.')[-1],
                                "file_size":os.path.getsize(os.path.join(directory,file)),
                                "file_modified_date":os.path.getmtime(os.path.join(directory, file))
                                })
        return db_meta

    def data_checks(self,db_meta):
        """
        This function checks db_meta for incompatibilities:
            - more than one '.' in filename
        """
        for element in db_meta:
            if element['filename_full'].count('.') > 1:
                print('db_manager.data_checks: WARNING: more than one "." in filename:',element['filename_full'])

    ##### super_display_property functions #####

    def create_super_properties(self):
        """
        Creates super properties (from __init__) for all files in db_prop['super']
        """
        for key_pair in self.super_keys:
            super_display_property = key_pair[0]
            super_display_property_value = key_pair[1]
            self.db_write([],super_display_property,super_display_property_value,super_prop=True,write_display_property=True)
        
    def update_super_properties(self):
        """
        Wrapper function for updating super_properties in db_prop['super']
        """
        self.filetime_sorter()

    def filetime_sorter(self):
        """
        This function creates a time-sorted list of data_id from db_prop['data_prop'] and writes it to
        db_prop['super']['data_id_sorted']
        
        """
        print('db_manager.filetime_sorter: update this function to work with stitched data')
        # Get the time of the data
        data_id_list = list(self.db_prop['data_prop'].keys())
        data_time_list = []
        for data_id in data_id_list:
            data_time_list.append(self.db_get(data_id,'file_modified_date'))

        # Sort the data_id by time
        data_id_time_sorted = [x for x, _ in sorted(zip(data_id_list, data_time_list), key=lambda pair: pair[1])]
        data_id_time_sorted.reverse()

        # Write the sorted data_id to db_prop['super']['data_id_sorted']
        super_display_property = 'data_id_time_sorted'
        super_display_property_value = data_id_time_sorted
        self.db_write([],super_display_property,super_display_property_value,super_prop=True)

        # Reorder db_prop['data_prop']
        unsorted_data_prop = self.db_prop['data_prop']
        sorted_data_prop = {key: unsorted_data_prop[key] for key in data_id_time_sorted}
        self.db_prop['data_prop'] = sorted_data_prop

    ##### display_property functions #####

    def create_standard_display_properties(self):
        """
        Creates standard display properties (from __init__) for all files in db_prop['data_prop']
        """

        for data_id in self.db_prop['data_prop'].keys():
            for display_property_pair in self.display_properties_all:
                # Check if display_properties exist
                #if self.db_get(data_id,display_property_pair[0]) == None:
                self.db_write(data_id,display_property_pair[0],display_property_pair[1],write_display_property=True)
            if self.db_get(data_id,'filename_ending') == 'dat':
                for display_property_pair in self.display_properties_dat:
                    self.db_write(data_id,display_property_pair[0],display_property_pair[1],write_display_property=True)
            if self.db_get(data_id,'filename_ending') == 'sxm':
                for display_property_pair in self.display_properties_sxm:
                    self.db_write(data_id,display_property_pair[0],display_property_pair[1],write_display_property=True)

    def update_standard_display_properties(self):
        """
        Wrapper function for various standard initialization functions for display properties.
        """
        self.favourite_channel()
        self.all_channels()

    def favourite_channel(self):
        """
        Find the favourite channel for each file in db_prop['data_prop'].
        """
        for data_id in self.db_prop['data_prop'].keys():
            
            filename_full = data_id
            filename_ending = self.db_get(data_id,'filename_ending')

            if filename_ending == 'sxm':
                try:
                    sxm_loaded = self.db_data[filename_full]

                    header = sxm_loaded.header
                    channels = sxm_loaded.channels
                    
                    feedback_status = header.get("z-controller").get("on")[0]
                    if feedback_status == '1': feedback_status_bool = True # Feedback is on
                    if feedback_status == '0': feedback_status_bool = False
                        
                    lockin_status = header.get("lock-in>lock-in status")
                    if lockin_status == 'ON': lockin_status_bool = True # Lock In is on
                    if lockin_status == 'OFF': lockin_status_bool = False
                    
                    PLL_status = header.get("oscillation control>output off")
                    if PLL_status == 'FALSE': PLL_status_bool = True # PLL is on
                    if PLL_status == 'TRUE': PLL_status_bool = False

                    if feedback_status_bool and 'z' in channels:
                        fchannel = 'z'
                        self.db_write(data_id,'fchannel',fchannel)
                    elif lockin_status_bool and 'dIdV' in channels:
                        fchannel = 'dIdV'
                        self.db_write(data_id,'fchannel',fchannel)
                    elif PLL_status_bool and 'df' in channels:
                        fchannel = 'df'
                        self.db_write(data_id,'fchannel',fchannel)
                    else:
                        fchannel = channels[0] # if all of these are not true, return default
                except KeyError:
                    print('db_manager.favourite_channel: sxm file '+ filename_full +' not loaded')
            
            if filename_ending == 'dat':
                try:
                    dat_loaded = self.db_data[filename_full]
                    channels = dat_loaded.channels
                    if 'V' in channels and 'dIdV' in channels:
                        fxchannel = 'V'
                        fychannel = 'dIdV'
                    else:
                        if len(channels)>1:
                            fxchannel = channels[0]
                            fychannel = channels[1]
                        else:
                            fxchannel = channels[0]
                            fychannel = channels[0]
                    self.db_write(data_id,'fxchannel',fxchannel)
                    self.db_write(data_id,'fychannel',fychannel)
                except KeyError:
                    print('db_manager.favourite_channel: dat file '+ filename_full +' not loaded')

    def all_channels(self):
        for data_id in self.db_get_all_ids():
            try:
                spm_loaded = self.db_data[data_id]
                channels = spm_loaded.channels
                self.db_write(data_id,'channel_names',channels)
            except KeyError:
                print('db_manager.all_channels: spm file '+ data_id +' not loaded')

    ##### db_prop functions #####

    def db_get(self,data_id:str,display_property:str,**kwargs):
        """
        This function performs a query in self.db_prop.

        Optional kwargs:
            db_prop: external db_prop instead of self.db_prop
            stitch_prop: bool, True then stitched_display_property is queried
            super_prop: bool, True then super_display_property is queried
            link_prop: bool, True then link_property is queried

        Input:
            data_id (str): fname or stitched_id or 'super'
            display_property (str): display_property, stitched_property or super_display_property to be queried
        
        Output:
            display_property_value or stitched_property_value or super_display_property_value or link_property_value
        
        Class Variables:
            self.db_prop
        
        Example:
            display_property_value = db_manager.db_get(data_id,display_property)
            display_property_value = db_manager.db_get(data_id,display_property,db_prop=db_prop_loaded)
            stitched_property_value = db_manager.db_get(stitched_id,stitched_property,stitch_prop=True)
            super_display_property_value = db_manager.db_get('super',super_display_property,super_prop=True)
            link_property_value = db_manager.db_get('link',link_property,link_prop=True)
        """

        if 'db_prop' in kwargs: db_prop = kwargs['db_prop']
        else: db_prop = self.db_prop
        
        if 'stitch_prop' in kwargs and kwargs['stitch_prop'] == True: db_base = 'stich'
        elif 'super_prop' in kwargs and kwargs['super_prop'] == True: db_base = 'super'
        elif 'link_prop' in kwargs and kwargs['link_prop'] == True: db_base = 'link'
        else: db_base = 'data_prop'
        
        # Input error handling
        if 'stitch_prop' in kwargs and 'super_prop' in kwargs or \
            'stitch_prop' in kwargs and 'link_prop' in kwargs or \
            'super_prop' in kwargs and 'link_prop' in kwargs:
            print('db_manager.db_get: Error: stitch_prop and super_prop cannot be kwards at the same time')
            return None
        
        # super_prop query
        if 'super_prop' in kwargs and kwargs['super_prop'] == True:
            try:
                display_property_value = db_prop[db_base][display_property]
            except KeyError:
                print('db_manager.db_get: KeyError: display_property '+str(display_property)+' not in db_prop[super]')
                display_property_value = None
            return display_property_value
        elif 'link_prop' in kwargs and kwargs['link_prop'] == True:
            try:
                display_property_value = db_prop[db_base][display_property]
            except KeyError:
                print('db_manager.db_get: KeyError: display_property '+str(display_property)+' not in db_prop[link]')
                display_property_value = None
            return display_property_value
        else:
            try:
                # Is data_fname in database db_prop
                d_prop = db_prop[db_base][data_id]
                try:
                    display_property_value = db_prop[db_base][data_id][display_property]
                except KeyError:
                    print('db_manager.db_get: KeyError: display_property '+str(display_property)+' not in db_prop')
                    display_property_value = None
            except KeyError:
                print('db_manager.db_get: KeyError: data_id '+str(data_id)+' not in db_prop[+'+str(db_base)+']')
                display_property_value = None
            return display_property_value
        
    def db_write(self,data_id:str,display_property:str,display_property_value, **kwargs):
        """
        This function creates a entry or value change in self.db_prop. Always replaces the value.

        Optional kwargs:
            write_data_id (bool): if True, allows to create new data_id entry
            write_display_property (bool): if True, allows to creat new display_property entry
            stitch_prop: bool, True then stitched_display_property is accessed
            super_prop: bool, True then super_display_property is accessed
            link_prop: bool, True then link_property is accessed
        
        Input:
            data_id (str): fname or stitched_id or 'super'
            display_property (str): display_property, stitched_property or super_display_property to be written
            display_property_value: display_property_value, stitched_property_value or super_display_property_value to be written

        Class Variables
            self.db_prop
        
        Example:
            db_manager.db_write(data_id,display_property,display_property_value)
            db_manager.db_write(data_id,display_property,display_property_value,write_data_id=True)
            db_manager.db_write(data_id,display_property,display_property_value,write_display_property=True)
            db_manager.db_write(stitched_id,stitched_property,stitch_property_value,stitch_prop=True)
            db_manager.db_write(stitched_id,stitched_property,stitch_property_value,stitch_prop=True,write_data_id=True)
            db_manager.db_write([],super_display_property,super_display_property_value,super_prop=True)
            db_manager.db_write([],super_display_property,super_display_property_value,super_prop=True,write_data_id=True)
            db_manager.db_write([],link_property,link_property_value,link_prop=True)
        """

        if 'write_data_id' in kwargs: write_data_id = kwargs['write_data_id']
        else: write_data_id = False
        if 'write_display_property' in kwargs: write_display_property = kwargs['write_display_property']
        else: write_display_property = False

        if 'stitch_prop' in kwargs and kwargs['stitch_prop']: db_base = 'stich'
        elif 'super_prop' in kwargs and kwargs['super_prop']: db_base = 'super'
        elif 'link_prop' in kwargs and kwargs['link_prop']: db_base = 'link'
        else: db_base = 'data_prop'
        
        # Input error handling
        if 'stitch_prop' in kwargs and 'super_prop' in kwargs:
            print('db_manager.db_write: Error: stitch_prop and super_prop cannot be kwards at the same time')
            return None
        if 'stitch_prop' in kwargs and 'link_prop' in kwargs:
            print('db_manager.db_write: Error: stitch_prop and link_prop cannot be kwards at the same time')
            return None
        if 'super_prop' in kwargs and 'link_prop' in kwargs:
            print('db_manager.db_write: Error: super_prop and link_prop cannot be kwards at the same time')
            return None

        if write_data_id:
            if data_id not in list(self.db_prop[db_base]):
                if db_base=='super' or db_base=='link':
                    pass
                else:
                    self.db_prop[db_base].update({data_id:{}})
            else:
                print('db_manager.db_write: cannot create existing data_id in db_prop[+'+str(db_base)+']')
        
        database_was_changed = False
        try:
            # Does data_id in in database db_prop[db_base] exsist?
            if db_base=='super' or db_base=='link':
                pass
            else:
                _ = self.db_prop[db_base][data_id]
            try:
                # Does display_property in database db_prop[db_base][data_id] exsist?
                if db_base=='super':
                    _ = self.db_prop[db_base][display_property]
                    # Write display_property_value
                    self.db_prop[db_base][display_property] = display_property_value
                elif db_base=='link':
                    _ = self.db_prop[db_base][display_property]
                    # Write link_property_value
                    self.db_prop[db_base][display_property] = display_property_value
                else:
                    _ = self.db_prop[db_base][data_id][display_property]
                    # Write display_property_value
                    self.db_prop[db_base][data_id][display_property] = display_property_value
                database_was_changed = True
            except KeyError:
                if write_display_property:
                    if db_base=='super':
                        self.db_prop[db_base].update({display_property:display_property_value})
                    elif db_base=='link':
                        self.db_prop[db_base].update({display_property:display_property_value})
                    else:
                        self.db_prop[db_base][data_id].update({display_property:display_property_value})
                    database_was_changed = True
                else:
                    print('KeyError: display_property '+str(display_property)+' not in database')
                database_was_changed = True
        except KeyError:
            print('db_manager.dp_write: KeyError: data_id '+str(data_id)+' not in db_prop[+'+str(db_base)+']')
            database_was_changed = False
        
        if database_was_changed == True:
            self.database_saved = False
        
    ##### db_data functions #####

    def db_get_data(self,data_id:str):
        return self.db_data[data_id]

    def load_file(self,directory,filename_full):
        """
        This function loads file defined by path and filename_full and writes the loaded data to db_data.

        "db_manager.load_file(self,directory,filename_full)"

        Input:
            directory: str
            filename_full: str
        
        Class Variables:
            self.db_data
        """
        ## Check (should not be needed)
        if filename_full in self.db_data:
            print('db_manager.load_file: File already loaded in db_data.')
        file_ending = filename_full.split('.')[-1]
        if not(file_ending == 'sxm' or file_ending == 'dat'):
            print('db_manager.load_file: File is not .sxm or .dat.')

        ## Load data file
        path = directory+'\\'+filename_full
        loaded = spmpy.spm(path)
        self.db_data.update({filename_full:loaded})
    
    def update_db_data(self,directory):
        """
        This function updates the db_data by loading all files in db_prop['data_prop'] that are not yet loaded.

        Input:
            directory: str
        """
        loaded_files = self.db_data.keys()
        for fname in self.db_prop['data_prop'].keys():
            if fname not in loaded_files:
                self.db_data.update({'fname':self.load_file(directory,fname)})

    def db_get_all_ids(self):
        """
        This function returns a list of all data_ids in db_prop['data_prop'].

        "db_manager.db_get_all_ids(self)"

        Output:
            data_ids: list of str
        """
        data_ids = list(self.db_prop['data_prop'].keys())
        return data_ids

    ##### db import & export functions #####

    def save_db(self,directory: str, **kwargs):
        """
        This function saves db_prop and (db_data, if with_data == True)
        to a pickle file in the specified directory with the name self.database_file

        "db_manager = save_db(self,directory,with_data,overwrite)"

        Input:
            directory: of self.database_file
            
        Optional Arguments:
            overwrite: if True, the database is overwritten
            with_data: if True, db_data is saved as well
        """

        if 'overwrite' in kwargs:
            overwrite = kwargs['overwrite']
        else:
            if self.database_overwrite_save != None:
                overwrite = self.database_overwrite_save
            else:
                overwrite = False
        if 'with_data'  in kwargs:
            with_data = kwargs['with_data']
        else:
            if self.database_save_with_data != None:
                with_data = self.database_save_with_data
            else:
                with_data = False

        self.db_write([],'db_save_time',datetime.datetime.now(),super_prop=True)

        if os.path.isfile(directory+'\\'+self.database_file) and not overwrite:
            proposed_filebase = self.database_file.split('.')[0]
            file_ending = self.database_file.split('.')[1]
            self.database_file = fname_generator(directory,proposed_filebase,file_ending)

        db_export_group = {'db_prop':self.db_prop}
        db_export_group.update({'this_is_a_database_for_the_databrowser':True})
        if with_data:
            db_export_group.update({'db_data':self.db_data})
        
        with open(directory+'\\'+self.database_file, 'wb') as handle:
            pickle.dump(db_export_group, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        self.database_saved = True
        print('db_manager.save_db: directory: ',directory, ' self.database_file: ',self.database_file, ' with_data: ',with_data, ' overwrite: ',overwrite)
    
    def load_db(self,directory: str,**kwargs):
        """
        This function loads the db_prop and (db_data, if available)
        from a pickle file in the specified directory with the name self.database_file

        "db_prop_loaded = db_manager.load_db(self,directory)"

        Input:
            directory: of self.database_file

        Optional Arguments:
            database_check: bool, if True, the database is checked for compatibility and the function returns is_this_a_database bool
            contains_data_check: bool, if True, the database is checked for data and the function returns contains_data bool
        
        Output (if database_check == False and contains_data_check == False) or no optional arguments:
            db_prop: dict
            db_data: dict

        Output (if database_check == True):
            is_this_a_database: bool
        Output (if contains_data_check == True):
            does_it_contain_data: bool
        Output (if database_check == True and contains_data_check == True):
            is_this_a_database: bool
            does_it_contain_data: bool
        """
        # Parse optional arguments
        if 'database_check' in kwargs:
            database_check = kwargs['database_check']
        else:
            database_check = False
        if 'contains_data_check' in kwargs:
            contains_data_check = kwargs['contains_data_check']
        else:
            contains_data_check = False

        # Load pickle file
        with open(directory+'\\'+self.database_file, 'rb') as handle:
            db_export_group = pickle.load(handle)
        
        # Extract db_prop and db_data
        db_prop_loaded = db_export_group['db_prop']
        is_this_a_database = db_export_group['this_is_a_database_for_the_databrowser']
        if 'db_data' in db_export_group:
            does_it_contain_data = True
            db_data_loaded = db_export_group['db_data']
        else:
            does_it_contain_data = False
            db_data_loaded = {}

        # Returns
        if database_check == True:
            return is_this_a_database
        if contains_data_check == True:
            return does_it_contain_data
        if database_check == True and contains_data_check == True:
            return is_this_a_database, does_it_contain_data
        if database_check == False and contains_data_check == False:
            return db_prop_loaded, db_data_loaded

    ##### Helper functions #####

    def file_type_finder(self,wanted_file_type):
        """
        Searches the database for files of a certain type (e.g. 'dat' or 'sxm')

        Input:
            wanted_file_type: str (e.g. 'dat' or 'sxm')
        Output:
            data_id_with_wanted_file_type: list of data_ids with the wanted file_type
            file_type_found: True if any file_type is found, False if not
        """

        all_data_ids = self.db_get_all_ids()
        data_id_with_wanted_file_type= []

        for data_id in all_data_ids:
            file_type = self.db_get(data_id,'filename_ending')
            if file_type == wanted_file_type:
                data_id_with_wanted_file_type.append(data_id)
        if len(data_id_with_wanted_file_type) == 0:
            print("db_manager.file_type_finder: no files of type: ", wanted_file_type, " found")
            file_type_found = False
        else:
            file_type_found = True
        return data_id_with_wanted_file_type, file_type_found
    
    def newest_db(self,directory: str,**kargs):
        """
        This function returns the newest database file with the ending '.pickle' by checking 'super_prop' 'db_save_time' in the specified directory.

        Input:
            directory: str (folder_path)

        Optional Arguments:
            print_pickle_files: bool

        Output:
            newest_db: str (filename)
        """

        # Parse optional arguments
        if 'print_pickle_files' in kargs:
            print_pickle_files = kargs['print_pickle_files']
        else:
            print_pickle_files = False

        # Check if directory is a folder
        is_folder = os.path.isdir(directory)
        if not is_folder:
            print('db_manager.newest_db: directory is not a folder.')
            return None
        
        # Search for pickle files in directory
        all_files = os.listdir(directory)
        pickle_files = [f for f in all_files if f.split('.')[-1] == 'pickle']
        if print_pickle_files:
            print('db_manager.newest_db: pickle_files: ',pickle_files)
        if len(pickle_files) == 0:
            return None
        

        # Find newest pickle file
        db_save_times = []
        db_names = []
        for db in pickle_files:
            with open(directory+'\\'+db, 'rb') as handle:
                db_export_group = pickle.load(handle)
            if 'db_prop' in db_export_group.keys():
                db_prop_loaded = db_export_group['db_prop']
                if 'super' in db_prop_loaded.keys():
                    
                    if 'db_save_time' in db_prop_loaded['super'].keys():
                        db_save_times.append(db_prop_loaded['super']['db_save_time'])
                        db_names.append(db)
                    else:
                        print('db_manager.newest_db: db_prop[super] does not contain db_save_time.')
                        print('If the database is being saved, very shortly after creation, it is possible that the super_properties were not yet created.\
                               Upon next startup the saved database will not be properly initalized.')
                else:
                    print('db_manager.newest_db: db_prop does not contain super.')
            else:
                print('db_manager.newest_db: loaded pickle file ',db,' does not contain db_prop.')    
        
        try:
            newest_datetime = max(db_save_times)
            newest_db = db_names[db_save_times.index(newest_datetime)]
        except:
            print('db_manager.newest_db: no db_save_time found.')
            return None

        return newest_db

    def db_get_unused_link_property_name(self,proposed_name):
        """
        This function returns an unused link_property name based on the proposed_name.

        Input:
            proposed_name: str
        
        Output:
            link_property_name: str
        """
        all_current_link_property_names = self.db_prop['link'].keys()
        if proposed_name not in all_current_link_property_names:
            return proposed_name
        else:
            i = 1
            while True:
                proposed_name_new = proposed_name + '_' + str(i)
                if proposed_name_new not in all_current_link_property_names:
                    return proposed_name_new
                else:
                    i += 1


    