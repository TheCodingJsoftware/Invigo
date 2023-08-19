from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


def get_trusted_users() -> list[str]:
    """
    This function returns a list of strings that are the trusted users

    Returns:
      A list of strings.
    """
    return settings_file.get_value(item_name="trusted_users")
