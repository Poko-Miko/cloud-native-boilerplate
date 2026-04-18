import logging
import os
import time
from datetime import date, datetime, timezone


def build_logger() -> logging.Logger:
    logger = logging.getLogger("cloud_worker")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                '{"time":"%(asctime)s","level":"%(levelname)s",'
                '"service":"cloud-worker","message":"%(message)s"}'
            )
        )
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = build_logger()


def get_worker_interval() -> int:
    raw_interval = os.getenv("WORKER_INTERVAL_SECONDS", "60")
    try:
        interval = int(raw_interval)
    except ValueError:
        logger.warning(
            "invalid WORKER_INTERVAL_SECONDS="
            f"{raw_interval}; falling back to 60s"
        )
        return 60

    return max(interval, 1)


def update_today_records_timestamp() -> dict:
    now = datetime.now(timezone.utc)
    today = date.today().isoformat()
    result = {
        "record_date": today,
        "updated_at": now.isoformat(),
        "updated_records": 1,
    }
    logger.info(
        "updated today records timestamp "
        f"record_date={result['record_date']} "
        f"updated_at={result['updated_at']} "
        f"updated_records={result['updated_records']}"
    )
    return result


def run_forever() -> None:
    interval = get_worker_interval()
    env = os.getenv("APP_ENV", "DEV")

    logger.info(
        f"worker started in {env} environment "
        f"with interval={interval}s"
    )

    while True:
        try:
            update_today_records_timestamp()
            time.sleep(interval)
        except Exception as exc:
            logger.exception(f"worker loop failed: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    run_forever()
