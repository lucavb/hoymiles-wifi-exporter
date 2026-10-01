import logging

from hoymiles_wifi.dtu import DTU

from config import STALE_AFTER_FAILURES
from metrics import dtu_up, publish, reset_instant
from snapshot import snapshot_from_response

logger = logging.getLogger(__name__)

_consecutive_failures = 0


async def collect_metrics(dtu: DTU, dtu_host: str) -> None:
    global _consecutive_failures

    try:
        response = await dtu.async_get_real_data_new()
    except Exception as e:
        _consecutive_failures += 1
        logger.exception(
            "DTU communication error (failure %d/%d): %s",
            _consecutive_failures,
            STALE_AFTER_FAILURES,
            e,
        )
        dtu_up.set(0)
        if STALE_AFTER_FAILURES > 0 and _consecutive_failures == STALE_AFTER_FAILURES:
            logger.info("Resetting instant metrics after %d failures", _consecutive_failures)
            try:
                reset_instant()
            except Exception as reset_error:
                logger.error("Failed to reset instant metrics: %s", reset_error)
        return

    if response is None:
        _consecutive_failures += 1
        logger.warning(
            "No response from DTU (failure %d/%d)",
            _consecutive_failures,
            STALE_AFTER_FAILURES,
        )
        dtu_up.set(0)
        if STALE_AFTER_FAILURES > 0 and _consecutive_failures == STALE_AFTER_FAILURES:
            logger.info("Resetting instant metrics after %d failures", _consecutive_failures)
            try:
                reset_instant()
            except Exception as reset_error:
                logger.error("Failed to reset instant metrics: %s", reset_error)
        return

    _consecutive_failures = 0
    dtu_up.set(1)

    try:
        snapshot = snapshot_from_response(response)
        publish(snapshot, dtu_host)
        logger.info(
            "Collected metrics: %d port(s) from %d inverter(s)",
            len(snapshot.ports),
            len(snapshot.inverters),
        )
    except Exception:
        logger.exception("Error processing metrics data")
