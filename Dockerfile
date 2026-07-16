# syntax=docker/dockerfile:1.7
#
# Hermes Agent on SnapDeploy with Google AI Studio (Gemma 4 31B IT)
#
# Extends the upstream NousResearch/hermes-agent image with:
#   - Google AI Studio / Gemini API integration via LiteLLM
#   - Persistent disk support for state survival
#   - Dashboard on port 10000 (default)
#   - Jupyter notebook server (when HERMES_JUPYTER=1)
#
# Pin the upstream tag here. Bump and redeploy to upgrade Hermes.
ARG HERMES_IMAGE=docker.io/nousresearch/hermes-agent:v2026.5.7
FROM ${HERMES_IMAGE}

# Expose the dashboard port
EXPOSE 10000
# Expose Jupyter port
EXPOSE 8888

# Default: start dashboard (HERMES_JUPYTER=1 disables dashboard and starts Jupyter)
ENV HERMES_JUPYTER=0
ENV HERMES_DASHBOARD=1
ENV HERMES_DASHBOARD_HOST=0.0.0.0
ENV HERMES_DASHBOARD_PORT=10000
ENV HERMES_DASHBOARD_TUI=1
# Allow open access (change for production)
ENV GATEWAY_ALLOW_ALL_USERS=true

# Install pip and Jupyter for notebook mode
USER root
RUN apt-get update && apt-get install -y python3-pip --no-install-recommends \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && pip3 install --no-cache-dir --break-system-packages jupyter jupyterlab ipywidgets

# Workarounds for upstream issues that prevent the dashboard's Chat tab
# from connecting on hosted deploys.
RUN chown -R hermes:hermes /opt/hermes/ui-tui /opt/hermes/node_modules \
 && mkdir -p /opt/hermes/ui-tui/packages/hermes-ink/dist /opt/hermes/ui-tui/dist \
 && touch /opt/hermes/ui-tui/packages/hermes-ink/dist/ink-bundle.js \
          /opt/hermes/ui-tui/dist/entry.js \
 && chown -R hermes:hermes /opt/hermes/ui-tui

# Boot-time wrapper: patches config.yaml with Gemma model settings, then hands off
COPY --chown=root:root scripts/bootstrap.sh /opt/render-tools/bootstrap.sh
COPY --chown=hermes:hermes notebooks /opt/hermes-notebooks
RUN chmod 0755 /opt/render-tools/bootstrap.sh

# Pre-create the data dir for persistent storage
RUN install -d -o hermes -g hermes -m 0755 /opt/data

# Stay as root so bootstrap can chown mounted /opt/data, then exec upstream entrypoint
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/opt/render-tools/bootstrap.sh"]
CMD ["gateway", "run"]
