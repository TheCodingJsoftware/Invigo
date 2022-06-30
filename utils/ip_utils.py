import socket

from utils.json_file import JsonFile

settings_file = JsonFile("settings")


def get_server_ip_address() -> str:
    """
    It returns the value of the "server_ip" key in the settings file

    Returns:
      The value of the item_name "server_ip" from the settings_file.
    """
    return settings_file.get_value(item_name="server_ip")


def get_server_port() -> int:
    """
    It returns the value of the "server_port" item in the settings file

    Returns:
      The value of the item "server_port" in the settings file.
    """
    return settings_file.get_value(item_name="server_port")


def get_system_ip_address() -> str:
    """
    It gets the IP address of the system by getting the hostname of the system and then getting the IP
    address of the hostname

    Returns:
      The IP address of the system.
    """
    return socket.gethostbyname(socket.gethostname())
