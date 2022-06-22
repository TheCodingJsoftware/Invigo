import os
import zipfile
from datetime import datetime


def compress_database(path_to_file: str) -> None:
    """
    It takes a path to a file, creates a zip file with the current date and time as the name, and then
    adds the file to the zip file

    Args:
      path_to_file (str): str = path_to_file.split("/")[-1]
    """
    file_name: str = path_to_file.split("/")[-1]
    path_to_zip_file: str = f"backups/{datetime.now().strftime('%Y-%m-%d-%H-%M')}.zip"
    file = zipfile.ZipFile(path_to_zip_file, mode="w")
    file.write(path_to_file, file_name, compress_type=zipfile.ZIP_DEFLATED)
    file.close()


def compress_folder(foldername, target_dir) -> None:
    """
    It takes a folder name and a target directory as input, and creates a zip file of the folder name in
    the target directory

    Args:
      foldername: The name of the folder you want to compress.
      target_dir: The directory to compress.
    """
    zipobj = zipfile.ZipFile(f"{foldername}.zip", "w", zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, _, files in os.walk(target_dir):
        for file in files:
            filename: str = os.path.join(base, file)
            zipobj.write(filename, filename[rootlen:])
