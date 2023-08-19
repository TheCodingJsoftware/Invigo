from zipfile import ZipFile


def extract(file_to_extract: str) -> None:
    """
    > The function takes a file name as an argument and extracts the contents of the file to a folder
    called data

    Args:
      file_to_extract (str): The name of the file to extract.
    """
    with ZipFile(file_to_extract, "r") as zip:
        zip.extractall(path="data/")
