import os


def get_file_type(filename: str):
    _, extension = os.path.splitext(filename)
    if extension.lower() == '.json':
        return 'JSON'
    elif extension.lower() == '.jpeg' or extension.lower() == '.jpg':
        return 'JPEG'
    else:
        return 'Unknown'