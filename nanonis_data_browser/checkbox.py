import ipywidgets as ipw

class checkbox():
    """
    Creates a checkbox button (self.button_checkbox) and updates the state of the checkbox in the database

    Input:
        data_id: str or list[str]
        db: db_manager (db_write, db_get, db_get_all_ids)
        
    Output:
        self.button_checkbox

    External functions:
        checkbox_updater_external()
    """

    def __init__(self,data_id:str|list[str],db):
        
        self.db = db

        if type(data_id) == str:
            self.data_ids = [data_id]
        elif type(data_id) == list:
            self.data_ids = data_id
        else:
            raise ValueError('tagging.__init__: data_id must be str or list[str]')
        
        self.check_state = self.get_check_state()

        # Create Widget
        self.button_checkbox = ipw.Button()
        self.button_checkbox_state_change()
        self.button_checkbox.on_click(self.button_checkbox_clicked)

    ### Database Interaction ###

    def get_check_state(self):
        """Returns the check state of the data_id"""
        if len(self.data_ids) == 1:
            check_state = self.db.db_get(self.data_ids[0],'checked')
        else:
            check_state = True
            for data_id in self.data_ids:
                if self.db.db_get(data_id,'checked') == True:
                    if self.button_checkbox == True:
                        check_state = True
                else:
                    check_state = False
                    break
        return check_state

    def write_check_state(self):
        """Writes the check state of the data_id to the database"""
        if len(self.data_ids)==1:
            self.db.db_write(self.data_ids[0],'checked',self.check_state)
        else:
            for data_id in self.data_ids:
                self.db.db_write(data_id,'checked',self.check_state)
        
    ### Callbacks for widgets ###

    def button_checkbox_state_change(self):
        """Changes the icon and tooltip of the button_checkbox according to the check_state"""
        if self.check_state == True:
            self.button_checkbox.icon = 'check-square-o'
            self.button_checkbox.tooltip = 'Uncheck'
        else:
            self.button_checkbox.icon = 'square-o'
            self.button_checkbox.tooltip = 'Check'
        self.button_checkbox.description = ''
        self.button_checkbox.button_style = ''
        self.button_checkbox.layout = ipw.Layout(width='40px')

    def button_checkbox_clicked(self, b):
        """Changes the state of the button_checkbox and button_checkbox_state variable and updates the checkbox state in the database"""
        if self.check_state == True:
            self.check_state = False
        else:
            self.check_state = True
        self.button_checkbox_state_change()
        self.write_check_state()

    ### External functions ###

    def checkbox_updater_external(self):
        """
        Updates the state of the checkbox by reading the database
        """
        self.check_state = self.get_check_state()
        self.button_checkbox_state_change()

    