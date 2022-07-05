import os
import time
import urllib.request
import zipfile

import requests
from tqdm import tqdm

download_link: str = "https://github.com/TheCodingJsoftware/Inventory-Manager/releases/latest/download/Inventory.Manager.zip"
file_name: str = ""


def download(url):
    """
    Downloads a file from a url and displays a progress bar using tqdm

    Args:
      url: The URL of the file you want to download.
    """
    global file_name
    try:
        get_response = requests.get(url, stream=True)
        file_name = url.split("/")[-1]
        total_download: int = 0
        with open(file_name, "wb") as f, tqdm(
            desc=file_name,
            total=57670000,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in get_response.iter_content(chunk_size=1024):
                if chunk:
                    total_download += len(chunk)
                    bar.update(len(chunk))
                    f.write(chunk)
    except Exception as e:
        print(f"{str(e)} ABORTING..")


def extract(file_name):
    """
    It will try to extract the zip file, and if it fails, it will wait 1 second and try again

    Args:
      file_name: The name of the file you want to extract.
    """
    extracted: bool = False
    while not extracted:
        try:
            with zipfile.ZipFile(file_name, "r") as zip_ref:
                zip_ref.extractall(".")
                extracted = True
        except Exception as e:
            if "update.exe" in str(e):
                extracted = True
            if "Inventory Manager.exe" in str(e):
                print("Close Inventory Manager.exe (NOT THIS WINDOW)")
        time.sleep(1)


print("Do. not. close. this. window.")
time.sleep(1)
print("Download starting...")
time.sleep(1)
download(url=download_link)
print("Download finished. :)")
print("Installing... :O")
extract(file_name=file_name)
os.remove(file_name)
print("Finished. :D")
time.sleep(2)
