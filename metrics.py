import logging

from prometheus_client import Gauge, Info

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
grid_energy_total = Gauge(
    "hoymiles_grid_energy_total_wh",
    "Total grid energy in watt-hours",
    ["inverter"],
)
grid_energy_daily = Gauge(
    "hoymiles_grid_energy_daily_wh",
    "Daily grid energy in watt-hours",
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


def register_port(port_label: str) -> None:
    """Track a port label for later reset."""
    _known_ports.add(port_label)


def register_inverter(inverter_label: str) -> None:
    """Track an inverter label for later reset."""
    _known_inverters.add(inverter_label)


def reset_instant_metrics() -> None:
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


def update_pv_metrics(pv_data, port_label: str) -> None:
    register_port(port_label)
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


def update_grid_metrics(sgs_data, inverter_label: str) -> None:
    register_inverter(inverter_label)
    grid_voltage.labels(inverter=inverter_label).set(_get_metric_value(sgs_data, "voltage") / 10)
    grid_frequency.labels(inverter=inverter_label).set(
        _get_metric_value(sgs_data, "frequency") / 100
    )
    grid_power.labels(inverter=inverter_label).set(_get_metric_value(sgs_data, "active_power") / 10)
    reactive = _get_metric_value(sgs_data, "reactive_power")
    grid_reactive_power.labels(inverter=inverter_label).set(reactive / 10)
    grid_current.labels(inverter=inverter_label).set(_get_metric_value(sgs_data, "current") / 100)
    grid_energy_total.labels(inverter=inverter_label).set(
        _get_metric_value(sgs_data, "energy_total")
    )
    grid_energy_daily.labels(inverter=inverter_label).set(
        _get_metric_value(sgs_data, "energy_daily")
    )

    inverter_power_factor.labels(inverter=inverter_label).set(
        _get_metric_value(sgs_data, "power_factor") / 1000
    )
    inverter_temperature.labels(inverter=inverter_label).set(
        _get_metric_value(sgs_data, "temperature") / 10
    )
    inverter_operating_status.labels(inverter=inverter_label).set(
        _get_metric_value(sgs_data, "operating_status")
    )
