from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


def get_trusted_users() -> list[str]:
    return settings_file.get_value(item_name="trusted_users")
