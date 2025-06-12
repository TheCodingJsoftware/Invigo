import difflib
import os
import pathlib
import time
from datetime import datetime


class FileChanges:
    def __init__(self, from_file: str, to_file: str):
        self.server_file = from_file
        self.client_file = to_file

        self.file_name = (
            self.client_file.replace(".json", "").replace("data/", "").title()
        )

    def get_time_difference(self) -> float:
        try:
            server_file_modified_date = datetime.strptime(
                pathlib.Path(self.server_file).read_text(), "%m/%d/%Y %I:%M:%S %p"
            )
        except FileNotFoundError:
            return -1
        client_file_modified_date = datetime.strptime(
            str(
                time.strftime(
                    "%m/%d/%Y %I:%M:%S %p",
                    time.localtime(os.path.getmtime(self.client_file)),
                )
            ),
            "%m/%d/%Y %I:%M:%S %p",
        )
        time.strftime(
            "Database last updated on %A %B %d %Y at %I:%M:%S %p",
            time.localtime(os.path.getmtime(self.client_file)),
        )
        (
            datetime.now().strftime(
                "Database last updated on %A %B %d %Y at %I:%M:%S %p"
            ),
        )
        difference = client_file_modified_date - server_file_modified_date
        difference = difference.total_seconds()
        return difference

        # if difference > -15 and difference < 15:
        # return f'<p style="color:green;"> <b>{self.file_name}</b> - Up to date. - {datetime.now().strftime("%r")}</p>'
        # return (
        #     f'<p style="color:yellow;"> <b>{self.file_name}</b> - Your local changes are not uploaded.- {datetime.now().strftime("%r")}</p>'
        #     if difference > 0
        #     else f'<p style="color:red;"><b>{self.file_name}</b> - There are changes to the cloud file that are not present locally. - {datetime.now().strftime("%r")}</p>'
        # )

    def get_changes(self) -> str:
        changes: str = ""
        try:
            with open(self.server_file, "r", encoding="utf-8") as from_file:
                from_file_lines = from_file.readlines()
        except FileNotFoundError:
            return "Could not download file"
        with open(self.client_file, "r", encoding="utf-8") as to_file:
            to_file_lines = to_file.readlines()
        for line in difflib.unified_diff(
            from_file_lines,
            to_file_lines,
            fromfile=self.server_file,
            tofile=self.client_file,
            lineterm="",
            n=0,
        ):
            for prefix in ("---", "+++", "@@"):
                if line.startswith(prefix):
                    break
            else:
                changes += line
        return changes
