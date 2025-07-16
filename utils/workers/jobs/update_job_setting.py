import requests

from utils.workers.base_worker import BaseWorker


class UpdateJobSettingWorker(BaseWorker):
    def __init__(self, job_id: int, key: str, value: str | float | int | bool):
        super().__init__(name="UpdateJobSettingWorker")
        self.job_id = job_id
        self.key = key
        self.value = value
        self.url = f"{self.DOMAIN}/jobs/update_job_setting/{job_id}"

    def do_work(self):
        try:
            data = {
                "key": self.key,
                "value": self.value,
            }
            with requests.Session() as session:
                response = session.post(
                    self.url,
                    data=data,
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                return self.job_id
        except Exception as e:
            self.signals.error.emit(str(e), self.job_id)
