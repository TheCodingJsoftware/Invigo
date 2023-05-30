import logging
import os
import sys
import zipfile
from datetime import datetime
from io import StringIO

import coloredlogs
import tornado.ioloop
import tornado.web
import tornado.websocket
from ansi2html import Ansi2HTMLConverter
from markupsafe import Markup

from utils.custom_print import CustomPrint, print_clients
from utils.files import get_file_type
from utils.inventory_updater import update_inventory
from utils.sheet_report import generate_sheet_report

# Store connected clients
connected_clients = set()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        logs = print_clients() + sys.stdout.getvalue()
        converter = Ansi2HTMLConverter()
        logs = converter.convert(logs)
        logs = Markup(logs)  # Mark the logs as safe HTML
        self.write(logs)


class FileSenderHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        connected_clients.add(self)

        CustomPrint.print(
            f"INFO - Connection established with: {self.request.remote_ip} - Connected clients: {len(connected_clients)}",
            connected_clients=connected_clients,
        )

    def on_close(self):
        connected_clients.remove(self)
        CustomPrint.print(
            f"INFO - Connection ended with: {self.request.remote_ip} - Connected clients: {len(connected_clients)}",
            connected_clients=connected_clients,
        )


class FileReceiveHandler(tornado.web.RequestHandler):
    # this downloads file per request of the client
    def get(self, filename):
        # Check if the requested file exists
        file_path = f"data/{filename}"
        try:
            with open(file_path, "rb") as file:
                data = file.read()

            # Set the response headers
            self.set_header("Content-Type", "application/json")
            self.set_header("Content-Disposition", f'attachment; filename="{filename}"')

            # Send the file as the response
            self.write(data)
            CustomPrint.print(
                f'INFO - Sent "{filename}" to {self.request.remote_ip}',
                connected_clients=connected_clients,
            )
        except FileNotFoundError:
            self.set_status(404)
            self.write(f'File "{filename}" not found.')
            CustomPrint.print(
                f'ERROR - File "{filename}" not found.',
                connected_clients=connected_clients,
            )

        self.finish()


class FileUploadHandler(tornado.web.RequestHandler):
    # this saves a file that the client uploads
    async def post(self):
        file_info = self.request.files.get("file")
        should_signal_connect_clients: bool = False
        if file_info:
            file_data = file_info[0]["body"]
            file_name = file_info[0]["filename"]

            if get_file_type(file_name) == "JSON":
                # Save the received file to a local location
                with open(f"data/{file_name}", "wb") as file:
                    file.write(file_data)
            elif get_file_type(file_name) == "JPEG":
                # Save the received file to a local location
                with open(f"parts in inventory images/{file_name}", "wb") as file:
                    file.write(file_data)
            CustomPrint.print(
                f'INFO - Received "{file_name}" from {self.request.remote_ip}',
                connected_clients=connected_clients,
            )

            if file_name == "parts_batch_to_upload.json":
                self.write("Batch sent successfully")
                update_inventory(f"data/{file_name}", connected_clients)
                should_signal_connect_clients = True
            else:
                self.write("File uploaded successfully.")
                should_signal_connect_clients = True
            if should_signal_connect_clients and get_file_type(file_name) == "JSON":
                signal_clients_for_changes(client_to_ignore=self.request.remote_ip)
        else:
            self.write("No file received.")
            CustomPrint.print(
                f"ERROR - No file received.", connected_clients=connected_clients
            )


class ImageHandler(tornado.web.RequestHandler):
    def get(self, image_name):
        filepath = os.path.join("parts in inventory images", image_name)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                self.set_header("Content-Type", "image/jpeg")
                self.write(f.read())
            CustomPrint.print(
                f'INFO - Sent "{image_name}" to {self.request.remote_ip}',
                connected_clients=connected_clients,
            )
        else:
            self.set_status(404)


class CommandHandler(tornado.web.RequestHandler):
    def post(self):
        # Receive the command from the client
        command = self.get_argument("command")
        CustomPrint.print(
            f'INFO - Command "{command}" from {self.request.remote_ip}',
            connected_clients=connected_clients,
        )
        if command == "send_sheet_report":
            # await self.run_in_executor(self.generate_sheet_report)
            generate_sheet_report(connected_clients)
        # Send the response back to the client
        # self.write('done')
        self.finish()


