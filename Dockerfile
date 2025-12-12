FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:4f0bb0bed02fc05d6361b4ed2c37cddd40ce6478abb222a2f30036e0888f6db5 AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.14-slim-bookworm@sha256:404ca55875fc24a64f0a09e9ec7d405d725109aec04c9bf0991798fd45c7b898

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/main.py /app/main.py

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 9099

CMD ["python", "main.py"]




