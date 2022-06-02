import difflib
import filecmp
import os
from datetime import datetime


# It's a class that keeps track of the changes made to a file
class FileChanges:
    def __init__(self, from_file: str, to_file: str) -> None:
        """
        This function takes two file names as input, and sets the file_name variable to the name of the
        file without the .json extension

        Args:
          from_file (str): The file that you want to copy from.
          to_file (str): The file that will be written to.
        """
        self.from_file = from_file
        self.to_file = to_file

        self.file_name = self.to_file.replace(".json", "").replace("data/", "")

        self.from_file_size: int = 0
        self.to_file_size: int = 0

    def which_file_changed(self) -> str:
        """
        If the files are the same, return a green message. If the local file is smaller than the cloud
        file, return a yellow message. If the local file is larger than the cloud file, return a red
        message

        Returns:
          A string.
        """
        changes: bool = filecmp.cmp(self.from_file, self.to_file, shallow=False)
        if changes:
            return f'<p style="color:green;"> <b>{self.file_name}</b> - Up to date. - {datetime.now().strftime("%H:%M:%S")}</p>'
        self.update_size()
        return (
            f'<p style="color:yellow;"> <b>{self.file_name}</b> - Your local changes are not uploaded.- {datetime.now().strftime("%H:%M:%S")}</p>'
            if self.from_file_size < self.to_file_size
            else f'<p style="color:red;"><b>{self.file_name}</b> - There are changes to the cloud file that are not present locally. - {datetime.now().strftime("%H:%M:%S")}</p>'
        )

    def update_size(self) -> None:
        """
        It updates the size of the files
        """
        self.from_file_size = os.path.getsize(self.from_file)
        self.to_file_size = os.path.getsize(self.to_file)
