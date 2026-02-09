FROM postgres:18-trixie

ARG TARGETARCH

RUN set -eux; \
    case "${TARGETARCH}" in amd64|arm64) ;; *) exit 1 ;; esac

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget ca-certificates postgresql-18-pgvector \
        build-essential git postgresql-server-dev-18

RUN cd /tmp && \
    PKG="pg-textsearch-postgresql-18_0.5.0-1_${TARGETARCH}.deb" && \
    wget -O "/tmp/${PKG}" "https://github.com/timescale/pg_textsearch/releases/download/v0.5.0/${PKG}" && \
    apt-get install -y --no-install-recommends "/tmp/${PKG}" && \
    rm -f "/tmp/${PKG}"

RUN cd /tmp && \
    wget -q -O - http://www.xunsearch.com/scws/down/scws-1.2.3.tar.bz2 | tar xjf - && \
    cd scws-1.2.3 && \
    ./configure && \
    make && \
    make install && \
    cd /tmp && \
    rm -rf scws-1.2.3

RUN cd /tmp && \
    git clone https://github.com/amutu/zhparser.git && \
    cd zhparser && \
    make && \
    make install && \
    cd /tmp && \
    rm -rf zhparser

RUN apt-get purge -y --auto-remove build-essential git postgresql-server-dev-18 && \
    rm -rf /var/lib/apt/lists/*
