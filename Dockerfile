FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim@sha256:74241aba44a777b228aef38d5d1b411a7405f6ec8faffdc284e24656ea3079b5 AS builder

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




