import logging
import os
import socket
from datetime import datetime

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
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.SERVER_IP, self.SERVER_PORT))
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
        while True:
            # Wait for message from client
            data, client_address = self.s.recvfrom(1024)
            data = data.decode("utf-8")
            logging.info("got data")
            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Message received from: {str(client_address)} Message: {data}{Colors.ENDC}"
            )

            if "sent" in data:
                text = data.split("|")[-1]
                with open("data/database.json", "w") as database:
                    database.write(text)
                    logging.info("downloaded data")
                self.s.sendto("Successfully uploaded".encode("utf-8"), client_address)
                logging.info("sent response")
            elif data == "download":
                self.send_database(client=client_address)

            print(
                f"{Colors.BOLD}{datetime.now()}{Colors.ENDC} - {Colors.OKGREEN}Response sent to: {str(client_address)}{Colors.ENDC}"
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

    def send_database(self, client):
        with open("data/database.json", "r") as database:
            text = database.read()
            self.s.sendto(text.encode("utf-8"), client)
            logging.info("sent data")


if __name__ == "__main__":
    Server()
