import difflib
import filecmp
import os
from datetime import datetime


class FileChanges:
    def __init__(self, from_file: str, to_file: str):
        self.from_file = from_file
        self.to_file = to_file

        self.file_name = self.to_file.replace(".json", "").replace("data/", "")

        self.from_file_size: int = 0
        self.to_file_size: int = 0

    def which_file_changed(self) -> str:
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
        self.from_file_size = os.path.getsize(self.from_file)
        self.to_file_size = os.path.getsize(self.to_file)
