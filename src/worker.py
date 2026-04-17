import time, logging, os

logger = logging.getLogger("worker")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "worker": "timestamp-updater", "message": "%(message)s"}'))
logger.addHandler(handler)

while True:
    logger.info(f"Updating timestamp of today records in {os.getenv('APP_ENV', 'DEV')} environment")
    time.sleep(60)