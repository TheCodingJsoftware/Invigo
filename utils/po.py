import contextlib
import os
from os import listdir
from os.path import isfile, join


def get_all_po() -> list[str]:
    return [po_file.split(".")[0] for po_file in listdir("PO's/templates") if isfile(join("PO's/templates", po_file)) and po_file.split(".")[-1] == "xlsx"]


def check_folders(folders: list[str]):
    for folder in folders:
        with contextlib.suppress(FileExistsError):
            if not os.path.exists(folder):
                os.mkdir(folder)


def check_po_directories():
    all_po_files = [
        po_file
        for po_file in listdir("PO's/templates")
        if isfile(join("PO's/templates", po_file)) and po_file.split(".")[-1] == "xlsx" or isfile(join("PO's/templates", po_file)) and po_file.split(".")[-1] == "xls"
    ]
    for template in all_po_files:
        extension: str = template.split(".")[-1]
        if extension in "xlsx":
            template: str = template.split(".")[0]
            check_folders([f"PO's/{template}"])
