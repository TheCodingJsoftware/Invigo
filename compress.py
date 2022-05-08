import zipfile
from datetime import datetime


def compress_file(path_to_file: str) -> None:
    file_name: str = path_to_file.split("/")[-1]
    path_to_zip_file: str = f"backups/{datetime.now().strftime('%Y-%m-%d-%H-%M')}.zip"
    zf = zipfile.ZipFile(path_to_zip_file, mode="w")
    zf.write(path_to_file, file_name, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()
