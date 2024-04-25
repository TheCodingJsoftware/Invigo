import socket

from utils.settings import Settings

settings_file = Settings()


def get_server_ip_address() -> str:
    return settings_file.get_value("server_ip")


def get_server_port() -> int:
    return settings_file.get_value("server_port")


def get_system_ip_address() -> str:
    return socket.gethostbyname(socket.gethostname())


def get_buffer_size() -> int:
    return settings_file.get_value("server_buffer_size")


def get_server_timeout() -> int:
    return settings_file.get_value("server_time_out")
