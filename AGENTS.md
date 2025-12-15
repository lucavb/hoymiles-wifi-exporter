# AGENTS.md

This repository is **hoymiles-wifi-exporter**: a small Python Prometheus exporter that polls a Hoymiles WiFi DTU/inverter via the `hoymiles-wifi` library and exposes metrics over HTTP.

If you are an AI coding agent working in this repo, optimize for:
- Keeping the runtime stable (this runs continuously and is usually deployed as a container)
- Avoiding breaking changes in metric names/labels
- Making changes that pass the existing CI checks (ruff + pyright + Docker build)

## Project layout

- `main.py`: single-file application entrypoint (defines metrics, polling loop, and HTTP server)
- `pyproject.toml`: project metadata + dependencies + ruff/pyright configuration
- `uv.lock`: locked dependency graph used by `uv sync --frozen`
- `Dockerfile`: multi-stage build using `uv` to create a `.venv`, then a slim runtime image
- `.github/workflows/ci.yml`: ruff check, ruff format (check), pyright, and a Docker build
- `.github/workflows/release.yml`: semantic-release tagging + container build/push to GHCR

## Runtime behavior (read before changing metrics)

- **Required env var**: `DTU_HOST` (IP/hostname of the inverter/DTU)
- **Optional env vars**:
  - `METRICS_PORT` (default: `9099`)
  - `SCRAPE_INTERVAL` seconds (default: `35`; do not go below ~32s as it can impact cloud/app connectivity per upstream notes)
  - `DEBUG` (`true`/`1` enables debug logs)

Metrics are exposed via `prometheus_client.start_http_server(METRICS_PORT)`.

### Metric stability

- Treat existing metric names and label sets as **public API**.
- If you must change a metric, prefer:
  - adding a *new* metric instead of renaming
  - keeping old metrics for backward compatibility when feasible

## Development environment

### Python version

- Local dev version is pinned by `.python-version`: **Python 3.14**.
- CI, local development, and the Docker image are all expected to run on **Python 3.14**.

### Install dependencies (uv)

- **Prod-only**:

```bash
uv sync
```

- **With dev tools (ruff + pyright)**:

```bash
uv sync --dev
```

Do not hand-edit `uv.lock`. Update dependencies via `uv` so the lock stays consistent.

## Common commands

### Run locally

```bash
DTU_HOST=192.168.1.100 uv run hoymiles-wifi-exporter
```

Alternative (equivalent entrypoint):

```bash
DTU_HOST=192.168.1.100 uv run python main.py
```

### Lint / format

```bash
uv run ruff check .
uv run ruff format .
```

CI enforces formatting:

```bash
uv run ruff format --check .
```

### Typecheck

```bash
uv run pyright
```

### Docker

Build:

```bash
docker build -t hoymiles-wifi-exporter:test .
```

Run:

```bash
docker run --rm -p 9099:9099 -e DTU_HOST=192.168.1.100 hoymiles-wifi-exporter:test
```

## CI expectations

GitHub Actions (`.github/workflows/ci.yml`) runs:
- `uv sync --dev`
- `ruff check .`
- `ruff format --check .`
- `pyright`
- `docker build ...`

If you change dependencies or Python constraints, update:
- `pyproject.toml`
- `uv.lock`
- CI workflow Python versions (if necessary)
- Dockerfile base image (if necessary)

## Release process (context)

Releases are tag-driven using `python-semantic-release` in `.github/workflows/release.yml`.
- It creates GitHub releases and tags (format `v{version}`)
- If a new tag was produced, it builds and pushes multi-arch images to GHCR

As an agent, do not introduce manual version-bump commits unless the maintainer explicitly wants that flow.

## Coding conventions

- Keep changes small and reviewable (this repo is intentionally minimal)
- Prefer clear, explicit code in `main.py` over adding new modules unless complexity demands it
- Follow existing logging style and keep default logging at INFO (DEBUG behind `DEBUG` env var)
- Ruff configuration:
  - line length: 100
  - lint rules: `E`, `F`, `I`, `UP`, `B`, `SIM`

## Security & operations

- Never add secrets/keys to the repo.
- This service talks to a LAN DTU; avoid adding “phone-home” behavior.
- Be careful when changing network timeouts/retry loops: it should not DoS the DTU or spam logs.


