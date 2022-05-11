import os
import zipfile
from datetime import datetime


def compress_database(path_to_file: str) -> None:
    file_name: str = path_to_file.split("/")[-1]
    path_to_zip_file: str = f"backups/{datetime.now().strftime('%Y-%m-%d-%H-%M')}.zip"
    zf = zipfile.ZipFile(path_to_zip_file, mode="w")
    zf.write(path_to_file, file_name, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()


def compress_folder(foldername, target_dir):
    zipobj = zipfile.ZipFile(f"{foldername}.zip", "w", zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])
