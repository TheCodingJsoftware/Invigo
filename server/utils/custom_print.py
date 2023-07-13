import os
from datetime import datetime

from utils.colors import Colors

messages = []
connected_clients = []
expected_clients: dict = {"10.0.0.75": "Jordan", "10.0.0.155": "Justin", "10.0.0.5": "Lynden"}


def convert_set_to_list(s):
    return list(map(lambda x: x, s))


class CustomPrint:
    @staticmethod
    def print(*args, **kwargs):
        """
        This is a customized print function that formats and colors the output text and also displays
        the IP addresses of connected clients if provided.
        """
        global messages, connected_clients
        try:
            connected_clients = convert_set_to_list(kwargs["connected_clients"])
            connected_clients = [connected_client.request.remote_ip for connected_client in connected_clients]
        except Exception:
            connected_clients = []
        text = " ".join(str(arg) for arg in args)
        formatted_text = f"{Colors.BOLD}{str(datetime.now())} - {text}{Colors.ENDC}"
        formatted_text = formatted_text.replace("INFO", f"{Colors.OKGREEN}INFO{Colors.BOLD}")  # Green
        formatted_text = formatted_text.replace("ERROR", f"{Colors.ERROR}ERROR{Colors.BOLD}")  # Red
        formatted_text = formatted_text.replace("WARN", f"{Colors.WARNING}WARN{Colors.BOLD}")  # Yellow
        # messages.append(formatted_text)
        # if len(messages) > 50:
        #     messages = messages[50:]
        print(formatted_text)
        # print_clients()


def print_clients():
    """
    This function prints a formatted list of connected and expected clients.

    Returns:
      The function `print_clients()` returns a string that contains information about the connected
    clients and their status. The string includes the number of connected clients, the name of each
    client, their expected status, and whether they are currently connected or disconnected. The string
    is formatted with color codes to highlight the status of each client.
    """
    # os.system("cls" if os.name == "nt" else "clear")
    # connected_clients.insert(0, f"{Colors.BOLD}Connected clients: ({len(connected_clients)}){Colors.ENDC}")
    all_clients = list(set(list(expected_clients.keys()) + connected_clients))
    all_clients.insert(0, f"{Colors.BOLD}Connected clients: ({len(connected_clients)}){Colors.ENDC}")
    string = ""
    for i, client in enumerate(all_clients):
        try:
            if client in all_clients:
                if client in connected_clients:
                    client = f"{Colors.OKGREEN}{client:<10s} {expected_clients[client]:<10s} Connected{Colors.BOLD}"
                else:
                    client = f"{Colors.ERROR}{client:<10s} {expected_clients[client]:<10s} Disconnected{Colors.BOLD}"
        except IndexError:
            client = "index error"
        except KeyError:
            if "Connected clients:" not in client:
                client = f"{Colors.WARNING}{client:<10s} {'UNKNOWN':<10s} Connected{Colors.BOLD}"
        # print(f"{client:>10s}")
        string += f"{client:>10s}\n"
    return string + "\n"
