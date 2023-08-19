import os


def get_file_type(filename: str):
    """
    The function takes a filename as input and returns the type of file based on its extension.

    Args:
      filename (str): A string representing the name of a file, including its extension.

    Returns:
      The function `get_file_type` takes a filename as input and returns the type of the file based on
    its extension. If the extension is ".json", it returns "JSON". If the extension is ".jpeg" or
    ".jpg", it returns "JPEG". Otherwise, it returns "Unknown".
    """
    _, extension = os.path.splitext(filename)
    if extension.lower() == ".json":
        return "JSON"
    elif extension.lower() in [".jpeg", ".jpg"]:
        return "JPEG"
    else:
        return "Unknown"
