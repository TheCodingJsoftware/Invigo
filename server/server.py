import logging
import os
import socket
import zipfile
from datetime import datetime
from time import sleep

import ujson as json
from git import Repo

from utils.colors import Colors


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
        self.SERVER_IP: str = "10.0.0.64"
        self.SERVER_PORT: int = 4000

        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"

        self.check_folders(folders=["data", "logs", "backups"])
        self.config_logs()
        self.__backup_inventroy_files()
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
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((self.SERVER_IP, self.SERVER_PORT))
            self.s.listen(128)
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[+] Server Started succesfully on {self.SERVER_IP}:{self.SERVER_PORT}{Colors.ENDC}"
            )
            logging.info("server started succesfully")
        except Exception as e:
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.ERROR}[+] Server could not start.\n\nReason:\n{e}{Colors.ENDC}"
            )
            logging.exception("Exception occured")
            return
        while True:
            try:
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.HEADER}[ ] Listening for connections...{Colors.ENDC}"
                )
                client_socket, client_address = self.s.accept()
                client_socket.settimeout(10)
                data = client_socket.recv(self.BUFFER_SIZE).decode()

                logging.info("got data")

                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[+] Connection established with: {str(client_address)} data: {data}{Colors.ENDC}"
                )
                logging.info(
                    f"Connection established with: {str(client_address)} data: {data}"
                )
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[ ] Starting process: {str(client_address)} Command: {data.split(self.SEPARATOR)[0]}{Colors.ENDC}"
                )
                logging.info(
                    f"Starting process: {str(client_address)} Command: {data.split(self.SEPARATOR)[0]}"
                )

                # The server returns a file to the client
                if "get_file" in data:
                    command, filename = data.split(self.SEPARATOR)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[ ] Sending file to client\tFile: {filename}{Colors.ENDC}"
                    )
                    logging.info(f"Sending file to client\tFile: {filename}")
                    client_socket.send(f"{os.path.getsize(filename)}".encode())
                    # sel
                    with open(filename, "rb") as f:
                        while True:
                            bytes_read = f.read(self.BUFFER_SIZE)
                            if not bytes_read:
                                # file transmitting is done
                                break
                            client_socket.sendall(bytes_read)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[+] File successfuly sent{Colors.ENDC}"
                    )
                    logging.info("File successfuly sent")

                # The client sends a file to the server
                if "send_file" in data:
                    command, filename, filesize = data.split(self.SEPARATOR)
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[ ] Receiving file from client\tFile: {filename}{Colors.ENDC}"
                    )
                    logging.info(f"Receiving file from client\tFile: {filename}")
                    # filesize = int(filesize)
                    with open(filename, "wb") as f:
                        while True:

                            # read 1024 bytes from the socket (receive)
                            bytes_read = client_socket.recv(self.BUFFER_SIZE)
                            print(f"In Loop writing file {bytes_read} {len(bytes_read)}")
                            if not bytes_read:
                                # file transmitting is done
                                break
                            f.write(bytes_read)
                    logging.info("sent response")
                    print(
                        f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[+] Succesfully received file{Colors.ENDC}"
                    )
                    logging.info("Succesfully received file")
                    self.__upload_inventory(filename)
                client_socket.close()
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.HEADER}[+] Connection closed succesfully with: {str(client_address)}{Colors.ENDC}"
                )
                logging.info(f"Connection closed succesfully with: {str(client_address)}")
            except Exception as e:
                logging.exception(e)
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.ERROR}[X] ERROR: {e} {Colors.ENDC}"
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
        try:
            with open(
                f"C:/Users/user/Desktop/Inventory-Manager/server/{file_name}", "r"
            ) as f:
                data = json.load(f)
        except Exception as e:
            print(
                f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.ERROR}Error loading file, improper JSON format, aborting. {e}{Colors.ENDC}"
            )
            logging.info("Error loading file, improper JSON format, aborting. {e}")
            return
        repo = Repo(
            "C:/Users/user/Desktop/Inventory-Manager"
        )  # if repo is CWD just do '.'
        repo.index.add([f"server/{file_name}"])
        repo.index.commit(file_name)
        origin = repo.remote("origin")
        origin.push()
        print(
            f"{Colors.ENDC}{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Updated {file_name}{Colors.ENDC}"
        )


if __name__ == "__main__":
    Server()
