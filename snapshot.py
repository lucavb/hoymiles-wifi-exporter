"""Pure interpretation of one DTU response into a snapshot of readings.

The seam between the hoymiles-wifi wire format and the Prometheus renderer:
scaling conventions and label formatting live here, so the renderer only
publishes.
"""

from dataclasses import dataclass

from hoymiles_wifi.protobuf import RealDataNew_pb2


@dataclass(frozen=True)
class DtuMeta:
    serial: str
    firmware_version: int
    timestamp: int


@dataclass(frozen=True)
class GridReading:
    inverter: str
    voltage_volts: float
    frequency_hz: float
    power_watts: float
    reactive_power_var: float
    current_amps: float
    power_factor: float
    temperature_celsius: float
    link_status: int


@dataclass(frozen=True)
class PvReading:
    port: str  # "{inverter_serial}_{port_number}"
    power_watts: float
    voltage_volts: float
    current_amps: float
    energy_total_wh: float
    energy_daily_wh: float


@dataclass(frozen=True)
class DtuSnapshot:
    dtu: DtuMeta
    inverters: tuple[GridReading, ...]
    ports: tuple[PvReading, ...]


def snapshot_from_response(
    response: RealDataNew_pb2.RealDataNewReqDTO,  # pyright: ignore[reportAttributeAccessIssue]
) -> DtuSnapshot:
    dtu = DtuMeta(
        serial=str(response.device_serial_number),
        firmware_version=response.firmware_version,
        timestamp=response.timestamp,
    )

    grid_map: dict[str, GridReading] = {}
    for entry in response.sgs_data:
        key = str(entry.serial_number)
        grid_map[key] = GridReading(
            inverter=key,
            voltage_volts=entry.voltage / 10,
            frequency_hz=entry.frequency / 100,
            power_watts=entry.active_power / 10,
            reactive_power_var=entry.reactive_power / 10,
            current_amps=entry.current / 100,
            power_factor=entry.power_factor / 1000,
            temperature_celsius=entry.temperature / 10,
            link_status=entry.link_status,
        )

    ports: list[PvReading] = []
    for entry in response.pv_data:
        ports.append(
            PvReading(
                port=f"{str(entry.serial_number)}_{entry.port_number}",
                power_watts=entry.power / 10,
                voltage_volts=entry.voltage / 10,
                current_amps=entry.current / 100,
                energy_total_wh=entry.energy_total,
                energy_daily_wh=entry.energy_daily,
            )
        )

    return DtuSnapshot(
        dtu=dtu,
        inverters=tuple(grid_map.values()),
        ports=tuple(ports),
    )
