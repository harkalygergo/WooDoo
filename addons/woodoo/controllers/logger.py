import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path="config/.env")

class Logger():
    @staticmethod
    def log(message):
        debug = os.getenv("DEBUG", "false").lower() == "true"
        if not debug:
            return
        with open("/tmp/woodoo.log", "a") as log_file:
            log_file.write("\n=====================\n")
            log_file.write(f"{datetime.now()}\n")
            log_file.write(f"{message}\n")
