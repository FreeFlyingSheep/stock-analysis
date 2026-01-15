#!/bin/bash
# Run the PGQueuer to process jobs for the stock analysis application.
#
# Requirements:
#   - Valid .env file with database credentials
#   - scripts/init.sh has been run to set up the project
set -euo pipefail

uv run pgq \
    run stock_analysis.jobs.pgqueuer:create_pgqueuer \
    --batch-size ${BATCH_SIZE} \
    --max-concurrent-tasks ${MAX_CONCURRENT_TASKS}
