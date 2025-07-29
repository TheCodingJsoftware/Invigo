import mimetypes
import os
import time

import requests

from utils.workers.base_worker import BaseWorker


class UploadFilesWorker(BaseWorker):
    def __init__(self, files_to_upload: list[str], max_retries: int = 3, delay_between_requests: float = 0.1):
        super().__init__(name="UploadFilesWorker")
        self.files_to_upload = files_to_upload
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.upload_url = f"{self.DOMAIN}/upload"

    def _prepare_file(self, filepath: str):
        ext = os.path.splitext(filepath)[1].lower()
        subfolder = "data" if ext == ".json" else "images" if ext in [".jpeg", ".jpg", ".png"] else None
        if subfolder and subfolder not in filepath:
            filepath = os.path.join(subfolder, filepath)

        mimetype = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
        with open(filepath, "rb") as f:
            content = f.read()

        return filepath, {"file": (os.path.basename(filepath), content, mimetype)}

    def do_work(self):
        successful, failed = [], []

        with requests.Session() as session:
            for original_path in self.files_to_upload:
                try:
                    full_path, file_payload = self._prepare_file(original_path)
                except Exception as e:
                    failed.append(original_path)
                    self.signals.error.emit(f"Failed to open file: {original_path} | {e}", 400)
                    continue

                for attempt in range(self.max_retries):
                    try:
                        resp = session.post(
                            self.upload_url,
                            files=file_payload,
                            headers=self.headers,
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            successful.append(original_path)
                            break
                        elif attempt == self.max_retries - 1:
                            failed.append(original_path)
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            failed.append(original_path)
                            self.signals.error.emit(f"{e} - {original_path}", 500)
                    time.sleep(self.delay_between_requests)

        return {
            "status": "success" if not failed else "partial" if successful else "failed",
            "successful": successful,
            "failed": failed,
        }
