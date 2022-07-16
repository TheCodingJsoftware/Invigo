import os
import zipfile
from datetime import datetime


def compress_database(path_to_file: str, on_close: bool = False) -> None:
    """
    It takes a path to a file, and creates a zip file in the backups directory with the current date and
    time as the name, and the file as the content

    Args:
      path_to_file (str): str = The path to the file you want to compress.
      on_close (bool): bool = False. Defaults to False
    """
    file_name: str = path_to_file.split("/")[-1]
    if on_close:
        path_to_zip_file: str = f"backups/{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')} - (Auto Generated).zip"
    else:
        path_to_zip_file: str = (
            f"backups/{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}.zip"
        )
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
