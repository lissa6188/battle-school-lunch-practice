#!/usr/bin/env bash
# Starts the application stack using Docker Compose.
# Usage:
#   ./scripts/start.sh        # run in foreground
#   ./scripts/start.sh -d     # run detached (background)

set -euo pipefail
DETACH=""
if [[ ${1:-} == "-d" ]]; then
  DETACH="-d"
fi

# Change to repo root (one level up from scripts)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
cd "$DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not found in PATH. Please install Docker and ensure 'docker' is available." >&2
  exit 1
fi

echo "Running: docker compose up --build $DETACH"
exec docker compose up --build $DETACH
