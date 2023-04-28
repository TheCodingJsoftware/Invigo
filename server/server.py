import contextlib
import logging
import os
import socket
import time
import zipfile
from datetime import datetime
from time import sleep

import ujson as json
from git import Repo

from utils.colors import Colors
from utils.inventory_updater import update_inventory
from utils.json_file import JsonFile
from utils.send_email import send

price_of_steel_inventory = JsonFile(file_name="data/inventory - Price of Steel")

class Server:
    """
    This script is seperate from the entire client-end project
    and is not intended for the client to use this script.
    """

    def __init__(self) -> None:
        """
        It checks if the folders "data" and "logs" exist, if not it creates them. Then it configures the
        logs and starts the server
        """
        # Declaring server IP and port
        self.SERVER_IP: str = "10.0.0.93"
        self.SERVER_PORT: int = 80

        self.BUFFER_SIZE = 8192
        self.SEPARATOR = "<SEPARATOR>"

        self.check_folders(folders=["data", "logs", "backups"])
        self.config_logs()
        self.__backup_inventroy_files()
        self.__check_low_sheet_quantities()
        self.start_server()

    def config_logs(self) -> None:
        """
        It configures the logs.
        """
        logging.basicConfig(
            filename=f"{os.path.dirname(os.path.realpath(__file__))}/logs/server.log",
            filemode="a",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.INFO,
        )

    def start_server(self) -> None:  # sourcery skip: low-code-quality
        """
        The server receives a file from the client, then sends a file to the client.

        Returns:
          The server returns a file to the client
        Question: What is being sent?
        Answer: The client sends a file to the server
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.SERVER_IP, self.SERVER_PORT))
            self.socket.listen(128)
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Server Started succesfully on {self.SERVER_IP}:{self.SERVER_PORT}{Colors.ENDC}"
            )
            logging.info("server started succesfully")
        except Exception as e:
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.ERROR}[X] Server could not start.\n\nReason:\n{e}{Colors.ENDC}"
            )
            logging.exception("Exception occured")
            return
        while True:
            try:

                print(
                    f"{Colors.BOLD}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-{Colors.ENDC}"
                )
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.HEADER}Listening for connections...{Colors.ENDC}"
                )
                client_socket, client_address = self.socket.accept()
                client_socket.settimeout(10)
                data = client_socket.recv(self.BUFFER_SIZE).decode()

                logging.info("got data")

                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[ ] Connection established with: {str(client_address)}{Colors.ENDC}"
                )
                logging.info(f"Connection established with: {str(client_address)}")
                sleep(0.5)  # ! IMPORTANT
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[ ] Starting process: {str(client_address)} Command: {data.split(self.SEPARATOR)[0]}{Colors.ENDC}"
                )
                logging.info(
                    f"Starting process: {str(client_address)} Command: {data.split(self.SEPARATOR)[0]}"
                )
                # The server returns a file to the client
                if "get_file" in data:
                    command, filename = data.split(self.SEPARATOR)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Sending file to {str(client_address)}\tFile: {filename}{Colors.ENDC}"
                    )
                    logging.info(f"Sending file to client\tFile: {filename}")
                    client_socket.sendall(f"{os.path.getsize(filename)}".encode())
                    sleep(0.5)  # ! IMPORTANT
                    # sel
                    with open(filename, "rb") as f:
                        while True:
                            if bytes_read := f.read(self.BUFFER_SIZE):
                                client_socket.sendall(bytes_read)
                            else:
                                # file transmitting is done
                                break
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] File successfuly sent!{Colors.ENDC}"
                    )
                    logging.info("File successfuly sent")

                # The client sends a file to the server
                if "send_file" in data:
                    command, filename, filesize = data.split(self.SEPARATOR)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Receiving file from client\tFile: {filename}{Colors.ENDC}"
                    )
                    logging.info(f"Receiving file from client\tFile: {filename}")
                    # filesize = int(filesize)

                    with open("data/temp.json", "wb") as f:
                        while True:
                            if bytes_read := client_socket.recv(self.BUFFER_SIZE):
                                f.write(bytes_read)
                            else:
                                # file transmitting is done
                                break
                    logging.info("sent response")
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] Succesfully received file{Colors.ENDC}"
                    )
                    logging.info("Succesfully received file")
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Saving file\tFile: {filename}{Colors.ENDC}"
                    )
                    try:
                        with open(
                            "data/temp.json",
                            "r",
                        ) as f:
                            data = json.load(f)
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        print(
                            f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] File saved\tFile: {filename}{Colors.ENDC}"
                        )
                        self.__upload_inventory(filename)
                    except Exception as e:
                        print(
                            f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.ERROR}[X] ERROR loading file, improper JSON format, aborting. {e}{Colors.ENDC}"
                        )
                        logging.info(
                            f"Error loading file, improper JSON format, aborting. {e}"
                        )

                # Laser PC sends file to server
                if "laser_parts_list_upload" in data:
                    command, filename, filesize = data.split(self.SEPARATOR)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Receiving file from client\tFile: {filename}{Colors.ENDC}"
                    )
                    logging.info(f"Receiving file from client\tFile: {filename}")
                    # filesize = int(filesize)

                    with open("data/temp.json", "wb") as f:
                        while (
                            bytes_read := client_socket.recv(self.BUFFER_SIZE)
                        ) and bytes_read.decode("utf-8") != "FINSIHED!":
                            f.write(bytes_read)
                    # receive acknowledgment from the server
                    # _ = client_socket.recv(1024)
                    logging.info("sent response")
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] Succesfully received file{Colors.ENDC}"
                    )
                    logging.info("Succesfully received file")
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Saving file\tFile: {filename}{Colors.ENDC}"
                    )
                    try:
                        with open(
                            "data/temp.json",
                            "r",
                        ) as f:
                            data = json.load(f)
                        with open(
                            "data/laser_parts_new_batch.json", "w", encoding="utf-8"
                        ) as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        print(
                            f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] File saved\tFile: {filename}{Colors.ENDC}"
                        )
                        client_socket.sendall("Batch sent successfully".encode("utf-8"))
                    except Exception as e:
                        print(
                            f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.ERROR}[X] ERROR loading file, improper JSON format, aborting. {e}{Colors.ENDC}"
                        )
                        logging.info(
                            f"Error loading file, improper JSON format, aborting. {e}"
                        )
                        client_socket.sendall(f"{e}".encode("utf-8"))
                    update_inventory("data/laser_parts_new_batch.json")

                if "get_modified_date" in data:
                    command, filename = data.split(self.SEPARATOR)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Sending modified date of {filename}{Colors.ENDC}"
                    )
                    logging.info(f"Sending modified date of {filename}")

                    client_socket.sendall(
                        f'{time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(os.path.getmtime(filename)))}'.encode()
                    )
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] Succesfully send modified date. {Colors.ENDC}"
                    )
                    logging.info("Succesfully send modified date")
                if "send_sheet_report" in data:
                    self.generate_sheet_report()
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[+] Process finished!{Colors.ENDC}"
                )
                client_socket.shutdown(socket.SHUT_RD)
                client_socket.close()
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[+] Connection closed succesfully with: {str(client_address)}{Colors.ENDC}"
                )
                logging.info(f"Connection closed succesfully with: {str(client_address)}")

            except Exception as e:
                logging.exception(e)
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.ERROR}[X] ERROR: {e} {Colors.ENDC}"
                )

    def check_folders(self, folders: list) -> None:
        """
        It checks if a folder exists, if it doesn't, it creates it

        Args:
          folders (list): list = ["logs", "data", "config"]
        """
        for folder in folders:
            if not os.path.exists(
                f"{os.path.dirname(os.path.realpath(__file__))}/{folder}"
            ):
                os.makedirs(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}")
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}{os.path.dirname(os.path.realpath(__file__))}/{folder} Created.{Colors.ENDC}"
                )

    def __check_low_sheet_quantities(self) -> None:
        """
        This function checks if the current day is Monday and generates a sheet report if it is.

        Returns:
          If the current day of the week is not Monday, the function will return nothing (None). If it
        is Monday, the function will call the method `generate_sheet_report()` and return nothing
        (None).
        """
        if datetime.now().strftime('%A') != 'Monday':
            return
        self.generate_sheet_report()

    def generate_sheet_report(self) -> None:
        """
        This function generates a report of sheets low in quantity and sends it as an email.
        """
        print(f'{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[ ] Sending sheet quantity report as an email{Colors.ENDC}')
        sheets_low_in_quantity: int = 0
        message_to_send: str = '<div class="tg-wrap"><table style="table-layout: fixed; width: 633px; border-collapse: collapse; border: 1px solid; text-align: center; vertical-align: middle;"><colgroup><col style="width: 187px"><col style="width: 146px"><col style="width: 146px"><col style="width: 340px"></colgroup><thead><tr><th>Sheet Name</th><th>Order Status</th><th>Current Quantity</th><th>Description</th></tr></thead><tbody>'
        data = price_of_steel_inventory.get_data()

        for material in list(data.keys()):
            if material == 'Price Per Pound':
                continue
            for sheet_name in list(data[material].keys()):
                try:
                    red_limit: int = data[material][sheet_name]['red_limit']
                    yellow_limit: int = data[material][sheet_name]['yellow_limit']
                except Exception:
                    # Default values
                    red_limit: int = 4
                    yellow_limit: int = 10
                current_quantity: int = data[material][sheet_name]['current_quantity']
                if (
                    current_quantity <= red_limit
                    or current_quantity <= yellow_limit
                ):
                    sheets_low_in_quantity += 1
                    notes: str = 'Nothing here'
                    with contextlib.suppress(Exception):
                        notes: str = data[material][sheet_name]['notes']
                    is_order_pending: bool = False
                    with contextlib.suppress(KeyError):
                        is_order_pending = data[material][sheet_name]['is_order_pending']
                    stylesheet = (
                        'color: red; border-color: darkred; background-color: #3F1E25;'
                        if current_quantity <= red_limit
                        else 'color: yellow; border-color: gold; background-color: #413C28;'
                    )
                    order_pending: str = "No order pending"
                    if is_order_pending:
                        order_pending = "Order is pending"
                        stylesheet = 'color: lime; border-color: green; background-color: darkgreen;'
                    else:
                        order_pending = "No order is pending"
                    message_to_send += f'<tr style="border: 1px solid; {stylesheet}"><td>{sheet_name}</td><td style="{"font-weight: bold;" if is_order_pending else ""}">{order_pending}</td><td>{current_quantity}</td><td>{notes}</td></tr>'
        message_to_send += '</tbody></table></div><br>Don\'t forget to update the pending status button in the Sheet Inventory tab when you sent a purchase order.<br>Have a fabulous week!'
        if sheets_low_in_quantity == 0:
            send('Nothing low in quantity, Whew! Have a marvelous Monday.')
        else:
            send(message_to_send)

    def __backup_inventroy_files(self):
        """
        It backs up the inventory file to a backup file
        """
        print(
            f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[ ] Backing up inventory file{Colors.ENDC}"
        )
        logging.info("Backing up inventory files")
        files = os.listdir(f"{os.path.dirname(os.path.realpath(__file__))}/data")
        for file_path in files:
            path_to_zip_file: str = f"{os.path.dirname(os.path.realpath(__file__))}/backups/{file_path} - {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}.zip"
            file = zipfile.ZipFile(path_to_zip_file, mode="w")
            file.write(
                f"{os.path.dirname(os.path.realpath(__file__))}/data/{file_path}",
                file_path,
                compress_type=zipfile.ZIP_DEFLATED,
            )
            file.close()
        print(
            f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[+] Inventory file backed up{Colors.ENDC}"
        )
        logging.info("Inventory file backed up")

    def __upload_inventory(self, file_name: str) -> None:
        """
        It adds the file to the git index, commits it, and pushes it to the remote origin
        """
        print(
            f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[ ] Updating {file_name} to github{Colors.ENDC}"
        )
        try:
            with open(
                f"C:/Users/joe/Documents/Inventory-Manager/server/{file_name}", "r"
            ) as f:
                data = json.load(f)
        except Exception as e:
            print(
                f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.ERROR}[X] Error loading file, improper JSON format, aborting. {e}{Colors.ENDC}"
            )
            logging.info(f"Error loading file, improper JSON format, aborting. {e}")
            return
        repo = Repo(
            "C:/Users/joe/Documents/Inventory-Manager"
        )  # if repo is CWD just do '.'
        repo.index.add([f"server/{file_name}"])
        repo.index.commit(file_name)
        origin = repo.remote("origin")
        origin.push()
        print(
            f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t\t{Colors.OKGREEN}[+] Updated {file_name} to github.{Colors.ENDC}"
        )


if __name__ == "__main__":
    Server()
