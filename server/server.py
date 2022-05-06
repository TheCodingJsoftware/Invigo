import socket


class Server:
    def __init__(self):
        # Declaring server IP and port
        self.SERVER_IP: str = "10.0.0.162"
        self.SERVER_PORT: int = 4000

        self.start_server()

    def start_server(self):
        try:
            # Starting server
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEclient_address, 1)
            self.s.bind((self.SERVER_IP, self.servSERVER_PORTer_port))
            print(f"Server Started succesfully on {self.SERVER_IP}:{self.SERVER_PORT}")
        except Exception as e:
            print(f"Server could not start.\n\nReason:\n{e}")
            return
        while True:
            # Wait for message from client
            data, client_address = self.s.recvfrom(1024)
            data = data.decode("utf-8")
            print(f"Message received from: {str(client_address)}")
            # TODO Handle data from the client
            print(data)
            self.s.sendto("Success".encode("utf-8"), client_address)


if __name__ == "__main__":
    Server()
