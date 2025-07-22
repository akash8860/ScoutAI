import logging
import os

def init_logger(logfile="scraper.log", level=logging.INFO):
    """
    Initializes the logger to output to both a log file and the console.

    Args:
        logfile (str): Name of the log file (default: scraper.log)
        level (logging level): Logging level (default: INFO)
    """
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", logfile)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
