from utils import *

def write_log_to_file(log_type: str, message: str, log_file: TextIOWrapper = None):
    if not log_file:
        if not os.path.exists("logs"):
            os.mkdir("logs")

        if not os.path.exists(
            os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt")
        ):
            log_file = open(
                os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt"),
                "w",
            )
        else:
            log_file = open(
                os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt"),
                "a",
            )
        return log_file

    log_file.write(f"[{log_type}] - {datetime.now().strftime('%H:%M:%S')}: {message}\n")

    return log_file

global log_file
log_file = write_log_to_file(None,None,None)