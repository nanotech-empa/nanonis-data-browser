import ipywidgets as ipw
from IPython.display import display, clear_output

class likebutton():
    """
    Creates a like button (self.button_like) and updates the database accordingly.
    
    Input:
        data_id: str or list[str]
        db: db_manager (db_write, db_get, db_get_all_ids)

    Output:
        self.button_like or self.output

    External Functions:
        like_updater_external: Updates the like state of the button_like and button_like_state variable according to the database
        update_data_id: Changes the active data_id

    """
    
    def __init__(self, data_id: str | list[str], db):
        self.db = db
        
        if isinstance(data_id, str):
            self.data_ids = [data_id]
        elif isinstance(data_id, list):
            self.data_ids = data_id
        else:
            raise ValueError('LikeButton.__init__: data_id must be str or list[str]')
        
        self.like_state = self.get_like_state()
        
        # Create Widget
        self.button_like = ipw.Button()

        # Display Output
        self.output = ipw.Output()
        with self.output:
            clear_output(wait=True)
            display(self.button_like)

        self.button_like_state_change()
        self.button_like.on_click(self.button_like_clicked)

    ### Database Interaction ###

    def get_like_state(self):
        """Returns the like state of the data_id"""
        if len(self.data_ids) == 1:
            like_state = self.db.db_get(self.data_ids[0], 'liked')
        else:
            like_state = all(self.db.db_get(data_id, 'liked') for data_id in self.data_ids)
        return like_state
    
    def write_like_state(self):
        """Writes the like state of the data_id to the database"""
        for data_id in self.data_ids:
            self.db.db_write(data_id, 'liked', self.like_state)

    ### Callbacks for widgets ###

    def button_like_state_change(self):
        """Changes the icon and tooltip of the button_like according to the like_state"""
        if self.like_state:
            self.button_like.icon = 'star'
            self.button_like.tooltip = 'Unlike'
        else:
            self.button_like.icon = 'star-o'
            self.button_like.tooltip = 'Like'
        self.button_like.description = ''
        self.button_like.button_style = ''
        self.button_like.layout = ipw.Layout(width='40px')
        with self.output:
            clear_output(wait=True)
            display(self.button_like)

    def button_like_clicked(self, b):
        """Changes the state of the button_like and button_like_state variable and updates the like state in the database"""
        self.like_state = not self.like_state
        self.button_like_state_change()
        self.write_like_state()

    ### External Functions ###

    def like_updater_external(self):
        """Updates the like state of the button_like and button_like_state variable according to the database"""
        self.like_state = self.get_like_state()
        self.button_like_state_change()

    def update_data_id(self, data_id: str | list[str]):
        """Changes the active data_id"""
        if isinstance(data_id, str):
            self.data_ids = [data_id]
        elif isinstance(data_id, list):
            self.data_ids = data_id
        else:
            raise ValueError('LikeButton.update_data_id: data_id must be str or list[str]')
        self.like_updater_external()
