import logging

from hoymiles_wifi.dtu import DTU

from config import STALE_AFTER_FAILURES
from metrics import (
    dtu_data_age,
    dtu_up,
    inverter_info,
    reset_instant_metrics,
    update_grid_metrics,
    update_pv_metrics,
)

logger = logging.getLogger(__name__)

_consecutive_failures = 0


async def collect_metrics(dtu: DTU, dtu_host: str) -> None:
    global _consecutive_failures

    try:
        response = await dtu.async_get_real_data_new()

        if response is None:
            logger.warning("No response from async_get_real_data_new, trying async_get_real_data")
            response = await dtu.async_get_real_data()

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
                    reset_instant_metrics()
                except Exception as reset_error:
                    logger.error("Failed to reset instant metrics: %s", reset_error)
            return
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
                reset_instant_metrics()
            except Exception as reset_error:
                logger.error("Failed to reset instant metrics: %s", reset_error)
        return

    _consecutive_failures = 0
    dtu_up.set(1)

    try:
        logger.debug("Response type: %s", type(response).__name__)
        logger.debug("Response fields: %s", [f for f in dir(response) if not f.startswith("_")])

        if hasattr(response, "dtu_info") and response.dtu_info:
            dtu_data_age.set(response.dtu_info.dtu_data_time)
            inverter_info.info(
                {
                    "dtu_serial": str(response.dtu_info.dtu_sn),
                    "dtu_sw_version": getattr(response.dtu_info, "dtu_sw_version", ""),
                    "dtu_hw_version": getattr(response.dtu_info, "dtu_hw_version", ""),
                    "host": dtu_host,
                }
            )

        sgs_data_list = getattr(response, "sgs_data", []) or []
        pv_data_list = getattr(response, "pv_data", []) or []

        sgs_data_map: dict[str, object] = {}
        for sgs_data in sgs_data_list:
            serial_number = str(sgs_data.serial_number)
            logger.debug(
                "Inverter %s sgs_data fields: %s",
                serial_number,
                [f for f in dir(sgs_data) if not f.startswith("_")],
            )
            sgs_data_map[serial_number] = sgs_data

        for serial_number, sgs_data in sgs_data_map.items():
            update_grid_metrics(sgs_data, serial_number)

        ports_processed = 0
        for pv_data in pv_data_list:
            serial_number = str(pv_data.serial_number)
            port_number = pv_data.port_number
            port_label = f"{serial_number}_{port_number}"

            logger.debug(
                "Port %s pv_data fields: %s",
                port_label,
                [f for f in dir(pv_data) if not f.startswith("_")],
            )
            update_pv_metrics(pv_data, port_label)
            ports_processed += 1

        logger.info(
            "Collected metrics: %d port(s) from %d inverter(s)",
            ports_processed,
            len(sgs_data_list),
        )
    except Exception as e:
        logger.exception("Error processing metrics data: %s", e)
