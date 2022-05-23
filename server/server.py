import logging
import os
import socket
from datetime import datetime
from time import sleep

from utils.colors import Colors


class Server:
    """
    This script is seperate from the entire client-end project
    and is not intended for the client to use this script.
    """

    def __init__(self):
        # Declaring server IP and port
        self.SERVER_IP: str = "10.0.0.64"
        self.SERVER_PORT: int = 4000

        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"

        self.check_folders(folders=["data", "logs"])
        self.config_logs()
        self.start_server()

    def config_logs(self):
        logging.basicConfig(
            filename=f"{os.path.dirname(os.path.realpath(__file__))}/logs/server.log",
            filemode="a",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.INFO,
        )

    def start_server(self):  # sourcery skip: low-code-quality
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((self.SERVER_IP, self.SERVER_PORT))
            self.s.listen(5)
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
            # Wait for message from client
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.HEADER}[ ] Listening for connections...{Colors.ENDC}"
            )
            client_socket, client_address = self.s.accept()
            data = client_socket.recv(self.BUFFER_SIZE).decode()

            logging.info("got data")
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[+] Connection established with: {str(client_address)} data: {data}{Colors.ENDC}"
            )
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[ ] Starting process: {str(client_address)} Command: {data.split(self.SEPARATOR)[0]}{Colors.ENDC}"
            )

            # The server returns a file to the client
            if "get_file" in data:
                command, filename = data.split(self.SEPARATOR)
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[ ] Sending file to client\tFile: {filename}{Colors.ENDC}"
                )
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

            # The client sends a file to the server
            if "send_file" in data:
                command, filename, filesize = data.split(self.SEPARATOR)
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[ ] Receiving file from client\tFile: {filename}{Colors.ENDC}"
                )
                filesize = int(filesize)
                with open(filename, "wb") as f:
                    while True:
                        # read 1024 bytes from the socket (receive)
                        bytes_read = client_socket.recv(self.BUFFER_SIZE)
                        if not bytes_read:
                            # file transmitting is done
                            break
                        f.write(bytes_read)
                # client_socket.send("Successfully uploaded".encode("utf-8"))
                logging.info("sent response")
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC}\t{Colors.OKGREEN}[+] Succesfully received file{Colors.ENDC}"
                )
            client_socket.close()
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}[+] Connection closed succesfully with: {str(client_address)}{Colors.ENDC}"
            )

    def check_folders(self, folders: list) -> None:
        for folder in folders:
            if not os.path.exists(
                f"{os.path.dirname(os.path.realpath(__file__))}/{folder}"
            ):
                os.makedirs(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}")
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}{os.path.dirname(os.path.realpath(__file__))}/{folder} Created.{Colors.ENDC}"
                )


if __name__ == "__main__":
    Server()
