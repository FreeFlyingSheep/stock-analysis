FROM python:3.14.2-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_NO_DEV=1

COPY . .

RUN uv sync --locked

CMD ["bash", "-c", "./scripts/run_pgq.sh"]
