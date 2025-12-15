import asyncio
import contextlib
import logging
import os
import signal
import sys

from hoymiles_wifi.dtu import DTU
from prometheus_client import Gauge, Info, start_http_server

log_level = logging.DEBUG if os.environ.get("DEBUG", "").lower() in ("1", "true") else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

METRICS_PORT = int(os.environ.get("METRICS_PORT", "9099"))
SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL", "35"))

inverter_info = Info("hoymiles_inverter", "Inverter information")

pv_power = Gauge(
    "hoymiles_pv_power_watts",
    "PV power in watts",
    ["port"],
)
pv_voltage = Gauge(
    "hoymiles_pv_voltage_volts",
    "PV voltage in volts",
    ["port"],
)
pv_current = Gauge(
    "hoymiles_pv_current_amps",
    "PV current in amps",
    ["port"],
)
pv_energy_total = Gauge(
    "hoymiles_pv_energy_total_wh",
    "Total PV energy in watt-hours",
    ["port"],
)
pv_energy_daily = Gauge(
    "hoymiles_pv_energy_daily_wh",
    "Daily PV energy in watt-hours",
    ["port"],
)

grid_voltage = Gauge(
    "hoymiles_grid_voltage_volts",
    "Grid voltage in volts",
    ["port"],
)
grid_frequency = Gauge(
    "hoymiles_grid_frequency_hz",
    "Grid frequency in Hz",
    ["port"],
)
grid_power = Gauge(
    "hoymiles_grid_power_watts",
    "Grid power in watts",
    ["port"],
)
grid_reactive_power = Gauge(
    "hoymiles_grid_reactive_power_var",
    "Grid reactive power in var",
    ["port"],
)
grid_current = Gauge(
    "hoymiles_grid_current_amps",
    "Grid current in amps",
    ["port"],
)
grid_energy_total = Gauge(
    "hoymiles_grid_energy_total_wh",
    "Total grid energy in watt-hours",
    ["port"],
)
grid_energy_daily = Gauge(
    "hoymiles_grid_energy_daily_wh",
    "Daily grid energy in watt-hours",
    ["port"],
)

inverter_power_factor = Gauge(
    "hoymiles_inverter_power_factor",
    "Inverter power factor",
    ["port"],
)
inverter_temperature = Gauge(
    "hoymiles_inverter_temperature_celsius",
    "Inverter temperature in celsius",
    ["port"],
)
inverter_operating_status = Gauge(
    "hoymiles_inverter_operating_status",
    "Inverter operating status",
    ["port"],
)

dtu_data_age = Gauge(
    "hoymiles_dtu_data_age_seconds",
    "Age of data from DTU in seconds",
)
dtu_up = Gauge(
    "hoymiles_dtu_up",
    "DTU connection status (1 = up, 0 = down)",
)


def update_pv_metrics(pv_data, port_label: str) -> None:
    pv_power.labels(port=port_label).set(pv_data.power / 10)
    pv_voltage.labels(port=port_label).set(pv_data.voltage / 10)
    pv_current.labels(port=port_label).set(pv_data.current / 100)
    pv_energy_total.labels(port=port_label).set(pv_data.energy_total)
    pv_energy_daily.labels(port=port_label).set(pv_data.energy_daily)


def _get_metric_value(obj: object, attr: str, default: float = 0) -> float:
    value = getattr(obj, attr, None)
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.debug("Could not convert %s=%r to float", attr, value)
        return default


def update_grid_metrics(sgs_data, port_label: str) -> None:
    grid_voltage.labels(port=port_label).set(_get_metric_value(sgs_data, "voltage") / 10)
    grid_frequency.labels(port=port_label).set(_get_metric_value(sgs_data, "frequency") / 100)
    grid_power.labels(port=port_label).set(_get_metric_value(sgs_data, "power") / 10)
    reactive = _get_metric_value(sgs_data, "reactive_power")
    grid_reactive_power.labels(port=port_label).set(reactive / 10)
    grid_current.labels(port=port_label).set(_get_metric_value(sgs_data, "current") / 100)
    grid_energy_total.labels(port=port_label).set(_get_metric_value(sgs_data, "energy_total"))
    grid_energy_daily.labels(port=port_label).set(_get_metric_value(sgs_data, "energy_daily"))

    inverter_power_factor.labels(port=port_label).set(_get_metric_value(sgs_data, "pf") / 1000)
    inverter_temperature.labels(port=port_label).set(_get_metric_value(sgs_data, "temp") / 10)
    inverter_operating_status.labels(port=port_label).set(
        _get_metric_value(sgs_data, "operating_status")
    )


async def collect_metrics(dtu: DTU, dtu_host: str) -> None:
    try:
        response = await dtu.async_get_real_data_new()

        if response is None:
            logger.warning("No response from async_get_real_data_new, trying async_get_real_data")
            response = await dtu.async_get_real_data()

        if response is None:
            logger.warning("No response from DTU")
            dtu_up.set(0)
            return

        dtu_up.set(1)
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

            sgs_data = sgs_data_map.get(serial_number)
            if sgs_data:
                update_grid_metrics(sgs_data, port_label)
            else:
                logger.warning("Port %s: no sgs_data found, grid metrics not updated", port_label)

            ports_processed += 1

        logger.info(
            "Collected metrics: %d port(s) from %d inverter(s)",
            ports_processed,
            len(sgs_data_list),
        )

    except Exception as e:
        logger.exception("Error collecting metrics: %s", e)
        dtu_up.set(0)


shutdown_event = asyncio.Event()


async def main_loop(dtu_host: str) -> None:
    dtu = DTU(dtu_host)

    logger.info("Starting metrics collection from DTU at %s", dtu_host)

    while not shutdown_event.is_set():
        await collect_metrics(dtu, dtu_host)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(shutdown_event.wait(), timeout=SCRAPE_INTERVAL)


def main() -> None:
    dtu_host = os.environ.get("DTU_HOST")
    if not dtu_host:
        logger.error("DTU_HOST environment variable is required")
        sys.exit(1)

    logger.info("Starting Hoymiles WiFi Exporter")
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
