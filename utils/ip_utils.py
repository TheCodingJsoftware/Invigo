import socket

from utils.settings import Settings

settings_file = Settings()
server_settings = settings_file.get_value("server")

def get_server_protocol() -> str:
    return server_settings.get("protocol")


def get_server_ip_address() -> str:
    return server_settings.get("ip")


def get_server_port() -> int:
    return server_settings.get("port")


def get_system_ip_address() -> str:
    return socket.gethostbyname(socket.gethostname())
