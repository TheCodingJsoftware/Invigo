# import concurrent.futures
import json
import logging
import os
import shutil
import sys
import threading
import time
import zipfile
from datetime import datetime
from functools import partial
from io import StringIO
from pathlib import Path

import coloredlogs
import jinja2
import schedule
import tornado.ioloop
import tornado.web
import tornado.websocket
from ansi2html import Ansi2HTMLConverter
from filelock import FileLock, Timeout
from git import Repo
from markupsafe import Markup

from utils.custom_print import CustomPrint, print_clients
from utils.files import get_file_type
from utils.inventory_updater import (
    add_sheet,
    get_cutoff_sheets,
    get_sheet_pending_data,
    get_sheet_quantity,
    remove_cutoff_sheet,
    set_sheet_quantity,
    sheet_exists,
    update_inventory,
)
from utils.send_email import send_error_log
from utils.sheet_report import generate_sheet_report

# Store connected clients
connected_clients = set()

# Configure Jinja2 template environment
loader = jinja2.FileSystemLoader("templates")
env = jinja2.Environment(loader=loader)


with open("utils/inventory_file_to_use.txt", "r") as f:
    inventory_file_name: str = f.read()

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
    def get(self, filename):
        if filename == "price_of_steel_information.json":
            file_path = "price_of_steel_information.json"
        else:
            file_path = f"data/{filename}"
        lock = FileLock(f'{file_path}.lock', timeout=1)
        try:
            with lock:
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
        finally:
            lock.release()

        self.finish()


def update_inventory_file_to_pinecone(file_name: str):
    shutil.copy2(f'data\\{file_name}', f'Z:\\Invigo\\{file_name}')
    CustomPrint.print(
        f'INFO - Updated "{file_name}" to Pinecone',
        connected_clients=connected_clients,
    )

class FileUploadHandler(tornado.web.RequestHandler):
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
                if file_name == f'{inventory_file_name}.json' or file_name == f'{inventory_file_name} - Price of Steel.json' or file_name == f'{inventory_file_name} - Parts in Inventory.json': # This needs to be done because the website uses this file
                    threading.Thread(target=update_inventory_file_to_pinecone, args=(file_name,)).start()
            elif get_file_type(file_name) == "JPEG":
                # Save the received file to a local location
                with open(f"parts in inventory images/{file_name}", "wb") as file:
                    file.write(file_data)
            CustomPrint.print(
                f'INFO - Received "{file_name}" from {self.request.remote_ip}',
                connected_clients=connected_clients,
            )
            # Managing OmniGen's batch uploads
            if 'parts_batch_to_upload_workorder' in file_name or 'parts_batch_to_upload_part' in file_name:
                self.write("Batch sent successfully")
                update_inventory(f"data/{file_name}", connected_clients)
            elif file_name == "parts_batch_to_upload_quote.json":
                self.write("Batch sent successfully")
                file_path = f"data/{file_name}"
                os.rename(
                    file_path,
                    f'{file_path.replace(".json", "").replace("parts_batch_to_upload_quote", "").replace("data", "parts batch to upload history")}Quote {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json',
                )
            elif file_name == "parts_batch_to_upload_packing_slip.json":
                self.write("Batch sent successfully")
                file_path = f"data/{file_name}"
                os.rename(
                    file_path,
                    f'{file_path.replace(".json", "").replace("parts_batch_to_upload_packing_slip", "").replace("data", "parts batch to upload history")}Packing Slip {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json',
                )
            else:
                # This is other Invigo json files
                self.write("File uploaded successfully.")
            should_signal_connect_clients = True
            if should_signal_connect_clients and get_file_type(file_name) == "JSON":
                signal_clients_for_changes(client_to_ignore=self.request.remote_ip)
        else:
            self.write("No file received.")
            CustomPrint.print("ERROR - No file received.", connected_clients=connected_clients)


