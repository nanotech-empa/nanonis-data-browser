import ipywidgets as ipw
from IPython.display import display, clear_output

class tagging():
    """
    Provides a tagging buttons and displays for a given data_id.
    Requires "tags" as a display_property in the db.
    If multiple data_id are provided only common "tags" are modified.

    Input:
        data_id: str or list[str]
        db: db_manager (db_write, db_get, db_get_all_ids)

    Output:
        self.tag_widgets or self.output
        

    External methods:
        tag_area_updater_external(): Reloads the tags from db and updates the tag area
        update_data_id(): Changes the active data_id
    """
    
    def __init__(self, data_id: str | list[str], db):
        """
        Initialize the tagging widget.

        Output:
            self.tag_editing_group: ipw.HBox
            self.tag_display_group: ipw.HBox
        """
        self.db = db
        if isinstance(data_id, str):
            self.data_ids = [data_id]
        elif isinstance(data_id, list):
            self.data_ids = data_id
        else:
            raise ValueError('Tagging.__init__: data_id must be str or list[str]')

        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        
        # Tag display
        self.tag_display = ipw.TagsInput(value=self.get_current_tags_as_list(), placeholder='Press enter to add more',allow_duplicates=False,tooltip='Click to edit tags')
        self.tag_display.observe(self.tag_submit,names='value')
        
        # Layouts hidden and visible
        self.layout_hidden = ipw.Layout(width='1px',height='1px',visibility='hidden')
        self.layout_visible = ipw.Layout(width='100px',height='100px',visibility='visible')

        # Tag editing in Multiselect
        self.button_explore_tags = ipw.Button(description='',icon='fa-tags',disabled=False,tooltip='Explore existing tags',layout=ipw.Layout(width='40px'))
        self.button_explore_tags.on_click(self.explore_tags_clicked)
        self.multiselect_existing_tags = ipw.SelectMultiple(options=[],value=[],rows=5,description='',disabled=False,layout=self.layout_hidden)
        self.button_tag_submit = ipw.Button(description='',icon='fa-plus-square-o',disabled=False,tooltip='Submit tags updates',layout=self.layout_hidden)
        self.button_tag_submit.on_click(self.tag_submit)

        # Initial visibility of widgets
        self.tag_submit_visibility_change(False)
        self.multiselect_existing_tags_visibility_change(False)

        # Grouped output widgets
        
        self.tag_widgets = ipw.VBox([ipw.HBox([self.button_explore_tags,self.tag_display]),
                                     ipw.HBox([self.multiselect_existing_tags,self.button_tag_submit])])
        
        # Display Output
        self.output = ipw.Output()
        with self.output:
            clear_output(wait=True)
            display(self.tag_widgets)

    ### Database Interaction ###

    def get_current_tags_as_list(self):
        """
        Serches the database for the tags of the data_id. If there are multiple data_ids provided, only common tags are returned.

        Output:
            current_db_tags: list[str]
        """
        if len(self.data_ids) == 1:
            current_db_tags = self.db.db_get(self.data_ids[0],"tags")
        else:
            data_ids_tags_list = []
            for data_id in self.data_ids:
                db_tags = self.db.db_get(data_id,"tags")
                data_ids_tags_list.append(db_tags)
            common_tags = list(set(data_ids_tags_list[0]).intersection(*data_ids_tags_list))
            current_db_tags = common_tags
        return current_db_tags
            
    def get_all_tags(self):
        """
        Searches the database for all possible tags.

        Output:
            all_tags: list[str]
        """
        all_tags = []
        all_data_ids = self.db.db_get_all_ids()
        for data_id in all_data_ids:
            for tag in self.db.db_get(data_id,"tags"):
                if tag not in all_tags:
                    all_tags.append(tag)
        return all_tags

    ### Callbacks for widgets ###

    def tag_submit_visibility_change(self,visibility:bool):
        """
        Changes the visibility of button_tag_submit.

        Input:
            visibility: bool
        """
        if visibility: 
            self.button_tag_submit.layout = ipw.Layout(visibility='visible',width='40px')
            self.button_tag_submit.disabled = False
        else:
            self.button_tag_submit.layout = self.layout_hidden
            self.button_tag_submit.disabled = True
    
    def multiselect_existing_tags_visibility_change(self,visibility:bool):
        """
        Changes the visibility of multiselect_existing_tags and updates the options, if switched to visible.

        Input:
            visibility: bool
        """
        if visibility:
            self.multiselect_existing_tags.layout = self.layout_visible
            self.multiselect_existing_tags.options = self.get_all_tags()
            if len(self.data_ids) == 1:
                self.multiselect_existing_tags.value = self.db.db_get(self.data_ids[0],"tags")
            else:
                data_ids_tags_list = []
                for data_id in self.data_ids:
                    db_tags = self.db.db_get(data_id,"tags")
                    data_ids_tags_list.append(db_tags)
                common_tags = list(set(data_ids_tags_list[0]).intersection(*data_ids_tags_list))
                self.multiselect_existing_tags.value = common_tags
        else:
            self.multiselect_existing_tags.layout = self.layout_hidden
    
    def explore_tags_clicked(self,b):

        if self.multiselect_existing_tags.layout.visibility == 'visible':
            self.multiselect_existing_tags_visibility_change(False)
            self.tag_submit_visibility_change(False)
        else:
            self.multiselect_existing_tags_visibility_change(True)
            self.tag_submit_visibility_change(True)

    def tag_submit(self,b):
        """
        Submit tags updates from multiselect_existing_tags and tag_display.
        Updates the database with the new tags.
        """
        if self.multiselect_existing_tags.layout.visibility == 'visible':
            # Updating Tags according to db.db_write(self.data_id,"tags",new_tag_list)
            if len(self.data_ids) == 1:
                self.db.db_write(self.data_ids[0],"tags",self.multiselect_existing_tags.value)
            else:
                for data_id in self.data_ids:
                    current_tags = self.db.db_get(data_id,"tags")
                    new_tag_to_add = current_tags
                    for new_tag in self.multiselect_existing_tags.value:
                        if new_tag not in new_tag_to_add:
                            new_tag_to_add.append(new_tag)
                    self.db.db_write(data_id,"tags",new_tag_to_add)
            self.multiselect_existing_tags_visibility_change(False)
            self.tag_submit_visibility_change(False)
            self.tag_display.value = self.get_current_tags_as_list()
        else:
            if len(self.data_ids) == 1:
                self.db.db_write(self.data_ids[0],"tags",self.tag_display.value)
            else:
                for data_id in self.data_ids:
                    current_tags = self.db.db_get(data_id,"tags")
                    new_tag_to_add = current_tags
                    for new_tag in self.tag_display.value:
                        if new_tag not in new_tag_to_add:
                            new_tag_to_add.append(new_tag)
                    self.db.db_write(data_id,"tags",new_tag_to_add)

    ### External functions ###
    
    def tag_area_updater_external(self):
        """
        This function is called from outside to update the tag display
        """
        self.multiselect_existing_tags_visibility_change(False)
        self.tag_submit_visibility_change(False)
        self.tag_display.value = self.get_current_tags_as_list()
        with self.output:
            clear_output(wait=True)
            display(self.tag_widgets)

    def update_data_id(self, data_id: str | list[str]):
        """Changes the active data_id"""
        if isinstance(data_id, str):
            self.data_ids = [data_id]
        elif isinstance(data_id, list):
            self.data_ids = data_id
        else:
            raise ValueError('Tagging.update_data_id: data_id must be str or list[str]')
        self.tag_area_updater_external() 
