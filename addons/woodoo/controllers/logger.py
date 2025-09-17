from datetime import datetime


class Logger():
    @staticmethod
    def log(message):
        with open("/tmp/woodoo.log", "a") as log_file:
            log_file.write("\n=====================\n")
            log_file.write(f"{datetime.now()}\n")
            log_file.write(f"{message}\n")
