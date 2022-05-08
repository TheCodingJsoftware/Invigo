import socket

from json_file import JsonFile

settings_file = JsonFile("settings")


def get_server_ip_address() -> str:
    return settings_file.get_value(item_name="server_ip")


def get_server_port() -> int:
    return settings_file.get_value(item_name="server_port")


def get_system_ip_address() -> str:
    return socket.gethostbyname(socket.gethostname())
