import ipywidgets as ipw
import threading, datetime, time
from IPython.display import display, clear_output

import databrowser_sxm_viewer
import databrowser_dat_viewer
import dat_viewer
import sxm_viewer
import helpers

import importlib
importlib.reload(databrowser_sxm_viewer)
databrowser_sxm_viewer = databrowser_sxm_viewer.databrowser_sxm_viewer
importlib.reload(databrowser_dat_viewer)
databrowser_dat_viewer = databrowser_dat_viewer.databrowser_dat_viewer
importlib.reload(dat_viewer)
dat_viewer = dat_viewer.dat_viewer
importlib.reload(sxm_viewer)
sxm_viewer = sxm_viewer.sxm_viewer
importlib.reload(helpers)
copy_to_clipboard_powershell = helpers.copy_to_clipboard_powershell




class databrowser():
    """
    Outputs a databrowser widget for viewing data in the database: self.widgets
    """

    def __init__(self,db,**kwargs):
        
        print('databrowser.__init__: Initializing Data Browser Display.')

        self.db = db

        # **kwargs
        if 'sort_by' in kwargs:
            self.sort_by = kwargs['sort_by']
        else:
            self.sort_by = 'Time Inverse'

        # Profiling ON or OFF
        self.profiling = False

        # Check if there is data in the database
        if len(list(self.db.db_prop['data_prop'].keys())) == 0:
            self.widgets = ipw.HTML(value="databrowser.__init__: db.db_data['data_prop'] is empty. No database initalized?")
            return
        
        # Create widgets
        self.create_widgets()


    ### Create Widgets
    def create_widgets(self):
        """
        Creates the widgets for the databrowser.
        """

        ## Create sidebar widgets
        self.create_widgets_sidebar()

        ## Create small data viewer widgets
        self.initalize_viewers()
        self.sort_and_display_viewers()

        # Update Sidebar Widgets
        self.tag_list_refresh(None)



        # Create Layout
        self.widgets = ipw.HBox([self.all_viewer_widgets,
                            ipw.VBox(children=[self.data_browser_options],layout=ipw.Layout(width='400px'))])

    def create_widgets_sidebar(self):
        """Creates the output widget (self.data_browser_options) for the databrowser sidebar."""

        ## Sidebar Widgets
        self.html_options = ipw.VBox([ipw.HTML(value='Data Browser Options')])

        # Refresh Options
        self.button_save_db = ipw.Button(description='Save Database',icon='upload',disabled=False,tooltip='Save Entire Database NOW',layout=ipw.Layout(width='200px'))
        self.button_save_db.on_click(self.save_db)

        self.button_refresh_db = ipw.Button(description='Refresh Database',icon='refresh',disabled=False,tooltip='Checks filepath for new files and adds them to the database',layout=ipw.Layout(width='200px'))
        self.button_refresh_db.on_click(self.refresh_db)

        self.button_refresh_properties = ipw.Button(description='Refresh Properties',disabled=False,tooltip='Refresh Properties (Tags and Likes) from Database',layout=ipw.Layout(width='200px'))
        self.button_refresh_properties.on_click(self.refresh_properties)

        # Sort Options
        self.html_sort_options = ipw.HTML(value='Sort Options:')

        self.sort_dropdown = ipw.Dropdown(options=['Name','Name Inverse','Time','Time Inverse','Tags','Tags Inverse','Selected Tags','Checked','Liked','Disliked'],value=self.sort_by,description='',disabled=False,layout=ipw.Layout(width='120px'))
        self.sort_dropdown.observe(self.tag_list_refresh, names='value')
    
        self.selected_tags_only = ipw.SelectMultiple(options=[],value=[],description='',disabled=True,layout=ipw.Layout(width='120px',height='100px'))

        self.sort_execute = ipw.Button(description='Sort',disabled=False,tooltip='Execute Sorting',layout=ipw.Layout(width='60px'))
        self.sort_execute.on_click(self.sort)

        # Selected Options
        self.html_selected_options = ipw.HTML(value='Modify Selected Elements:')

        self.button_check_all = ipw.Button(description='Select All',disabled=False,tooltip='Select all databrowser items',layout=ipw.Layout(width='120px'))
        self.button_check_all.on_click(self.check_all)
        self.button_uncheck_all = ipw.Button(description='Unselect All',disabled=False,tooltip='Unselect all databrowser items',layout=ipw.Layout(width='120px'))
        self.button_uncheck_all.on_click(self.uncheck_all)

        self.tag_input = ipw.Text(value='',placeholder='New tag',description='',disabled=False,layout=ipw.Layout(width='120px'))
        self.button_add_tag = ipw.Button(description='Add',disabled=False,tooltip='Add new tag',layout=ipw.Layout(width='60px'))
        self.button_add_tag.on_click(self.add_tag)
        self.button_delete_tag = ipw.Button(description='Delete',disabled=False,tooltip='Delete tag if exists',layout=ipw.Layout(width='60px'))
        self.button_delete_tag.on_click(self.delete_tag)
        
        self.button_like = ipw.Button(description='Like',disabled=False,tooltip='Like all selected',layout=ipw.Layout(width='60px'))
        self.button_like.on_click(self.like)
        self.button_unlike = ipw.Button(description='Unlike',disabled=False,tooltip='Unlike all selected',layout=ipw.Layout(width='60px'))
        self.button_unlike.on_click(self.unlike)

        self.export_png_button = ipw.Button(description='Export png',disabled=False,tooltip='Export png of all selected',layout=ipw.Layout(width='120px'))
        self.export_png_button.on_click(self.export_png)

        self.copy_png_button = ipw.Button(description='Copy png',disabled=False,tooltip='Copy png of all selected',layout=ipw.Layout(width='120px'))
        self.copy_png_button.on_click(self.copy_png)

        # Metadata Print Options
        self.html_metadata_options = ipw.HTML(value='Metadata Print Options:')
        self.metadata_dropdown = ipw.Dropdown(options=['dat','sxm','All'],value='All',description='',disabled=False,layout=ipw.Layout(width='120px'))
        self.metadata_dropdown.observe(self.metadata_dropdown_change, names='value')
        self.metadata_category_add_button = ipw.Button(description='',icon='plus',disabled=False,tooltip='Add new category',layout=ipw.Layout(width='60px'))
        self.metadata_category_add_button.on_click(self.metadata_category_add)
        self.metadata_add_show = False
        self.metadata_tags = ipw.TagsInput(placeholder='Tags',description='',disabled=False,layout=ipw.Layout(width='120px'))
        self.metadata_tags.observe(self.metadata_tags_change, names='value')
        self.metadata_condition = ipw.Text(value='',placeholder='Condition e.g. "filename_substring_ = XXX" or "fchannel = XXX"',description='',disabled=True,layout=ipw.Layout(width='180px',visibility='hidden'))
        self.metadata_category_name = ipw.Text(value='',placeholder='Category Name',description='',disabled=True,layout=ipw.Layout(width='180px',visibility='hidden'))

        self.data_browser_options = ipw.VBox([self.html_options,
                                              self.button_save_db,
                                              self.button_refresh_db,
                                              self.button_refresh_properties,
                                              ipw.VBox([self.html_sort_options,
                                                        ipw.HBox([self.sort_dropdown,self.sort_execute])]),
                                                        self.selected_tags_only,
                                              ipw.VBox([self.html_selected_options,
                                                        ipw.HBox([self.button_check_all,self.button_uncheck_all]),
                                                        ipw.HBox([self.tag_input,self.button_add_tag,self.button_delete_tag]),
                                                        ipw.HBox([self.button_like,self.button_unlike]),
                                                        ipw.HBox([self.export_png_button,self.copy_png_button]),
                                                        ]),
                                              ipw.VBox([self.html_metadata_options,
                                                        ipw.HBox([self.metadata_dropdown,self.metadata_category_add_button]),
                                                        ipw.HBox([self.metadata_category_name,self.metadata_condition]),
                                                        self.metadata_tags])
                                                ])

    ### Internal Functions ###

    def initalize_viewers(self,profiling=False):
        """
        Create a dictionary of all the viewer widgets for each data_id in the database.
        """
        
        if self.profiling:
            all_times = ''
            times_list = []
        
        # Create Item Viewers Widgets
        self.databrowser_items = {}
        self.databrowser_init_items = {} # Initalized classes
        
        for data_id in list(self.db.db_get('super','data_id_time_sorted',super_prop=True)):

            if self.profiling:
                start_time = time.time()

            try:
                if self.db.db_get(data_id,'filename_ending') == 'sxm':
                    viewer_sxm = databrowser_sxm_viewer(data_id,self.db,prerender=True)
                    self.databrowser_init_items.update({data_id:viewer_sxm})
                    viewer_sxm_widgets = viewer_sxm.widgets
                    self.databrowser_items.update({data_id:viewer_sxm_widgets})

                if self.db.db_get(data_id,'filename_ending') == 'dat':
                    viewer_dat = databrowser_dat_viewer(data_id,self.db,prerender=True)
                    self.databrowser_init_items.update({data_id:viewer_dat})
                    viewer_dat_widgets = viewer_dat.widgets
                    self.databrowser_items.update({data_id:viewer_dat_widgets})
            except Exception as e:
                print(f"databrowser.initalize_viewers: Error: Could not initalize databrowser viewer for data_id: {data_id} with the following error: {e}")

            
            if self.profiling:
                end_time = time.time()
                iteration_time = (end_time - start_time) * 1000
                times_list.append(iteration_time)
                time_line = str(data_id) + ": " + f"{iteration_time:.2f}" + " ms.\n"
                all_times += time_line

        if self.profiling:
            print(all_times)
            print(f"Average time: {sum(times_list)/len(times_list):.2f} ms.")
            print(f"Total time: {sum(times_list):.2f} ms.")

    def sort_and_display_viewers(self):
        """Creates the output widget (self.all_viwer_widgets) that displays all the viewer widgets."""

        self.databrowser_items_list = []
        for key in self.databrowser_items.keys():
            self.databrowser_items_list.append(self.databrowser_items[key])

        self.sort_viewers()

        self.all_viewer_widgets = ipw.VBox(children=self.databrowser_items_list,
                                      layout=ipw.Layout(display='flex-wrap',flex_flow='row wrap',justify_content='space-between',height='700px', overflow_y='auto',width='1000px'))
        self.widgets = ipw.HBox([self.all_viewer_widgets,
                    ipw.VBox(children=[self.data_browser_options],layout=ipw.Layout(width='400px'))])

    def sort_viewers(self):
        """
        Sorts the viewer widgets based on the selected sorting method.
        Sort Options:
            - Name (Filename Alphabetical)
            - Name Inverse (Filename Alphabetical Inverse)
            - Time (Filename Generation Time)
            - Time Inverse (Filename Generation Time Inverse)
            - Tags (Tag Alphabetical)
            - Tags Inverse (Tag Alphabetical Inverse)
            - Selected Tags (Only)
            - Checked (Only)
            - Liked (Only)
            - Not Liked (Only)
        """
        if self.sort_dropdown.value == 'Name' or self.sort_dropdown.value == 'Name Inverse':

            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Get the filenames for each data_id
            data_name_list = []
            for data_id in data_ids:
                data_name_list.append(self.db.db_get(data_id,'filename_full'))

            # Sort the data_id by name
            data_id_name_sorted = [x for x, _ in sorted(zip(data_ids, data_name_list), key=lambda pair: pair[1])]

            if self.sort_dropdown.value == 'Name Inverse':
                data_id_name_sorted.reverse()

            # Sort the viewer widgets by name
            self.databrowser_items_list = []
            for data_id in data_id_name_sorted:
                self.databrowser_items_list.append(self.databrowser_items[data_id])


        if self.sort_dropdown.value == 'Time' or self.sort_dropdown.value == 'Time Inverse':
            
            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Get the file modified date for each data_id
            data_time_list = []
            for data_id in data_ids:
                data_time_list.append(self.db.db_get(data_id,'file_modified_date'))

            # Sort the data_id by time
            data_id_time_sorted = [x for x, _ in sorted(zip(data_ids, data_time_list), key=lambda pair: pair[1])]

            if self.sort_dropdown.value == 'Time Inverse':
                data_id_time_sorted.reverse()

            # Sort the viewer widgets by time
            self.databrowser_items_list = []
            for data_id in data_id_time_sorted:
                self.databrowser_items_list.append(self.databrowser_items[data_id])
        

        if self.sort_dropdown.value == 'Tags' or self.sort_dropdown.value == 'Tags Inverse':
            
            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Get the tag for each data_id
            data_tag_list = []
            for data_id in data_ids:
                data_tag_list.append(self.db.db_get(data_id,'tags'))
            
            # Find unique tags
            unique_tags = list(set([item for sublist in data_tag_list for item in sublist]))
            unique_tags.sort() # Sort alphabetically

            tag_sorted_ids = []
            for tag in unique_tags:
                for id in data_ids:
                    if tag in self.db.db_get(id,"tags"):
                        tag_sorted_ids.append(id)
            
            if self.sort_dropdown.value == 'Tags Inverse':
                tag_sorted_ids.reverse()

            # Sort the viewer widgets by tag
            self.databrowser_items_list = []
            for data_id in tag_sorted_ids:
                self.databrowser_items_list.append(self.databrowser_items[data_id])

        if self.sort_dropdown.value == 'Selected Tags':
            
            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Find the data_ids of the elements that have the selected tags
            selected_tag_ids = []
            selected_tags = self.selected_tags_only.value
            selected_tags = list(selected_tags)

            for data_id in data_ids:
                print(self.db.db_get(data_id,'tags'))
                for selected_tag in selected_tags:
                    if selected_tag in self.db.db_get(data_id,'tags'):
                        selected_tag_ids.append(data_id)

            unique_selected_tag_ids = list(set(selected_tag_ids))
            
            # Output the selected tags
            self.databrowser_items_list = []
            for data_id in unique_selected_tag_ids:
                self.databrowser_items_list.append(self.databrowser_items[data_id])

        if self.sort_dropdown.value == 'Checked':

            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Find the data_ids of the elements that have been checked
            checked_ids = []
            for data_id in data_ids:
                if self.db.db_get(data_id,'checked'):
                    checked_ids.append(data_id)

            # Output the checked data_ids
            self.databrowser_items_list = []
            for data_id in checked_ids:
                self.databrowser_items_list.append(self.databrowser_items[data_id])
            
        if self.sort_dropdown.value == 'Liked':

            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Find the data_ids of the elements that have been liked
            liked_ids = []
            for data_id in data_ids:
                if self.db.db_get(data_id,'liked'):
                    liked_ids.append(data_id)
            
            # Output the liked data_ids
            self.databrowser_items_list = []
            for data_id in liked_ids:
                self.databrowser_items_list.append(self.databrowser_items[data_id])

        if self.sort_dropdown.value == 'Disliked':

            # Get all the data_ids
            data_ids = list(self.databrowser_init_items.keys())

            # Find the data_ids of the elements that have been disliked
            disliked_ids = []
            for data_id in data_ids:
                if self.db.db_get(data_id,'liked') == False:
                    disliked_ids.append(data_id)

            # Output the disliked data_ids
            self.databrowser_items_list = []
            for data_id in disliked_ids:
                self.databrowser_items_list.append(self.databrowser_items[data_id])
            
    ### Callbacks ###

    def metadata_dropdown_change(self,change):
        print('databrowser.metadata_dropdown_change: Not implemented yet.')

    def metadata_tags_change(self,change):
        print('databrowser.metadata_tags_change: Not implemented yet.')

    def metadata_category_add(self,change):
        if self.metadata_add_show == False:
            self.metadata_add_show = True
            self.metadata_category_name.disabled = False
            self.metadata_category_name.layout.visibility = 'visible'
            self.metadata_condition.disabled = False
            self.metadata_condition.layout.visibility = 'visible'
            self.metadata_category_add_button.tooltip = 'Submit new category'
        else:
            self.metadata_add_show = False
            self.metadata_category_name.disabled = True
            self.metadata_category_name.layout.visibility = 'hidden'
            self.metadata_condition.disabled = True
            self.metadata_condition.layout.visibility = 'hidden'
            self.metadata_category_add_button.tooltip = 'Add new category'
        print('databrowser.metadata_category_add: Not implemented yet.')

    def save_db(self,change):
        self.db.save_db(self.db.directory,with_data=True,overwrite=True)

    def refresh_db(self,change):
        """Checks the filepath for new files, adds them to the database and adds the viewers to the databrowser."""

        # Update the database
        new_data = self.db.update(self.db.directory)
        
        if new_data == False:
            print('databrowser.refresh_db: New data found.')
            self.refresh_viewers()
        else:
            print('databrowser.refresh_db: No new data found.')
    
    def refresh_viewers(self):
        """ Updates the databrowser viewers with the new data."""
        # Check which data_ids are not yet displayed
        all_data_ids = self.db.db_get_all_ids()
        all_displayed_data_ids = list(self.databrowser_items.keys())
        new_data_ids = []
        for data_id in all_data_ids:
            if data_id not in all_displayed_data_ids and self.db.db_get(data_id,'filename_ending') in ['sxm','dat']:
                new_data_ids.append(data_id)
        
        # Create new viewers for the new data_ids
        for data_id in new_data_ids:
            if self.db.db_get(data_id,'filename_ending') == 'sxm':
                viewer_sxm = databrowser_sxm_viewer(data_id,self.db,prerender=True)
                self.databrowser_init_items.update({data_id:viewer_sxm})
                viewer_sxm_widgets = viewer_sxm.widgets
                self.databrowser_items.update({data_id:viewer_sxm_widgets})

            if self.db.db_get(data_id,'filename_ending') == 'dat':
                viewer_dat = databrowser_dat_viewer(data_id,self.db,prerender=True)
                self.databrowser_init_items.update({data_id:viewer_dat})
                viewer_dat_widgets = viewer_dat.widgets
                self.databrowser_items.update({data_id:viewer_dat_widgets})
        
        # Sort the data_ids according to the current sorting and update the display
        self.sort_and_display_viewers()

    def refresh_properties(self,change):
        """Loads the likebutton and tag properties from the database and updates the widgets."""

        # Refreshing Tag from database
        for key in self.databrowser_items.keys():
            self.databrowser_init_items[key].tagging.tag_area_updater_external()

        # Refreshing Like from database
        for key in self.databrowser_items.keys():
            self.databrowser_init_items[key].likebox.like_updater_external()

    def sort(self,change):
        """Callback Function Wrapper. Sorts the databrowser_items according to the current sorting and updates the display."""
        self.sort_and_display_viewers()

    def tag_list_refresh(self,change):
        """Provides a list of all tags in the database and updates the self.selected_tags_only"""

        # Update the display
        all_tags = []
        for key in self.databrowser_items.keys():
            all_tags.append(self.db.db_get(key,'tags'))
        all_tags = list(set([item for sublist in all_tags for item in sublist]))
        all_tags.sort()
        self.selected_tags_only.options = all_tags
        if self.sort_dropdown.value == 'Selected Tags':
            self.selected_tags_only.disabled = False
            self.selected_tags_only.layout.visibility = 'visible'

        else:
            self.selected_tags_only.disabled = True
            self.selected_tags_only.layout.visibility = 'hidden'

    def check_all(self,change):
        """Sets the display_proptery 'checked' to True for all databrowser_items. And updates the checkbox."""
        for key in self.databrowser_items.keys():
            # Set database entry to checked
            self.db.db_write(key,'checked',True)
            # Update checkbox
            self.databrowser_init_items[key].checkbox.checkbox_updater_external()

    def uncheck_all(self,change):
        """Sets the display_proptery 'checked' to False for all databrowser_items. And updates the checkbox."""
        for key in self.databrowser_items.keys():
            # Set database entry to unchecked
            self.db.db_write(key,'checked',False)
            # Update checkbox
            self.databrowser_init_items[key].checkbox.checkbox_updater_external()

    def add_tag(self,change):
        """Read which data_id are selected and adds the tag to the corresponding database entries."""

        all_keys = list(self.databrowser_items.keys())

        # Read which data_ids are selected
        selected_keys = []
        for key in all_keys:
            if self.db.db_get(key,'checked')==True:
                selected_keys.append(key)
        
        if selected_keys == []:
            print('databrowser.delete_tag: No data_id selected.')

        # Add the tag to the database entries of selected data_ids
        for key in selected_keys:
            old_tags = self.db.db_get(key,'tags')
            if str(self.tag_input.value)not in old_tags:
                new_tags = old_tags
                new_tags.append(str(self.tag_input.value))
                self.db.db_write(key,'tags',new_tags)
        
        # Update the tag properties
        for key in selected_keys:
            # self.databrowser_init_items[key].tagging.tag_area_updater_external()
            self.databrowser_init_items[key].tagging.multiselect_existing_tags_visibility_change(False)
            self.databrowser_init_items[key].tagging.tag_submit_visibility_change(False)
            self.databrowser_init_items[key].tagging.tag_display.value = self.databrowser_init_items[key].tagging.get_current_tags_as_list()
        
    def delete_tag(self,change):
        """Read which data_id are selected and deletes the tag from the corresponding database entries."""

        print('databrowser.delete_tag: Does delete the tag from the database. But is unable to update the ipywidgets.TagsInput widget.')

        all_keys = list(self.databrowser_items.keys())

        # Read which data_ids are selected
        selected_keys = []
        for key in all_keys:
            if self.db.db_get(key,'checked')==True:
                selected_keys.append(key)

        if selected_keys == []:
            print('databrowser.delete_tag: No data_id selected.')

        # Delete the tag from the database entries of selected data_ids
        for key in selected_keys:
            old_tags = self.db.db_get(key,'tags')
            if str(self.tag_input.value) in old_tags:
                new_tags = old_tags
                new_tags.remove(str(self.tag_input.value))
                self.db.db_write(key,'tags',new_tags)
        
        # Update the tag properties
        for key in selected_keys:
            # self.databrowser_init_items[key].tagging.tag_area_updater_external()
            self.databrowser_init_items[key].tagging.multiselect_existing_tags_visibility_change(False)
            self.databrowser_init_items[key].tagging.tag_submit_visibility_change(False)
            self.databrowser_init_items[key].tagging.tag_display.value = self.databrowser_init_items[key].tagging.get_current_tags_as_list()

    def like(self,change):
        """Reads which data_id are selected and likes the corresponding database entries."""
        
        all_keys = list(self.databrowser_items.keys())

        # Read which data_ids are selected
        selected_keys = []
        for key in all_keys:
            if self.db.db_get(key,'checked')==True:
                selected_keys.append(key)
            
        if selected_keys == []:
            print('databrowser.like: No data_id selected.')
        
        # Like the database entries of selected data_ids
        for key in selected_keys:
            self.db.db_write(key,'liked',True)

        # Update the like properties
        for key in selected_keys:
            self.databrowser_init_items[key].likebox.like_updater_external()

    def unlike(self,change):
        """Reads which data_id are selected and unlikes the corresponding database entries."""
            
        all_keys = list(self.databrowser_items.keys())

        # Read which data_ids are selected
        selected_keys = []
        for key in all_keys:
            if self.db.db_get(key,'checked')==True:
                selected_keys.append(key)
            
        if selected_keys == []:
            print('databrowser.like: No data_id selected.')
        
        # Unlike the database entries of selected data_ids
        for key in selected_keys:
            self.db.db_write(key,'liked',False)
        
        # Update the like properties
        for key in selected_keys:
            self.databrowser_init_items[key].likebox.like_updater_external()
    
    def export_png(self,change):
        """Exports the png of all selected data_ids to the filepath of the database."""
        
        selected_keys = []
        for key in list(self.databrowser_items.keys()):
            if self.db.db_get(key,'checked')==True:
                selected_keys.append(key)
        
        if selected_keys == []:
            print('databrowser.export_png: No data_id selected.')



    def copy_png(self,change):
        """Copies the png of all selected data_ids to the clipboard."""

        selected_keys = []
        for key in list(self.databrowser_items.keys()):
            if self.db.db_get(key,'checked')==True:
                selected_keys.append(key)
        
        if selected_keys == []:
            print('databrowser.copy_png: No data_id selected.')
        
        # Create a list of all the figures to copy by opening the corresponding viewers
        all_fig_to_copy = []
        for key in selected_keys:
            if self.db.db_get(key,'filename_ending') == 'sxm':
                temp_sxm_viewer = sxm_viewer(self.db)
                temp_sxm_viewer.external_open(key)
                all_fig_to_copy.append(temp_sxm_viewer.fig_sxm)
                del temp_sxm_viewer
            elif self.db.db_get(key,'filename_ending') == 'dat':
                temp_dat_viewer = dat_viewer(self.db)
                temp_dat_viewer.external_open(key)
                temp_dat_viewer.fig_size_y.value = 4
                all_fig_to_copy.append(temp_dat_viewer.fig_combined)
                del temp_dat_viewer
            else:
                raise Exception(f"databrowser.copy_png: Error: filename_ending not recognized: {self.db.db_get(key,'filename_ending')}")
        
        # Copy the figures to the clipboard
        copy_to_clipboard_powershell(self.db,all_fig_to_copy,format="png",dpi=300)
                
            



    ### External Functions ###

    def get_all_initailized_viewers(self):
        """Returns a dictionary of all the initialized viewer classes."""
        return self.databrowser_init_items