# syntax=docker/dockerfile:1.7
#
# Jupyter Notebook Server
#
# Install hermes-agent manually from Jupyter with:
# !pip install git+https://github.com/NousResearch/hermes-agent.git
#
FROM python:3.11-slim

# Expose Jupyter port
EXPOSE 8888

# Install Jupyter
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
 && npm install -g ijavascript \
 && pip install --no-cache-dir jupyter jupyterlab \
 && jupyter nbextension enable --py widgetsnbextension \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install IRkernel for R support (optional)
RUN pip install --no-cache-dir irkernel

# Copy notebooks
WORKDIR /workspace
COPY notebooks/ /workspace/

# Default: start JupyterLab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
