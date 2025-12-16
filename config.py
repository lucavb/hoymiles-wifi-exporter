import logging
import os


def setup_logging() -> logging.Logger:
    log_level = (
        logging.DEBUG if os.environ.get("DEBUG", "").lower() in ("1", "true") else logging.INFO
    )
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


METRICS_PORT = int(os.environ.get("METRICS_PORT", "9099"))
SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL", "35"))
STALE_AFTER_FAILURES = int(os.environ.get("STALE_AFTER_FAILURES", "3"))


def get_dtu_host() -> str | None:
    return os.environ.get("DTU_HOST")
