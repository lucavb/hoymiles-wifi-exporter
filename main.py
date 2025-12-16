import asyncio
import contextlib
import logging
import signal
import sys

from hoymiles_wifi.dtu import DTU
from prometheus_client import start_http_server

from collector import collect_metrics
from config import METRICS_PORT, SCRAPE_INTERVAL, get_dtu_host, setup_logging
from version import get_version

setup_logging()
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()


async def main_loop(dtu_host: str) -> None:
    dtu = DTU(dtu_host)

    logger.info("Starting metrics collection from DTU at %s", dtu_host)

    while not shutdown_event.is_set():
        await collect_metrics(dtu, dtu_host)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(shutdown_event.wait(), timeout=SCRAPE_INTERVAL)


def main() -> None:
    dtu_host = get_dtu_host()
    if not dtu_host:
        logger.error("DTU_HOST environment variable is required")
        sys.exit(1)

    logger.info("Starting Hoymiles WiFi Exporter v%s", get_version())
    logger.info("DTU Host: %s", dtu_host)
    logger.info("Metrics Port: %d", METRICS_PORT)
    logger.info("Scrape Interval: %ds", SCRAPE_INTERVAL)

    start_http_server(METRICS_PORT)
    logger.info("Prometheus metrics server started on port %d", METRICS_PORT)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown_handler(sig, frame):
        logger.info("Received signal %s, shutting down...", sig)
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        loop.run_until_complete(main_loop(dtu_host))
    finally:
        loop.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
