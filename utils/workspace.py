import contextlib
import math
import os

import ujson as json

class Workspace:
    def __init__(self, user: str) -> None:
        self.user: str = user
        self.data = {}
        
        self.file_name: str = 'workspace'
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.__create_file()
        self.load_data()

    def __create_file(self) -> None:
        """
        If the file doesn't exist, create it
        """
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def load_data(self) -> None:
        """
        It opens the file, reads the data, and then closes the file
        """
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                self.data = json.load(json_file)
        except Exception as error:
            print(error)
            
    def get_users_data(self, filter: dict) -> dict:
        '''
        filters should be for each tab there is in the prats in inventory
        {      tag ID     tag name
            "material": "304 SS",
            "thickness": "12 Gauge"
        }
        Consider filtering items relevant to the user
        '''
        data = {}
        

        pass
    
    def 
