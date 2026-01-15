FROM python:3.14.2-slim-trixie

RUN apt-get update && apt-get install -y curl

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_NO_DEV=1

COPY . .

RUN uv sync --locked

CMD ["uv", "run", "app"]
