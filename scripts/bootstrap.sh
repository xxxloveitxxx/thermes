#!/bin/sh
# Entrypoint wrapper for Hermes on Render with Gemma support.
#
# Runs as root (PID-1 child of tini). On every boot it:
#   1. Ensures /opt/data exists and is owned by hermes:hermes.
#   2. Copies default config.yaml with Gemma model settings if not present.
#   3. Loads .env from /opt/data/.env if it exists.
#   4. For Jupyter mode (HERMES_JUPYTER=1): starts JupyterLab.
#   5. Otherwise: exec's the upstream entrypoint chain.

set -eu

DATA_DIR="${HERMES_HOME:-/opt/data}"
CONFIG_FILE="${DATA_DIR}/config.yaml"
ENV_FILE="${DATA_DIR}/.env"
JUPYTER_DIR="${DATA_DIR}/.jupyter"

# Make sure the data dir exists and the hermes user can write to it
mkdir -p "${DATA_DIR}"
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

# If no .env exists, create from example
if [ ! -f "${ENV_FILE}" ]; then
  echo "[hermes-gemma] No .env file found in ${DATA_DIR}"
  echo "[hermes-gemma] Create /opt/data/.env with your GOOGLE_API_KEY"
fi

# Load .env into environment if it exists
if [ -f "${ENV_FILE}" ]; then
  set -a
  . "${ENV_FILE}"
  set +a
fi

# Check if Jupyter mode is enabled
if [ "${HERMES_JUPYTER:-0}" = "1" ]; then
  echo "[hermes-gemma] Jupyter mode enabled - starting JupyterLab..."
  
  # Disable dashboard for Jupyter mode
  export HERMES_DASHBOARD=0
  
  # Create Jupyter config directory
  mkdir -p "${JUPYTER_DIR}"
  chown hermes:hermes "${JUPYTER_DIR}"
  
  # Generate Jupyter config if needed
  if [ ! -f "${JUPYTER_DIR}/jupyter_lab_config.py" ]; then
    su hermes -c "jupyter lab --generate-config -y" 2>/dev/null || true
    if [ -f "/home/hermes/.jupyter/jupyter_lab_config.py" ]; then
      mv /home/hermes/.jupyter/jupyter_lab_config.py "${JUPYTER_DIR}/"
      chown hermes:hermes "${JUPYTER_DIR}/jupyter_lab_config.py"
    fi
  fi
  
  # Set Jupyter to listen on all interfaces
  export JUPYTER_TOKEN="${JUPYTER_TOKEN:-hermes-jupyter-token}"
  
  # Copy notebooks to data dir for persistence
  if [ -d /opt/hermes-notebooks ]; then
    cp -r /opt/hermes-notebooks/* "${DATA_DIR}/notebooks/" 2>/dev/null || \
      mkdir -p "${DATA_DIR}/notebooks" && cp -r /opt/hermes-notebooks/* "${DATA_DIR}/notebooks/"
    chown -R hermes:hermes "${DATA_DIR}/notebooks"
  fi
  
  echo "[hermes-gemma] Starting JupyterLab server..."
  echo "[hermes-gemma] Access token: ${JUPYTER_TOKEN}"
  echo "[hermes-gemma] Notebooks directory: ${DATA_DIR}/notebooks"
  
  # Start JupyterLab as hermes user
  exec su hermes -c "cd ${DATA_DIR} && jupyter lab \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --NotebookApp.token='${JUPYTER_TOKEN}' \
    --NotebookApp.allow_origin='*' \
    --NotebookApp.disable_check_xsrf=True \
    --ServerApp.root_dir='${DATA_DIR}/notebooks' \
    2>&1"
fi

# Hand off to the upstream entrypoint (dashboard mode)
exec /opt/hermes/docker/entrypoint.sh "$@"
