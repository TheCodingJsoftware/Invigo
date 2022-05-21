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
        )

    def start_server(self):
        try:
            # Starting server
            self.s = socket.socket()
            # self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.SERVER_IP, self.SERVER_PORT))
            self.s.listen(5)
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Server Started succesfully on {self.SERVER_IP}:{self.SERVER_PORT}{Colors.ENDC}"
            )
            logging.info("server started succesfully")
        except Exception as e:
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.ERROR}Server could not start.\n\nReason:\n{e}{Colors.ENDC}"
            )
            logging.exception("Exception occured")
            return
        # while True:
        # Wait for message from client
        client_socket, client_address = self.s.accept()
        data = client_socket.recv(self.BUFFER_SIZE).decode()
        command, filename, filesize = data.split(self.SEPARATOR)
        filesize = int(filesize)

        logging.info("got data")
        print(
            f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Message received from: {str(client_address)} Message: {data}{Colors.ENDC}"
        )

        print(command, filename, filesize)

        if command == "get_file":
            self.send_database(file_to_send=file, client=client_address)
        if command == "send_file":
            with open(filename, "wb") as f:
                print("opening file")
                while True:
                    # read 1024 bytes from the socket (receive)
                    bytes_read = client_socket.recv(self.BUFFER_SIZE)
                    print(bytes_read)
                    if not bytes_read:
                        # file transmitting is done
                        break
                    f.write(bytes_read)
            print("finished")
            self.s.sendto("Successfully uploaded".encode("utf-8"), client_address)
            client_socket.close()
            logging.info("sent response")
        print(
            f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Response sent to: {str(client_address)}{Colors.ENDC}"
        )
        # sleep(5)

    def check_folders(self, folders: list) -> None:
        for folder in folders:
            if not os.path.exists(
                f"{os.path.dirname(os.path.realpath(__file__))}/{folder}"
            ):
                os.makedirs(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}")
                print(
                    f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}{os.path.dirname(os.path.realpath(__file__))}/{folder} Created.{Colors.ENDC}"
                )

    def send_database(self, file_to_send: str, client):
        with open(f"{file_to_send}", "r") as database:
            text = database.read()
            self.s.sendto(text.encode("utf-8"), client)
            logging.info("sent data")


if __name__ == "__main__":
    Server()
