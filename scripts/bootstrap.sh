#!/bin/sh
# Entrypoint wrapper for Hermes on Render with Gemma support.
#
# Runs as root (PID-1 child of tini). On every boot it:
#   1. Ensures /opt/data exists and is owned by hermes:hermes.
#   2. Regenerates config.yaml with Gemma model + WebSocket messaging enabled.
#   3. Loads .env from /opt/data/.env if it exists.
#   4. Exec's the upstream entrypoint chain.

set -eu

DATA_DIR="${HERMES_HOME:-/opt/data}"
CONFIG_FILE="${DATA_DIR}/config.yaml"
ENV_FILE="${DATA_DIR}/.env"

# Make sure the data dir exists and the hermes user can write to it
mkdir -p "${DATA_DIR}"
if ! chown -R hermes:hermes "${DATA_DIR}" 2>/dev/null; then
  echo "[hermes-gemma] warning: could not chown ${DATA_DIR}; continuing" >&2
fi

# Always regenerate config.yaml to ensure WebSocket messaging is enabled
# This overwrites any stale config from previous deployments
echo "[hermes-gemma] Regenerating config.yaml with Gemma 4 31B IT + WebSocket messaging..."
cat > "${CONFIG_FILE}" << 'HERMES_CONFIG'
# Hermes Agent Configuration
# Model: Gemma 4 31B IT via Google AI Studio
model:
  default: gemini-4-31b-it
  provider: gemini

agent:
  default: Claude
  
  memory:
    enabled: true
    max_characters: 2200

# WebSocket messaging platform for dashboard chat connectivity
# This enables /api/ws, /api/events, /api/pty endpoints
messaging_platforms:
  websocket:
    enabled: true
    host: 0.0.0.0
    port: 10001
HERMES_CONFIG
chown hermes:hermes "${CONFIG_FILE}"
echo "[hermes-gemma] Config regenerated at ${CONFIG_FILE}"

# If no .env exists, create from example
if [ ! -f "${ENV_FILE}" ]; then
  echo "[hermes-gemma] No .env file found in ${DATA_DIR}"
  echo "[hermes-gemma] Create /opt/data/.env with your GOOGLE_API_KEY"
fi

# Hand off to the upstream entrypoint
exec /opt/hermes/docker/entrypoint.sh "$@"
