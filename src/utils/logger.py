from datetime import date, datetime
from pathlib import Path
from utils import *


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self._log_file = None

    @property
    def log_file_path(self) -> Path:
        return self.log_dir / f"log-{date.today().strftime('%d-%m-%Y')}.txt"

    def __enter__(self):
        if not self._log_file:
            self._log_file = open(self.log_file_path, "a")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def log(self, log_type: str, message: str) -> None:
        try:
            if not self._log_file:
                self.__enter__()
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._log_file.write(f"[{log_type}] - {timestamp}: {message}\n")
            self._log_file.flush()
        except Exception as e:
            print(f"Error writing to log: {e}")


# Usage example:
logger = Logger()


def write_log_to_file(log_type: str, message: str):
    with logger:
        logger.log(log_type, message)
