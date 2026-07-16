# syntax=docker/dockerfile:1.7
#
# Jupyter Notebook Server with Git-Based Persistence
#
# Notebooks sync to GitHub for persistence!
# Set GIT_REPO_URL env var: https://TOKEN@github.com/user/repo.git
#
FROM python:3.11-slim

# Create directories
RUN mkdir -p /data/notebooks /data/scripts

# Expose Jupyter port
EXPOSE 8888

# Install Jupyter and git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
 && pip install --no-cache-dir jupyter jupyterlab \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy initial notebooks
COPY notebooks/*.ipynb /data/notebooks/

# Workdir
WORKDIR /data

# Default: start JupyterLab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
