# Hoymiles WiFi Exporter

Prometheus exporter for Hoymiles WiFi inverters using [hoymiles-wifi](https://github.com/suaveolent/hoymiles-wifi).

## Installation

### Using uv

```bash
uv sync
uv run hoymiles-wifi-exporter
```

### Using Docker

```bash
docker run -d \
  --name hoymiles-exporter \
  -p 9099:9099 \
  -e DTU_HOST=192.168.1.100 \
  ghcr.io/lucavb/hoymiles-wifi-exporter:latest
```

### Docker Compose

```yaml
services:
  hoymiles-exporter:
    image: ghcr.io/lucavb/hoymiles-wifi-exporter:latest
    ports:
      - "9099:9099"
    environment:
      - DTU_HOST=192.168.1.100
    restart: unless-stopped
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DTU_HOST` | *required* | IP address of the inverter/DTU |
| `METRICS_PORT` | `9099` | Port for Prometheus metrics endpoint |
| `SCRAPE_INTERVAL` | `35` | Seconds between data fetches (≥35s recommended) |
| `DEBUG` | `false` | Enable debug logging |

## Metrics

### PV (Solar Panel) Metrics

- `hoymiles_pv_power_watts` - PV power in watts
- `hoymiles_pv_voltage_volts` - PV voltage in volts
- `hoymiles_pv_current_amps` - PV current in amps
- `hoymiles_pv_energy_total_wh` - Total PV energy in watt-hours
- `hoymiles_pv_energy_daily_wh` - Daily PV energy in watt-hours

### Grid Metrics

- `hoymiles_grid_voltage_volts` - Grid voltage in volts
- `hoymiles_grid_frequency_hz` - Grid frequency in Hz
- `hoymiles_grid_power_watts` - Grid power in watts
- `hoymiles_grid_reactive_power_var` - Grid reactive power in var
- `hoymiles_grid_current_amps` - Grid current in amps
- `hoymiles_grid_energy_total_wh` - Total grid energy in watt-hours
- `hoymiles_grid_energy_daily_wh` - Daily grid energy in watt-hours

### Inverter Metrics

- `hoymiles_inverter_power_factor` - Power factor
- `hoymiles_inverter_temperature_celsius` - Temperature in celsius
- `hoymiles_inverter_operating_status` - Operating status code
- `hoymiles_inverter_info` - Inverter information labels

### DTU Metrics

- `hoymiles_dtu_up` - Connection status (1 = up, 0 = down)
- `hoymiles_dtu_data_age_seconds` - Age of data from DTU

## Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'hoymiles'
    static_configs:
      - targets: ['localhost:9099']
    scrape_interval: 35s
```

## Supported Devices

Tested with HMS-800W-2T. Should work with other Hoymiles WiFi inverters and DTUs supported by [hoymiles-wifi](https://github.com/suaveolent/hoymiles-wifi#supported-devices).

## Notes

The scrape interval is set to 35 seconds by default. According to the hoymiles-wifi documentation, intervals below ~32 seconds may disable cloud functionality. Setting to 1-2 seconds may disrupt app connections.

## Development

```bash
uv sync --dev
uv run ruff check .
uv run ruff format .
uv run pyright
```

## License

MIT
