from hoymiles_wifi.protobuf import RealDataNew_pb2

from snapshot import snapshot_from_response


def _make_response() -> RealDataNew_pb2.RealDataNewReqDTO:  # pyright: ignore[reportAttributeAccessIssue]
    response = RealDataNew_pb2.RealDataNewReqDTO()  # pyright: ignore[reportAttributeAccessIssue]
    response.device_serial_number = "DTUSN123"
    response.firmware_version = 1056
    response.timestamp = 1700000000
    return response


def test_grid_reading_scales_and_labels() -> None:
    response = _make_response()
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

    snapshot = snapshot_from_response(response)

    assert len(snapshot.inverters) == 1
    r = snapshot.inverters[0]
    assert r.inverter == "1001"
    assert r.voltage_volts == 231.0
    assert r.frequency_hz == 50.0
    assert r.power_watts == 123.0
    assert r.reactive_power_var == -10.0
    assert r.current_amps == 1.5
    assert r.power_factor == 0.98
    assert r.temperature_celsius == 38.0
    assert r.link_status == 1


def test_pv_reading_scales_and_port_label() -> None:
    response = _make_response()
    pv = response.pv_data.add()
    pv.serial_number = 42
    pv.port_number = 1
    pv.power = 2500
    pv.voltage = 3300
    pv.current = 750
    pv.energy_total = 12345
    pv.energy_daily = 678

    snapshot = snapshot_from_response(response)

    assert len(snapshot.ports) == 1
    r = snapshot.ports[0]
    assert r.port == "42_1"
    assert r.power_watts == 250.0
    assert r.voltage_volts == 330.0
    assert r.current_amps == 7.5
    assert r.energy_total_wh == 12345.0
    assert r.energy_daily_wh == 678.0


def test_dtu_meta_mapped_from_root_fields() -> None:
    response = _make_response()

    snapshot = snapshot_from_response(response)

    assert snapshot.dtu.serial == "DTUSN123"
    assert snapshot.dtu.firmware_version == 1056
    assert snapshot.dtu.timestamp == 1700000000


def test_empty_data_yields_empty_tuples() -> None:
    response = _make_response()

    snapshot = snapshot_from_response(response)

    assert snapshot.inverters == ()
    assert snapshot.ports == ()
    assert snapshot.dtu.serial == "DTUSN123"


def test_duplicate_inverter_serials_last_wins_keeps_first_position() -> None:
    response = _make_response()
    first = response.sgs_data.add()
    first.serial_number = 1001
    first.voltage = 2310
    second = response.sgs_data.add()
    second.serial_number = 1002
    second.voltage = 2350
    third = response.sgs_data.add()
    third.serial_number = 1001
    third.voltage = 2400

    snapshot = snapshot_from_response(response)

    assert len(snapshot.inverters) == 2
    assert snapshot.inverters[0].inverter == "1001"
    assert snapshot.inverters[1].inverter == "1002"
    assert snapshot.inverters[0].voltage_volts == 240.0
