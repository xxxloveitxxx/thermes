#!/bin/sh
# Entrypoint wrapper for Hermes on SnapDeploy with Gemma support.
#
# Runs as root (PID-1 child of tini). On every boot it:
#   1. Ensures /opt/data exists and is owned by hermes:hermes.
#   2. Creates config.yaml with Gemma model settings if not present.
#   3. Generates HERMES_GATEWAY_TOKEN if not set.
#   4. Loads .env from /opt/data/.env if it exists.
#   5. Exec's the upstream entrypoint chain.

set -eu

DATA_DIR="${HERMES_HOME:-/opt/data}"
CONFIG_FILE="${DATA_DIR}/config.yaml"
ENV_FILE="${DATA_DIR}/.env"
HERMES_DIR="${DATA_DIR}/.hermes"

# Make sure the data dir exists and the hermes user can write to it
mkdir -p "${DATA_DIR}" "${HERMES_DIR}"
if ! chown -R hermes:hermes "${DATA_DIR}" 2>/dev/null; then
  echo "[hermes-gemma] warning: could not chown ${DATA_DIR}; continuing" >&2
fi

# If no config.yaml exists, create one with Gemma 4 31B IT settings
if [ ! -f "${CONFIG_FILE}" ]; then
  echo "[hermes-gemma] Creating default config.yaml with Gemma 4 31B IT settings..."
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
HERMES_CONFIG
  chown hermes:hermes "${CONFIG_FILE}"
  echo "[hermes-gemma] Config created at ${CONFIG_FILE}"
fi

# Generate HERMES_GATEWAY_TOKEN if not set
if [ -z "${HERMES_GATEWAY_TOKEN:-}" ]; then
  export HERMES_GATEWAY_TOKEN=$(head -c 32 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 32)
  echo "[hermes-gemma] Generated HERMES_GATEWAY_TOKEN"
fi

# Create .hermes/.env with gateway token
if [ ! -f "${HERMES_DIR}/.env" ]; then
  echo "[hermes-gemma] Creating ${HERMES_DIR}/.env..."
  cat > "${HERMES_DIR}/.env" << EOF
HERMES_GATEWAY_TOKEN=${HERMES_GATEWAY_TOKEN}
EOF
  chown hermes:hermes "${HERMES_DIR}/.env"
fi

# Allow open access
export GATEWAY_ALLOW_ALL_USERS=true

echo "[hermes-gemma] Starting Hermes Gateway..."

# Hand off to the upstream entrypoint
exec /opt/hermes/docker/entrypoint.sh "$@"
