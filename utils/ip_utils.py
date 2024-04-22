import socket

from utils.json_file import JsonFile

settings_file = JsonFile("settings")


def get_server_ip_address() -> str:
    return settings_file.get_value(item_name="server_ip")


def get_server_port() -> int:
    return settings_file.get_value(item_name="server_port")


def get_system_ip_address() -> str:
    return socket.gethostbyname(socket.gethostname())


def get_buffer_size() -> int:
    return settings_file.get_value(item_name="server_buffer_size")


def get_server_timeout() -> int:
    return settings_file.get_value(item_name="server_time_out")
