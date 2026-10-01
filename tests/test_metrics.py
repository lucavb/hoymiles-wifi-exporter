import time

import pytest
from hoymiles_wifi.protobuf import RealDataNew_pb2
from prometheus_client import REGISTRY, generate_latest

from metrics import publish, reset_instant
from snapshot import snapshot_from_response


def _make_response() -> RealDataNew_pb2.RealDataNewReqDTO:  # pyright: ignore[reportAttributeAccessIssue]
    response = RealDataNew_pb2.RealDataNewReqDTO()  # pyright: ignore[reportAttributeAccessIssue]
    response.device_serial_number = "DTUSN123"
    response.firmware_version = 1056
    response.timestamp = int(time.time() - 10)
    sgs = response.sgs_data.add()
    sgs.serial_number = 1001
    sgs.voltage = 2310
    sgs.frequency = 5000
    sgs.active_power = 1230
    sgs.reactive_power = -100
    sgs.current = 150
    sgs.power_factor = 980
    sgs.temperature = 380
    sgs.link_status = 1
    pv = response.pv_data.add()
    pv.serial_number = 42
    pv.port_number = 1
    pv.power = 2500
    pv.voltage = 3300
    pv.current = 750
    pv.energy_total = 12345
    pv.energy_daily = 678
    return response


@pytest.fixture
def snapshot():
    return snapshot_from_response(_make_response())


def test_publish_exposes_pv_and_grid_lines(snapshot) -> None:
    publish(snapshot, "testhost")

    output = generate_latest(REGISTRY)

    assert b'hoymiles_pv_power_watts{port="42_1"} 250.0' in output
    assert b'hoymiles_pv_voltage_volts{port="42_1"} 330.0' in output
    assert b'hoymiles_pv_current_amps{port="42_1"} 7.5' in output
    assert b'hoymiles_pv_energy_total_wh{port="42_1"} 12345.0' in output
    assert b'hoymiles_pv_energy_daily_wh{port="42_1"} 678.0' in output
    assert b'hoymiles_grid_voltage_volts{inverter="1001"} 231.0' in output
    assert b'hoymiles_grid_frequency_hz{inverter="1001"} 50.0' in output
    assert b'hoymiles_grid_power_watts{inverter="1001"} 123.0' in output
    assert b'hoymiles_grid_reactive_power_var{inverter="1001"} -10.0' in output
    assert b'hoymiles_grid_current_amps{inverter="1001"} 1.5' in output
    assert b'hoymiles_inverter_power_factor{inverter="1001"} 0.98' in output
    assert b'hoymiles_inverter_temperature_celsius{inverter="1001"} 38.0' in output
    info_lines = [
        line
        for line in output.splitlines()
        if line.startswith(b"hoymiles_inverter_info{") and b'"testhost"' in line
    ]
    assert info_lines
    assert b"dtu_serial" in info_lines[0]
    assert b"DTUSN123" in info_lines[0]
    assert b"dtu_sw_version" in info_lines[0]
    assert b"1056" in info_lines[0]


def test_reset_instant_zeroes_instant_gauges_only(snapshot) -> None:
    publish(snapshot, "testhost")
    reset_instant()

    output = generate_latest(REGISTRY)

    assert b'hoymiles_pv_power_watts{port="42_1"} 0.0' in output
    assert b'hoymiles_pv_voltage_volts{port="42_1"} 0.0' in output
    assert b'hoymiles_pv_current_amps{port="42_1"} 0.0' in output
    assert b'hoymiles_pv_energy_total_wh{port="42_1"} 12345.0' in output
    assert b'hoymiles_pv_energy_daily_wh{port="42_1"} 678.0' in output


def test_dtu_data_age_uses_clock(monkeypatch) -> None:
    fixed_now = 1_000_000.0
    monkeypatch.setattr("metrics.time.time", lambda: fixed_now)
    response = _make_response()
    response.timestamp = int(fixed_now - 10)
    snapshot = snapshot_from_response(response)

    publish(snapshot, "testhost")

    output = generate_latest(REGISTRY)
    assert b"hoymiles_dtu_data_age_seconds 10.0" in output


def test_operating_status_carries_link_status(snapshot) -> None:
    publish(snapshot, "testhost")

    output = generate_latest(REGISTRY)

    assert b'hoymiles_inverter_operating_status{inverter="1001"} 1.0' in output
