from datetime import date, datetime
import os
from typing import Optional
from pathlib import Path
from utils import *


# def write_log_to_file(log_type: str, message: str, log_file: TextIOWrapper = None):
#     if not log_file:
#         if not os.path.exists("logs"):
#             os.mkdir("logs")

#         if not os.path.exists(
#             os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt")
#         ):
#             log_file = open(
#                 os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt"),
#                 "w",
#             )
#         else:
#             log_file = open(
#                 os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt"),
#                 "a",
#             )
#         return log_file

#     log_file.write(f"[{log_type}] - {datetime.now().strftime('%H:%M:%S')}: {message}\n")

#     return log_file

# global log_file
# log_file = write_log_to_file(None,None,None)


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
            self._log_file = open(self.log_file_path, 'a')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._log_file:
            self._log_file.close()
            self._log_file = None
    
    def log(self, log_type: str, message: str) -> None:
        try:
            if not self._log_file:
                self.__enter__()
            timestamp = datetime.now().strftime('%H:%M:%S')
            self._log_file.write(f"[{log_type}] - {timestamp}: {message}\n")
            self._log_file.flush()
        except Exception as e:
            print(f"Error writing to log: {e}")

# Usage example:
logger = Logger()

def write_log_to_file(log_type: str, message: str):
    with logger:
        logger.log(log_type, message)