"""Prometheus renderer for DTU snapshots.

Owns the module-level metric objects; interpretation of the wire format
lives in snapshot.py, this module only publishes.
"""

import logging
import time

from prometheus_client import Gauge, Info

from snapshot import DtuSnapshot

logger = logging.getLogger(__name__)

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
    ["inverter"],
)
grid_frequency = Gauge(
    "hoymiles_grid_frequency_hz",
    "Grid frequency in Hz",
    ["inverter"],
)
grid_power = Gauge(
    "hoymiles_grid_power_watts",
    "Grid power in watts",
    ["inverter"],
)
grid_reactive_power = Gauge(
    "hoymiles_grid_reactive_power_var",
    "Grid reactive power in var",
    ["inverter"],
)
grid_current = Gauge(
    "hoymiles_grid_current_amps",
    "Grid current in amps",
    ["inverter"],
)

inverter_power_factor = Gauge(
    "hoymiles_inverter_power_factor",
    "Inverter power factor",
    ["inverter"],
)
inverter_temperature = Gauge(
    "hoymiles_inverter_temperature_celsius",
    "Inverter temperature in celsius",
    ["inverter"],
)
inverter_operating_status = Gauge(
    "hoymiles_inverter_operating_status",
    "Inverter operating status",
    ["inverter"],
)

dtu_data_age = Gauge(
    "hoymiles_dtu_data_age_seconds",
    "Age of data from DTU in seconds",
)
dtu_up = Gauge(
    "hoymiles_dtu_up",
    "DTU connection status (1 = up, 0 = down)",
)

_known_ports: set[str] = set()
_known_inverters: set[str] = set()


def publish(snapshot: DtuSnapshot, dtu_host: str) -> None:
    inverter_info.info(
        {
            "dtu_serial": snapshot.dtu.serial,
            "dtu_sw_version": str(snapshot.dtu.firmware_version),
            "host": dtu_host,
        }
    )

    logger.debug("Raw DTU timestamp: %s", snapshot.dtu.timestamp)

    if snapshot.dtu.timestamp > 0:
        dtu_data_age.set(time.time() - snapshot.dtu.timestamp)

    for r in snapshot.inverters:
        _known_inverters.add(r.inverter)
        labels = {"inverter": r.inverter}
        grid_voltage.labels(**labels).set(r.voltage_volts)
        grid_frequency.labels(**labels).set(r.frequency_hz)
        grid_power.labels(**labels).set(r.power_watts)
        grid_reactive_power.labels(**labels).set(r.reactive_power_var)
        grid_current.labels(**labels).set(r.current_amps)
        inverter_power_factor.labels(**labels).set(r.power_factor)
        inverter_temperature.labels(**labels).set(r.temperature_celsius)
        inverter_operating_status.labels(**labels).set(r.link_status)

    for r in snapshot.ports:
        _known_ports.add(r.port)
        labels = {"port": r.port}
        pv_power.labels(**labels).set(r.power_watts)
        pv_voltage.labels(**labels).set(r.voltage_volts)
        pv_current.labels(**labels).set(r.current_amps)
        pv_energy_total.labels(**labels).set(r.energy_total_wh)
        pv_energy_daily.labels(**labels).set(r.energy_daily_wh)


def reset_instant() -> None:
    """Reset power/voltage/current metrics to 0 for all known ports and inverters."""
    for port in _known_ports:
        pv_power.labels(port=port).set(0)
        pv_voltage.labels(port=port).set(0)
        pv_current.labels(port=port).set(0)

    for inverter in _known_inverters:
        grid_power.labels(inverter=inverter).set(0)
        grid_voltage.labels(inverter=inverter).set(0)
        grid_frequency.labels(inverter=inverter).set(0)
        grid_current.labels(inverter=inverter).set(0)
        grid_reactive_power.labels(inverter=inverter).set(0)
        inverter_power_factor.labels(inverter=inverter).set(0)
        inverter_temperature.labels(inverter=inverter).set(0)
        inverter_operating_status.labels(inverter=inverter).set(0)
