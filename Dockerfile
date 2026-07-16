# syntax=docker/dockerfile:1.7
#
# Jupyter Notebook Server with Supabase Persistence
#
# Notebooks sync to Supabase Storage!
# Set SUPABASE_URL and SUPABASE_KEY env vars
#
FROM python:3.11-slim

# Create directories
RUN mkdir -p /data/notebooks /data/scripts

# Expose Jupyter port
EXPOSE 8888

# Install Jupyter and supabase
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && pip install --no-cache-dir jupyter jupyterlab supabase \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy initial notebooks
COPY notebooks/*.ipynb /data/notebooks/

# Workdir
WORKDIR /data

# Default: start JupyterLab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
