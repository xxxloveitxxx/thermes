# syntax=docker/dockerfile:1.7
#
# Jupyter Notebook Server with Persistent Storage
#
# Volume mounts for persistence:
#   /data     - Notebooks, scripts, installed packages
#   /root/.local - Python packages
#
# Install hermes-agent manually from Jupyter with:
# !pip install git+https://github.com/NousResearch/hermes-agent.git
#
FROM python:3.11-slim

# Create persistent directories
RUN mkdir -p /data/notebooks /data/scripts

# Expose Jupyter port
EXPOSE 8888

# Install Jupyter
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
 && pip install --no-cache-dir jupyter jupyterlab \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy initial notebooks to persistent storage
COPY notebooks/*.ipynb /data/notebooks/

# Set environment for persistent package storage
ENV PYTHONUSERBASE=/data/.local

# Workdir
WORKDIR /data

# Default: start JupyterLab with persistent storage
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.notebook_dir=/data/notebooks"]
