#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# start.sh — Safe startup script for the MyGES Discord bot on a VPS.
#
# Problem: If `schedule_state.json` does not exist on the host when Docker
# mounts it, Docker creates a *directory* at that path.  The bot then fails
# with "IsADirectoryError" when trying to open that path as a JSON file.
#
# This script must be run instead of `docker-compose up` directly.
# ---------------------------------------------------------------------------

set -euo pipefail

# Step 1 – If Docker previously created a directory by mistake, remove it.
if [ -d schedule_state.json ]; then
    echo "[start.sh] WARNING: schedule_state.json is a directory (Docker bug). Removing it."
    rm -rf schedule_state.json
fi

# Step 2 – Create the file if it doesn't exist yet.
if [ ! -f schedule_state.json ]; then
    echo "[start.sh] Creating empty schedule_state.json"
    echo '{}' > schedule_state.json
fi

echo "[start.sh] Starting bot with docker-compose..."
docker-compose up -d --build

echo "[start.sh] Done. Use 'docker-compose logs -f' to follow the logs."
