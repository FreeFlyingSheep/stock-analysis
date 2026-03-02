#!/bin/bash
# Generate a visual graph of the Docker Compose services and their dependencies.
set -euo pipefail

docker run \
    --rm \
    -v $(PWD):/data \
    derlin/docker-compose-viz-mermaid \
    /data/compose.yaml \
    -f svg \
    -o docs/images/compose.svg