class WorkspaceFileUploader(tornado.web.RequestHandler):
    async def post(self):
        file_info = self.request.files.get("file")
        if file_info:
            file_data = file_info[0]["body"]
            file_name = os.path.basename(file_info[0]["filename"])
            file_ext = os.path.splitext(file_name)[1].upper().replace('.', '')
            Path(f'data/workspace/{file_ext}').mkdir(parents=True, exist_ok=True)
            with open(f'data/workspace/{file_ext}/{file_name}', "wb") as file:
                file.write(file_data)
            CustomPrint.print(
                f'INFO - Received "{file_name}" from {self.request.remote_ip}',
                connected_clients=connected_clients,
            )
            self.write("File uploaded successfully.")
        else:
            self.write("No file received.")
            CustomPrint.print("ERROR - No file received.", connected_clients=connected_clients)


class WorkspaceFileHandler(tornado.web.RequestHandler):
    def get(self, file_name):
        file_ext = os.path.splitext(file_name)[1].upper().replace('.', '')
        file_name = os.path.basename(file_name)
        filepath = os.path.join("data/workspace", file_ext, file_name)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                self.write(f.read())
            CustomPrint.print(
                f'INFO - Sent "{file_name}" to {self.request.remote_ip}',
                connected_clients=connected_clients,
            )
        else:
            self.set_status(404)


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
        command = self.get_argument("command")
        CustomPrint.print(
            f'INFO - Command "{command}" from {self.request.remote_ip}',
            connected_clients=connected_clients,
        )
        if command == "send_sheet_report":
            generate_sheet_report(connected_clients)
        self.finish()


class SetOrderNumberHandler(tornado.web.RequestHandler):
    def post(self):
        order_number = self.get_argument("order_number")
        if order_number is not None:
            with open("order_number.json", 'r') as file:
                json_file = json.load(file)
                json_file["order_number"] = int(order_number)

            with open("order_number.json", 'w') as file:
                json.dump(json_file, file)

            CustomPrint.print(
                f'INFO - {self.request.remote_ip} set order number to {order_number}',
                connected_clients=connected_clients,
            )
        else:
            self.set_status(400)


class GetOrderNumberHandler(tornado.web.RequestHandler):
    def get(self):
        with open("order_number.json", 'r') as file:
            order_number = json.load(file)["order_number"]

        self.write({"order_number": order_number})
        CustomPrint.print(
            f'INFO - Sent order number to {self.request.remote_ip}',
            connected_clients=connected_clients,
        )


class SheetQuantityHandler(tornado.web.RequestHandler):
    def get(self, sheet_name):
        sheet_name = sheet_name.replace('_', ' ')
        if sheet_exists(sheet_name=sheet_name):
            quantity = get_sheet_quantity(sheet_name=sheet_name)
            pending_data = get_sheet_pending_data(sheet_name=sheet_name)
            if self.request.remote_ip in ["10.0.0.11", "10.0.0.64", "10.0.0.217"]:
                template = env.get_template("sheet_template.html")
                rendered_template = template.render(sheet_name=sheet_name, quantity=quantity, pending_data=pending_data)
            else:
                template = env.get_template("sheet_template_read_only.html")
                rendered_template = template.render(sheet_name=sheet_name, quantity=quantity, pending_data=pending_data)

            self.write(rendered_template)
        else:
            self.write("Sheet not found")
            self.set_status(404)

    def post(self, sheet_name):
        try:
            new_quantity = float(self.get_argument("new_quantity"))
        except ValueError:
            self.write("Not a number")
            self.set_status(500)
            return

        set_sheet_quantity(sheet_name=sheet_name, new_quantity=new_quantity, clients=connected_clients)

        self.redirect(f"/sheets_in_inventory/{sheet_name}")


class AddCutoffSheetHandler(tornado.web.RequestHandler):
    def get(self):
        template = env.get_template("add_cutoff_sheet.html")
        rendered_template = template.render(thicknesses=["22 Gauge", "20 Gauge", "18 Gauge", "16 Gauge", "14 Gauge", "12 Gauge", "11 Gauge", "10 Gauge", "3/16", "1/4", "5/16", "3/8", "1/2", "5/8", "3/4", "1"], materials=["304 SS", "409 SS", "Mild Steel", "Galvanneal", "Galvanized", "Aluminium", "Laser Grade Plate"])
        self.write(rendered_template)

    def post(self):
        length: float = float(self.get_argument("length"))
        width: float = float(self.get_argument("width"))
        material: str = self.get_argument("material")
        thickness: str = self.get_argument("thickness")
        quantity: int = int(self.get_argument("quantity"))

        add_sheet(thickness=thickness, material=material, sheet_dim=f'{length:.3f}x{width:.3f}', sheet_count=quantity, _connected_clients=connected_clients)

        self.redirect("/add_cutoff_sheet")


