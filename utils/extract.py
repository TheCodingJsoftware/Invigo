from zipfile import ZipFile


def extract(file_to_extract: str) -> None:
    with ZipFile(file_to_extract, "r") as zip:
        zip.extractall(path="data/")
