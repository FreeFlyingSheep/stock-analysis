FROM python:3.14.2-slim-trixie AS build

RUN apt-get update && apt-get install -y curl

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_NO_DEV=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM build AS runtime

ENV PATH="/app/.venv/bin:$PATH"
ENV NO_LOG_FILE=true

COPY --from=build /app/.venv /app/.venv

CMD ["/app/.venv/bin/app"]
