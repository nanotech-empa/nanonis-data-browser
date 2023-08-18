### Load Libraries
import db_manager
import databrowser
import sxm_viewer
import dat_viewer

import importlib
importlib.reload(db_manager)
db_manager = db_manager.db_manager
importlib.reload(databrowser)
databrowser = databrowser.databrowser
importlib.reload(sxm_viewer)
sxm_viewer = sxm_viewer.sxm_viewer
importlib.reload(dat_viewer)
dat_viewer = dat_viewer.dat_viewer


import ipywidgets as ipw
from ipyfilechooser import FileChooser
import os
import threading
import time
from IPython.display import display, clear_output

### class loadapp

class loadapp():
    """
    Output:
        self.tab
    """

    def __init__(self,**kargs) -> None:
        """
        Loads the databrowser app
        Optional arguments:
            auto_start_up_bool: bool (default: False)
            directory: str (default: './')
        Output:
            self.tab
        """

        ## Parsing optional arguments
        if 'auto_start_up_bool' in kargs: self.auto_start_up_bool = kargs['auto_start_up_bool']
        else: self.auto_start_up_bool = False
        if 'directory' in kargs: self.directory = kargs['directory']
        else:self.directory = './'

        ## Starting db_manager
        self.db = db_manager()

        ## Auto start up
        self.inital_start_up_complete = False
        if self.auto_start_up_bool == True:
            # Is self.directory a valid path?
            if os.path.exists(self.directory) == False:
                print('loadapp.__init__: Auto start up enable in invalid directory: '+self.directory)
            else:
                print('loadapp.__init__: Auto start up enabled in directory: '+self.directory)
                self.db.create(self.directory,False)
                self.inital_start_up_complete = True

        self.create_load_tab_widgets()
        self.create_tab_layout_app()

        if self.inital_start_up_complete == True:
            self.load_data_layout_changes()

    ### Create Widgets and Layout ###

    def create_load_tab_widgets(self):
        """Creates all widgets for the loadapp (first tab)"""

        ## Load Options
        self.html_load = ipw.HTML(value='Load Options')

        # FileChooser
        self.fc = FileChooser('./')
        self.fc.default_path = './'
        if os.path.exists('./'+self.db.database_file):
            self.fc.default_filename = self.db.database_file

        # Database Load and Save
        self.db_load_option = ipw.Dropdown(options=['Enable','Disable'],value='Enable',description='Database Load:',disabled=False,tooltip='Allow for import of database',layout=ipw.Layout(width='200px'),style={'description_width': '100px'})
        self.db_save_option = ipw.Dropdown(options=['Enable','Disable'],value='Enable',description='Database Save:',disabled=False,tooltip='Immediate export of database',layout=ipw.Layout(width='200px'),style={'description_width': '100px'})
        self.db_save_with_data_option = ipw.Dropdown(options=['Enable','Disable'],value='Enable',description='Save with Data:',disabled=False,tooltip='Save database with data',layout=ipw.Layout(width='200px'),style={'description_width': '100px'})
        self.db_save_with_data_option.observe(self.db_save_with_data_option_change)
        self.db_maintance_option = ipw.Dropdown(options=['Enable','Disable'],value='Disable',description='Maintance:',disabled=False,tooltip='Enable automiatic seraching for new data and saving of database',layout=ipw.Layout(width='200px'),style={'description_width': '100px'})
        self.db_save_overwrite = ipw.Dropdown(options=['Enable','Disable'],value='Enable',description='Overwrite:',disabled=False,tooltip='Overwrite existing data in database',layout=ipw.Layout(width='200px'),style={'description_width': '100px'})
        self.db_save_overwrite.observe(self.db_save_overwrite_change)
        self.load_button = ipw.Button(description='Load',disabled=False,tooltip='Load data into database',icon='download',layout=ipw.Layout(width='150px'))
        self.database_file_default = self.db.database_file
        self.load_button.on_click(self.load_data)
        self.refresh_button = ipw.Button(description='Refresh Database',disabled=False,tooltip='Refresh file list',icon='refresh',layout=ipw.Layout(width='150px'))
        self.refresh_button.on_click(self.refresh_data)

        # Save Options
        self.html_save = ipw.HTML(value='Save Options')
        self.export_db_button = ipw.Button(description='Save Database',disabled=False,tooltip='Export database',icon='upload',layout=ipw.Layout(width='200px'))
        self.export_db_button.on_click(self.export_db)
        self.export_liked_button = ipw.Button(description='Export Liked and Tags',disabled=False,tooltip='Export liked data as text',icon='upload',layout=ipw.Layout(width='200px'))
        self.export_liked_button.on_click(self.save_liked_and_tags_as_text)

        # Background Service
        self.background_tasts_html = ipw.HTML(value='Background Service',layout=ipw.Layout(width='200px'))
        self.button_background_start = ipw.Button(description='',icon='play',disabled=False,tooltip='Start background tasks',layout=ipw.Layout(width='100px'))
        self.button_background_start.on_click(self.background_tasks_start)
        self.button_background_stop = ipw.Button(description='',icon='stop',disabled=True,tooltip='Stop background tasks',layout=ipw.Layout(width='100px'))
        self.button_background_stop.on_click(self.background_tasks_stop)
        self.html_background_tasks_status = ipw.HTML(value='Status: Not Running',layout=ipw.Layout(width='200px'))
        
        ## Layout
        self.loadapp_widgets = ipw.HBox([ipw.VBox([self.html_load,self.fc,self.db_load_option,self.db_save_option,self.db_save_with_data_option,self.db_maintance_option,self.db_save_overwrite,self.load_button,self.refresh_button]),
                                 ipw.VBox([self.html_save,self.export_db_button,self.export_liked_button]),
                                 ipw.VBox([self.background_tasts_html,
                                           ipw.HBox([self.button_background_start,self.button_background_stop]),
                                           self.html_background_tasks_status]),
                                 ])

    def create_tab_layout_app(self):
        """Create the tab layout for the app in the initalized state"""
        
        # Initialize the other tabs

        # Intialize the dat viewer output
        self.dat_viewer_widgets_out= ipw.Output()

        # Initialize the sxm viewer output
        self.sxm_viewer_widgets_out = ipw.Output()

        # Initialize the databrowser
        self.dbrowser_widgets_out = ipw.Output()

        # Create Tab Layout
        self.tab = ipw.Tab()
        self.tab.children = [self.loadapp_widgets,self.dbrowser_widgets_out,self.sxm_viewer_widgets_out,self.dat_viewer_widgets_out]
        self.tab.set_title(0, 'Load')
        self.tab.set_title(1, 'DataBrowser')
        self.tab.set_title(2, 'SXM Viewer')
        self.tab.set_title(3, 'DAT Viewer')
        self.tab.selected_index = 0

        # If inital start up is complete, initalize the tabs otherwise display a message
        if self.inital_start_up_complete == True:
            self.initalize_tabs()
        else:
            # Place holder for the other tabs
            with self.dat_viewer_widgets_out:
                display(ipw.HTML(value='DAT viewer not available. Please load database.'))
            with self.sxm_viewer_widgets_out:
                display(ipw.HTML(value='SXM viewer not available. Please load database.'))
            with self.dbrowser_widgets_out:
                display(ipw.HTML(value='Databrowser not available. Please load database.'))

    def initalize_tabs(self):
        """Initalize the tabs with the database"""
        
        # Initialize the dat viewer
        self.dat_viewer = dat_viewer(self.db)
        with self.dat_viewer_widgets_out:
            clear_output(wait=True)
            display(self.dat_viewer.dat_viewer_widgets)
        
        # Initialize the sxm viewer
        self.sxm_viewer = sxm_viewer(self.db)
        with self.sxm_viewer_widgets_out:
            clear_output(wait=True)
            display(self.sxm_viewer.sxm_viewer_widgets)
        
        # Initialize the databrowser
        self.dbrowser = databrowser(self.db)
        with self.dbrowser_widgets_out:
            clear_output(wait=True)
            display(self.dbrowser.widgets)
        # Additional observers on buttons in databrowser
        self.dbrowser.sort_execute.on_click(self.databroweser_refresh_out)
        self.dbrowser.button_refresh_db.on_click(self.databroweser_refresh_out)
        self.databrowser_open_with_viewer_linking()

        # Create tab level observers
        self.create_tab_level_observers()

    ### Tab Level Observers ###

    def create_tab_level_observers(self):
        """Create observers for the tab level widgets"""
        self.tab.observe(self.tab_change,'selected_index')

    def tab_change(self,change):
        """Callback function for tab change"""
        if change['new'] == 1: # DataBrowser Tab
            self.dbrowser.refresh_properties(None)
        if change['new'] == 2: # SXM Viewer Tab
            # self.sxm_viewer.__init__(self.db)
            self.sxm_viewer.update_like()
            self.sxm_viewer.update_tagging()
            self.sxm_viewer.likebutton.like_updater_external()
            #self.sxm_viewer.likebox.like_state = self.sxm_viewer.likebox.get_like_state()
            #self.sxm_viewer.likebox.button_like_state_change()
            # self.sxm_viewer_refresh_out(None)

    
    ### Refresh Output Functions ###

    def dat_viewer_refresh_out(self,x):
        self.dat_viewer_widgets_out.clear_output(wait=True)
        with self.dat_viewer_widgets_out:
            display(self.dat_viewer.dat_viewer_widgets)

    def sxm_viewer_refresh_out(self,x):
        self.sxm_viewer_widgets_out.clear_output(wait=True)
        with self.sxm_viewer_widgets_out:
            display(self.sxm_viewer.sxm_viewer_widgets)

    def databroweser_refresh_out(self,x):
        self.dbrowser_widgets_out.clear_output(wait=True)
        with self.dbrowser_widgets_out:
            display(self.dbrowser.widgets)
        self.databrowser_open_with_viewer_linking()

    ### Linking "open with viewer" buttons of databrowser viewers with the sxm and dat viewer ###

    def change_tab_to_specific_viewer(self,change):
        selected_data_id = self.db.open_with_viewer_data_id
        if selected_data_id == None:
            raise ValueError('loadapp.change_tab_to_specific_viewer(): Error: selected_data_id = ',selected_data_id)
        else:
            if self.db.db_get(selected_data_id,'filename_ending') == 'sxm':
                self.tab.selected_index = 2
                self.sxm_viewer.external_open(selected_data_id)
            elif self.db.db_get(selected_data_id,'filename_ending') == 'dat':
                self.tab.selected_index = 3
                self.dat_viewer.external_open(selected_data_id)
            else:
                raise ValueError('loadapp.change_tab_to_specific_viewer(): Error: filename_ending = ',self.db.db_get(selected_data_id,'filename_ending'))

    def databrowser_open_with_viewer_linking(self):
        """Links the "open with viewer" buttons of the databrowser viewers with the sxm and dat viewer"""
        all_initailized_viewers = self.dbrowser.get_all_initailized_viewers()
        try:
            for key in all_initailized_viewers.keys():
                if key not in self.linked_viewers:
                    all_initailized_viewers[key].open_viewer.on_click(self.change_tab_to_specific_viewer)
                    self.linked_viewers.append(key)
        except:
            self.linked_viewers = []
            for key in all_initailized_viewers.keys():
                all_initailized_viewers[key].open_viewer.on_click(self.change_tab_to_specific_viewer)
                self.linked_viewers.append(key)

    #### Callback Functions ####

    ### Change Database Variables

    def db_save_overwrite_change(self,change):
        if self.db_save_overwrite.value == 'Enable':
            self.db.database_overwrite_save = True
        else:
            self.db.database_overwrite_save = False
    
    def db_save_with_data_option_change(self,change):
        if self.db_save_with_data_option.value == 'Enable':
            self.db.database_save_with_data = True
        else:
            self.db.database_save_with_data = False
    
    ### Load Data Functions ###

    def load_data(self,change):
        
        if self.inital_start_up_complete == True:
            print('loadapp.load_data: start up already complete')
        else:
            directory = self.fc.selected_path
            selected_db_filename = self.fc.selected_filename
            print('loadapp.load_data: directory = ',directory)
        
            if directory == None:
                print('loadapp.load_data: no directory selected')
            else:

                if self.db_load_option.value == 'Enable':
                    current_force_new_import_bool = False

                    ### Check for existing database files
                    # Is a database file selected?
                    check_for_other_databases = False
                    if selected_db_filename != '':
                        # Check if selected file is a'.pickle' file
                        if selected_db_filename.endswith('.pickle'):
                            # Check if it is a viable database file
                            default_database_filename = self.db.database_file
                            self.db.database_file = selected_db_filename
                            is_this_a_database = self.db.load_db(directory,database_check=True)
                        else:
                            is_this_a_database = False
                        if is_this_a_database == True:
                            check_for_other_databases = False
                        else:
                            self.db.database_file = default_database_filename
                            check_for_other_databases = True
                    else:
                        check_for_other_databases = True
                    
                    if check_for_other_databases == True:                            
                        # Check for existing database files
                        possible_database_file = self.check_for_existing_database()
                        # Find newest database file
                        if len(possible_database_file) > 0:
                            newest_db = self.db.newest_db(directory)
                            if newest_db != None:
                                self.db.database_file = newest_db
                else:
                    current_force_new_import_bool = True
                
                # Creating database
                self.db.create(directory,current_force_new_import_bool)

                if self.db_save_overwrite.value == 'Enable':
                    self.db.database_overwrite_save = True
                else:
                    self.db.database_overwrite_save = False

                if self.db_save_with_data_option.value == 'Enable':
                    self.db.database_save_with_data = True
                else:
                    self.db.database_save_with_data = False

                # Saving database
                if self.db_save_option.value == 'Enable':
                    self.db.save_db(directory)

                # Initalizing tabs
                self.initalize_tabs()
                
                # Updating widgets
                self.dbrowser_widgets = self.dbrowser.widgets
                self.sxm_viewer_widgets = self.sxm_viewer.sxm_viewer_widgets
                self.dat_viewer_widgets = self.dat_viewer.dat_viewer_widgets
                self.tab.children = [self.loadapp_widgets,self.dbrowser_widgets,self.sxm_viewer_widgets,self.dat_viewer_widgets]

                self.inital_start_up_complete = True
                self.load_data_layout_changes()

                if self.db_maintance_option.value == 'Enable':
                    self.background_tasks_start(None)

    def load_data_layout_changes(self):
        if self.inital_start_up_complete == True:
            self.db_load_option.disabled = True
            self.db_save_option.disabled = True
            self.load_button.disabled = True
            self.db_maintance_option.disabled = True
        else:
            self.db_load_option.disabled = False
            self.db_save_option.disabled = False
            self.load_button.disabled = False
            self.db_maintance_option.disabled = False

    def check_for_existing_database(self):
        possible_database_file = []
        files = os.listdir(self.fc.selected_path)
        for file in files:
            if  file.endswith('.pickle'):
                possible_database_file.append(file)
        return possible_database_file
            
    ### Refresh Data Functions ###

    def refresh_data(self,change):
        """Checks the directory for new data and updates the database"""
        new_data = self.db.update(self.db.directory)

        if new_data == True:
            print('loadapp.refresh_data: New data found')
            # Update the databrowser
            self.dbrowser.refresh_viewers()
            self.databroweser_refresh_out(None)
            # Update the sxm viewer
            self.sxm_viewer.__init__(self.db)
            self.sxm_viewer_refresh_out(None)
            # Update the dat viewer
            self.dat_viewer.__init__(self.db)
            self.dat_viewer_refresh_out(None)
        else:
            print('loadapp.refresh_data: No new data found')
            
    ### Save Data Functions ###
    
    def export_db(self,change):
        """Saves the database"""
        self.db.save_db(self.db.directory)

    def save_liked_and_tags_as_text(self,change):
        """Saves the liked and tags data as a text file"""

        if self.inital_start_up_complete == False:
            print('loadapp.save_liked_as_text: inital_start_up_complete == False')
        else:
            if len(self.db.db_get_all_ids()) == 0:
                print("loadapp.save_liked: len(self.db.db_get_all_ids) == 0 i.e. no data in database")
            else:
                
                save_like_txt = []
                for data_id in self.db.db_get_all_ids():
                    liked = self.db.db_get(data_id,'liked')
                    tags = self.db.db_get(data_id,'tags')
                    if liked == True or tags != []:
                        line = self.db.db_get(data_id,'filename_full')
                        if liked == True:
                            line += ' liked'
                        if tags != []:
                            line += ' tags: ' + str(tags)
                        save_like_txt.append(line)
                '\n'.join(save_like_txt)
                
                with open(self.db.directory + '/liked_and_tags.txt', 'w') as f:
                    f.write('\n'.join(save_like_txt))
                print('loadapp.save_liked_and_tags_as_text: complete')

    ### Background Tasks Functions ###
    # - Checks peridodically for new data
    # - Saves database peridodically

    def background_tasks_new_data_thread(self):
        """Checks the directory for new data and updates the database"""
        new_data = self.db.update(self.db.directory)
        print('loadapp.background_tasks_new_data_thread: Checking for new data')
        if new_data == True:
            # Update the databrowser
            self.dbrowser.refresh_viewers()
            self.databroweser_refresh_out(None)
            # Update the sxm viewer
            self.sxm_viewer.__init__(self.db)
            self.sxm_viewer_refresh_out(None)
            # Update the dat viewer
            self.dat_viewer.__init__(self.db)
            self.dat_viewer_refresh_out(None)

    def background_tasks_save_db_thread(self):
        """Saves the database according to options specified in the load options"""
        self.db.save_db(self.db.directory)
        print('loadapp.background_tasks_save_db_thread: Saving database')

    def background_tasks_thread_wrapper(self):
        """Wrapper for the background tasks thread with a delay of 5 minutes"""
        while self.stop_event.is_set() == False:
            print('loadapp.background_tasks_thread_wrapper: Running background tasks')
            self.background_tasks_new_data_thread()
            time.sleep(5)
            self.background_tasks_save_db_thread()
            time.sleep(1*60)
        
    def background_tasks_start(self,change):
        """Starts the background tasks thread"""

        print('loadapp.background_tasks_start: Starting background tasks')

        # Change button layout
        self.button_background_start.disabled = True
        self.button_background_stop.disabled = False
        self.html_background_tasks_status.value = 'Status: Running'

        # Start thread
        self.stop_event = threading.Event()
        self.background_tasks_thread = threading.Thread(target=self.background_tasks_thread_wrapper)
        self.background_tasks_thread.start()

    def background_tasks_stop(self,change):
        """Stops the background tasks thread"""
        print('loadapp.background_tasks_stop: Stopping background tasks')

        # Change button layout
        self.button_background_start.disabled = False
        self.button_background_stop.disabled = True
        self.html_background_tasks_status.value = 'Status: Not Running'

        # Stop thread
        self.stop_event.set()
        self.background_tasks_thread.join()
        print('loadapp.background_tasks_stop: Background tasks stopped')
        

