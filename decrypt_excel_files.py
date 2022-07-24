import fnmatch
import os
from os import listdir
from os.path import isfile, join
from pathlib import Path

from utils.po_template import ExcelFile

files = []
for root, dirnames, filenames in os.walk(
    r"F:\Code\Python-Projects\Inventory Manager\PO's\Piney MFG"
):
    files.extend(
        os.path.join(root, filename) for filename in fnmatch.filter(filenames, "*.xls")
    )

for file in files:
    # e = ExcelFile(file)
    # e.convert_xls_to_xlsx()
    os.remove(file)
    print(file)
