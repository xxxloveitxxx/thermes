#!/bin/sh
# Runs the robust Python-based bootstrap process with signal handling and background sync
echo "Running Jupyter Notebook Server and Hermes Startup..."
exec python3 /workspace/scripts/bootstrap.py
