#!/bin/bash
# Build the docker images for the stock analysis application.
#
# Requirements:
#   - Minikube is running
set -euo pipefail

eval $(minikube -p minikube docker-env)

docker build -t stock-analysis-migrate:dev -f docker/migrate.Dockerfile .
docker build -t stock-analysis-api:dev -f docker/api.Dockerfile .
docker build -t stock-analysis-worker:dev -f docker/worker.Dockerfile .
docker build -t stock-analysis-web:dev -f docker/web.Dockerfile .