def signal_clients_for_changes(client_to_ignore) -> None:
    CustomPrint.print(
        f"INFO - Signaling {len(connected_clients)} clients",
        connected_clients=connected_clients,
    )
    for client in connected_clients:
        if client.request.remote_ip == client_to_ignore:
            CustomPrint.print(
                f"INFO - Ignoring {client.request.remote_ip}",
                connected_clients=connected_clients,
            )
            continue
        if client.ws_connection and client.ws_connection.stream.socket:
            client.write_message("download changes")
            CustomPrint.print(
                f"INFO - Signaling {client.request.remote_ip} to download changes",
                connected_clients=connected_clients,
            )


def config_logs() -> None:
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


def backup_inventroy_files():
    """
    It backs up the inventory file to a backup file
    """
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
    logging.info("Inventory file backed up")
    CustomPrint.print(f"INFO - Backup complete", connected_clients=connected_clients)



if __name__ == "__main__":
    coloredlogs.install(level="INFO")  # Enable colored logs
    sys.stdout = StringIO()
    CustomPrint.print("""

                                      **//*                                     
                            *&&&&&&&&&&&&&&&%%%%%%           
                        %&&&&&&&&&&&&&&&&&&%%%%    #%%%%%(                                     ████████████████████                                                                 
                     &&&&&&&&&&&&%%%(           *%%%%%%((/                                    ████████████████████                                                                  
                  *&&&&&&&&&&&&%%(            %%%%%%(((    (##/                              ██▀                ██                                                                  
                 &&&&&&&&&&&&&%%           %%%%%%#((     #######                 ▄████████                     ██                                 ██                               
               &&&&&&&&& #&&&%&          %%%%%#((*       %########             ▄█▀      ▀███▄▄████▄▄▄         ██                                                                    
              &&&&&&&&   %&&%%%       %%%%%%(((           (#####(((           █▀          ██████    ▀█▄      ▄█            ▄▄   ▄▄█▄    ▄▄▄▄▄    ██          ▄███▄        ▄▄▄▄▄     
             &&&&&&&&    %%%%%%     %%%%%#((                ##((((((         ██          █▀   ████    █     ██  ▀█▄██  ▄██████    ███  ██████ ▄████      ▄███▀   ▀     ▄▄█████▀▀      
            %&&&&&&%     %%%%%%      ##((                    (((((((/        █          ▄█       ███  █    ██     ███▄██▀ ███     ███ █   ██   ███     ██▀   ▄       ▄█▀ ▄▄▄▄▄     
            &&&&&&%      %%%%%%                    ###((((((((((((///        ██         ██        █████  ▄█▀      ████▀  ███     ███▀    ██   ███     █     ██      ██  █   ███     
           *&&&&&&       %%%%%%                   /(##(((((((((//////         ██        ▀█          ██ ▄█▀       ███▀   ███      ██    ▄█▀   ███    ██     ███     ██      ▄██      
           (&&&&&&       %%%%%%                   /((((           ///          ██                    ▄██▀       ███    ███      ███  ▄██▀   ███    ██    ██ ██    ███     ▄██       
            &&&&&%#      %%%%%#        %%%%#(     /((((         ***//           ▀██▄▄            ▄▄██▀         ███     ██       ████▀▀     ▄██    ███   ██ ███    ██    ▄▄█▀        
            %%%&%%%       %%%#      /%%%%#((/     /((((      **//////             ▀▀██████████████▀           ███     ████     ▄█▀         ███▀   ▀█████▀ ███     ▀██████▀           
             %%%%%%%              %%%%##((        /////    *////////                                                                                      ██                        
             *%%%%%%%%         #%%%%#((/          *////   /////////                                                                                      ██                         
               %%%%%%%%#     %%%%#(((             ///// //////////                                                                                      ██                          
                %%%%%%%%%*%%%%##((*              ///////////////                                                                                      ▄██                           
                  %%%%%%%%%##((/               ///////////////*                                                                               ▀█▄   ▄█▀                             
                    #%####(((    #(          ///////////////                                                                                    ▀███▀                                                      
                            (####(((((((((//////////*                           
                                      ****                                      
                                                    
""")

    config_logs()
    # backup_inventroy_files()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/file/(.*)", FileReceiveHandler),
            (r"/command", CommandHandler),
            (r"/upload", FileUploadHandler),
            (r"/ws", FileSenderHandler),
            (r"/image/(.*)", ImageHandler),
        ]
    )
    app.listen(80)
    CustomPrint.print(f"INFO - Server started")
    tornado.ioloop.IOLoop.current().start()
