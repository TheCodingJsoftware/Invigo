import msgspec
import requests

from utils.workers.base_worker import BaseWorker
from utils.workspace.workorder import Workorder


class UploadWorkorderWorker(BaseWorker):
    def __init__(self, folder: str, workorder: Workorder, html_file_contents: str):
        super().__init__(name="UploadWorkorderWorker")
        self.folder = folder
        self.workorder = workorder
        self.html_file_contents = html_file_contents
        self.upload_url = f"{self.DOMAIN}/upload_workorder"

    def do_work(self):
        data = {
            "folder": self.folder,
            "html_file_contents": self.html_file_contents,
        }
        files = {
            "workorder_data": (
                "workorder.json",
                msgspec.json.encode(self.workorder.to_dict()),
                "application/json",
            )
        }

        try:
            response = requests.post(
                self.upload_url,
                data=data,
                files=files,
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                return "Workorder sent successfully"
            self.signals.error.emit(f"Upload failed: {response.status_code}", response.status_code)
        except Exception as e:
            self.signals.error.emit(str(e), 500)