class DeleteCutoffSheetHandler(tornado.web.RequestHandler):
    def post(self):
        sheet_id = self.get_argument("sheet_id")

        remove_cutoff_sheet(sheet_id, connected_clients)

        self.redirect("/add_cutoff_sheet")


class GetPreviousNestsFiles(tornado.web.RequestHandler):
    def get(self):
        directory = "parts batch to upload history"

        files = {}
        for filename in os.listdir(directory):
            if "Part" in filename:
                continue
            file_path = os.path.join(directory, filename)
            file_info = {
                "name": filename,
                "created_date": os.path.getctime(file_path)
            }
            files[filename] = file_info

        self.set_header("Content-Type", "application/json")
        self.set_status(200)
        self.write(json.dumps(files))


class GetPreviousNestsDataHandler(tornado.web.RequestHandler):
    def post(self):
        file_names = self.get_argument("file_names").split(';')
        combined_data = {}

        for file_name in file_names:
            with open(f'parts batch to upload history/{file_name}', "r") as file:
                file_data = json.load(file)
                combined_data.update(file_data)

        self.set_status(200)
        self.write(json.dumps(combined_data))


class SendErrorReport(tornado.web.RequestHandler):
    def post(self):
        error_log = self.get_argument("error_log")
        CustomPrint.print(
                f"ERROR - Received Error Log - {error_log}",
                connected_clients=connected_clients,
            )
        if error_log is not None:
            send_error_log(body=error_log, connected_clients=connected_clients)
            with open(f'{os.path.dirname(os.path.realpath(__file__))}/logs/U{datetime.now().strftime("%B %d %A %Y %I-%M-%S %p")}.log', 'w') as error_file:
                error_file.write(error_log)
        else:
            self.set_status(400)


class UploadSheetsSettingsHandler(tornado.web.RequestHandler):
    async def post(self):
        file_info = self.request.arguments.get("file")
        if file_info:
            file_data = file_info[1]
            file_name = file_info[0].decode()
            CustomPrint.print(
                f'INFO - Received "{file_name}" from {self.request.remote_ip}',
                connected_clients=connected_clients
            )
            with open(file_name, 'wb') as file:
                file.write(file_data)
            self.write("success")
            signal_clients_for_changes(client_to_ignore=self.request.remote_ip)


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
    logging.basicConfig(
        filename=f"{os.path.dirname(os.path.realpath(__file__))}/logs/server.log",
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.INFO,
    )


def backup_inventroy_files():
    logging.info("Backing up inventory files")
    files = os.listdir(f"{os.path.dirname(os.path.realpath(__file__))}/data")
    path_to_zip_file: str = (
        f"{os.path.dirname(os.path.realpath(__file__))}/backups/{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}.zip"
    )
    file = zipfile.ZipFile(path_to_zip_file, mode="w")
    for file_path in files:
        file.write(
            f"{os.path.dirname(os.path.realpath(__file__))}/data/{file_path}",
            file_path,
            compress_type=zipfile.ZIP_DEFLATED,
        )
    file.close()
    logging.info("Inventory file backed up")
    CustomPrint.print("INFO - Backup complete", connected_clients=connected_clients)

