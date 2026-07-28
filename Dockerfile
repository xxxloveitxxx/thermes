# syntax=docker/dockerfile:1.7
#
# Jupyter Notebook Server with Hermes Agent
# Auto-syncs notebooks, scripts, and hermes config to Supabase
#
FROM python:3.11-slim

# Create workspace directories
RUN mkdir -p /workspace/notebooks /workspace/scripts

# Expose Jupyter port
EXPOSE 8888

# Install Jupyter and supabase
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && pip install --no-cache-dir jupyter jupyterlab supabase \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy scripts and bootstrap wrapper
COPY scripts/* /workspace/scripts/
RUN chmod +x /workspace/scripts/*

# Setup IPython startup (auto-runs on kernel start)
RUN mkdir -p /root/.ipython/profile_default/startup && \
    echo "import sys; sys.path.insert(0, '/workspace/scripts'); import startup; startup.main()" > /root/.ipython/profile_default/startup/00_hermes_startup.py

# Set workdir
WORKDIR /workspace

# Start with the robust bootstrap process (handles setup, auto-save, and shutdown signals)
CMD ["python", "/workspace/scripts/bootstrap.py"]
