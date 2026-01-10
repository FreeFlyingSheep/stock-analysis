#!/bin/bash
# Run the PGQueuer to process jobs for the stock analysis application.
#
# Exit codes:
#   0: PGQueuer started successfully
#   others: PGQueuer failed to start
#
# Requirements:
#   - Valid .env file with database credentials
#   - scripts/init.sh has been run to set up the project
set -euo pipefail

source .env

pgq run stock_analysis.jobs.pgqueuer:create_pgqueuer --batch-size 2 --max-concurrent-tasks 5
