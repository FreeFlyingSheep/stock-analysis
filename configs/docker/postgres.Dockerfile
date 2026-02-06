FROM postgres:18-trixie

ARG TARGETARCH

RUN set -eux; \
    case "${TARGETARCH}" in amd64|arm64) ;; *) exit 1 ;; esac; \
    apt-get update; \
    apt-get install -y --no-install-recommends wget ca-certificates postgresql-18-pgvector; \
    PKG="pg-textsearch-postgresql-18_0.5.0-1_${TARGETARCH}.deb"; \
    wget -O "/tmp/${PKG}" "https://github.com/timescale/pg_textsearch/releases/download/v0.5.0/${PKG}"; \
    apt-get install -y --no-install-recommends "/tmp/${PKG}"; \
    rm -f "/tmp/${PKG}"; \
    rm -rf /var/lib/apt/lists/*
