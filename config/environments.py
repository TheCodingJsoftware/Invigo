import os

from dotenv import load_dotenv

load_dotenv()


class Environment:
    def __init__(self):
        raise RuntimeError("Environment is a static class and cannot be instantiated.")

    DATA_PATH = os.getcwd()
    APP_ENV = os.environ.get("APP_ENV", "production")
    SOFTWARE_API_BASE = os.environ.get("SOFTWARE_API_BASE", "http://invi.go/api/software")