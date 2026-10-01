# Hoymiles WiFi Exporter

Polls a Hoymiles DTU over the local network and exposes solar metrics to Prometheus. This glossary is the shared language for that domain.

## Language

**DTU**:
The Hoymiles data transfer unit — the dongle that talks to the inverters over powerline/wireless and is the exporter's only source of readings.
_Avoid_: gateway, dongle, "the device"

**Inverter**:
A Hoymiles micro-inverter, identified by its serial number. Produces one grid reading per scrape.
_Avoid_: device, module, MI

**Port**:
A PV string input on an inverter, identified as `{inverter_serial}_{port_number}`. Produces one PV reading per scrape.
_Avoid_: channel, string, input

**Grid reading**:
The AC-side measurements of one inverter: voltage, frequency, active and reactive power, current, power factor, temperature, and link status.
_Avoid_: sgs_data, grid data

**PV reading**:
The DC-side measurements of one port: power, voltage, current, and the total and daily energies.
_Avoid_: pv_data, panel data

**Link status**:
Whether an inverter is connected to the DTU. Published as the inverter's operating status.
_Avoid_: operating status (that is the metric's name, not the domain fact)

**Snapshot**:
All readings taken from one DTU response, frozen. The unit of work between fetching and publishing.
_Avoid_: response, sample, payload

**Scrape**:
One poll cycle of the DTU, at a fixed interval.
_Avoid_: poll, request, cycle

## Metric classes

**Instant metric**:
A reading that is only true right now (power, voltage, current, temperature). Reset to zero when the DTU goes stale, so a gap never reads as a real zero.
_Avoid_: live metric

**Cumulative metric**:
A reading that accumulates over time (energy total, daily energy). Never reset by staleness.
_Avoid_: counter metric

**Staleness threshold**:
The number of consecutive failed scrapes after which instant metrics reset, once.
_Avoid_: failure limit, failure count