def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    coloredlogs.install(level="INFO")  # Enable colored logs
    sys.stdout = StringIO()
    CustomPrint.print(
        """

                           **//*
                 *&&&&&&&&&&&&&&&%%%%%%
             %&&&&&&&&&&&&&&&&&&%%%%    #%%%%%(                                   ████████████████████
          &&&&&&&&&&&&%%%(           *%%%%%%((/                                  ████████████████████
       *&&&&&&&&&&&&%%(            %%%%%%(((    (##/                            ██▀                ██
      &&&&&&&&&&&&&%%           %%%%%%#((     #######               ▄████████                     ██                                 ██
    &&&&&&&&& #&&&%&          %%%%%#((*       %########           ▄█▀      ▀███▄▄████▄▄▄         ██
   &&&&&&&&   %&&%%%       %%%%%%(((           (#####(((         █▀          ██████    ▀█▄      ▄█            ▄▄   ▄▄█▄    ▄▄▄▄▄    ██          ▄███▄        ▄▄▄▄▄▄
  &&&&&&&&    %%%%%%     %%%%%#((                ##((((((       ██          █▀   ████    █     ██  ▀█▄██  ▄██████    ███  ██████ ▄████      ▄███▀   ▀     ▄▄██▀▀▀
 %&&&&&&%     %%%%%%      ##((                    (((((((/      █          ▄█       ███  █    ██     ███▄██▀ ███     ███ █   ██   ███    ▄██▀   ▄       ▄█▀ ▄▄▄▄▄
 &&&&&&%      %%%%%%                    ###((((((((((((///      ██         ██        █████  ▄█▀      ████▀  ███     ███▀    ██   ███    ▄█     ██      ██  █▀  ███
*&&&&&&       %%%%%%                   /(##(((((((((//////       ██        ▀█          ██ ▄█▀       ███▀   ███      ██    ▄█▀   ███    ██     ███     ██      ▄██
(&&&&&&       %%%%%%                   /((((           ///        ██                    ▄██▀       ███    ███      ███  ▄██▀   ███    ██    ██ ██    ███     ▄██
 &&&&&%#      %%%%%#        %%%%#(     /((((         ***//         ▀██▄▄            ▄▄██▀         ███     ██       ████▀▀     ▄██     ██   ██ ███    ██    ▄▄█▀
 %%%&%%%       %%%#      /%%%%#((/     /((((      **//////           ▀▀██████████████▀           ███     ████     ▄█▀         ███▀    ▀████▀ ███     ▀██████▀
  %%%%%%%              %%%%##((        /////    *////////                                                                                    ██
  *%%%%%%%%         #%%%%#((/          *////   /////////                                                                                    ██
    %%%%%%%%#     %%%%#(((             ///// //////////                                                                                    ██
     %%%%%%%%%*%%%%##((*              ///////////////                                                                                    ▄██
       %%%%%%%%%##((/               ///////////////*                                                                             ▀█▄   ▄█▀
         #%####(((    #(          ///////////////                                                                                  ▀███▀
                 (####(((((((((//////////*
                           ****

"""
    )

    config_logs()
    backup_inventroy_files()
    generate_sheet_report(clients=connected_clients)
    schedule.every().monday.at("04:00").do(partial(generate_sheet_report, connected_clients))
    schedule.every().day.at("04:00").do(backup_inventroy_files)
    thread = threading.Thread(target=schedule_thread)
    thread.start()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/file/(.*)", FileReceiveHandler),
            (r"/command", CommandHandler),
            (r"/upload", FileUploadHandler),
            (r"/workspace_upload", WorkspaceFileUploader),
            (r"/workspace_get_file/(.*)", WorkspaceFileHandler),
            (r"/ws", FileSenderHandler),
            (r"/image/(.*)", ImageHandler),
            (r"/set_order_number", SetOrderNumberHandler),
            (r"/get_order_number", GetOrderNumberHandler),
            (r"/sheets_in_inventory/(.*)", SheetQuantityHandler),
            (r"/add_cutoff_sheet", AddCutoffSheetHandler),
            (r"/delete_cutoff_sheet", DeleteCutoffSheetHandler),
            (r"/get_previous_nests_files", GetPreviousNestsFiles),
            (r"/get_previous_nests_data", GetPreviousNestsDataHandler),
            (r"/send_error_report", SendErrorReport),
            (r"/upload_sheets_settings", UploadSheetsSettingsHandler),
        ]
    )
    # executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    # app.executor = executor
    # 10.0.0.9
    app.listen(8080)
    CustomPrint.print("INFO - Server started")
    tornado.ioloop.IOLoop.current().start()
