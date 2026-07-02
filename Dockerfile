# syntax=docker/dockerfile:1.7
#
# Hermes Agent on Render with Google AI Studio (Gemma 4 31B IT)
#
# Extends the upstream NousResearch/hermes-agent image with:
#   - Google AI Studio / Gemini API integration via LiteLLM
#   - Render persistent disk support for state survival
#   - Optional Render MCP server integration
#
# Pin the upstream tag here. Bump and redeploy to upgrade Hermes.
ARG HERMES_IMAGE=docker.io/nousresearch/hermes-agent:v2026.5.7
FROM ${HERMES_IMAGE}

# Workarounds for upstream issues that prevent the dashboard's Chat tab
# from connecting on hosted deploys.
USER root
RUN chown -R hermes:hermes /opt/hermes/ui-tui /opt/hermes/node_modules \
 && mkdir -p /opt/hermes/ui-tui/packages/hermes-ink/dist /opt/hermes/ui-tui/dist \
 && touch /opt/hermes/ui-tui/packages/hermes-ink/dist/ink-bundle.js \
          /opt/hermes/ui-tui/dist/entry.js \
 && chown -R hermes:hermes /opt/hermes/ui-tui

# Optional: Pull the official Render skill bundle from github.com/render-oss/skills
# (uncomment if you want Render MCP server integration)
# ARG RENDER_SKILLS_REPO=render-oss/skills
# ARG RENDER_SKILLS_REF=1b8496570748203351f628b2ae738805ac2c23d5
# RUN set -eu; \
#     tmp="$(mktemp -d)"; \
#     url="https://codeload.github.com/${RENDER_SKILLS_REPO}/tar.gz/${RENDER_SKILLS_REF}"; \
#     curl -fsSL --retry 3 -o "${tmp}/skills.tar.gz" "${url}"; \
#     tar -xzf "${tmp}/skills.tar.gz" -C "${tmp}"; \
#     extracted="$(find "${tmp}" -maxdepth 2 -type d -name 'skills' | head -n 1)"; \
#     test -n "${extracted}" || { echo "could not find skills/ in tarball" >&2; exit 1; }; \
#     install -d -o hermes -g hermes -m 0755 /opt/render-tools/skills-upstream; \
#     cp -a "${extracted}/." /opt/render-tools/skills-upstream/; \
#     chown -R hermes:hermes /opt/render-tools/skills-upstream; \
#     rm -rf "${tmp}"

# Boot-time wrapper: patches config.yaml with Gemma model settings, then hands off
COPY --chown=root:root scripts/bootstrap.sh /opt/render-tools/bootstrap.sh
RUN chmod 0755 /opt/render-tools/bootstrap.sh

# Pre-create the data dir for persistent storage
RUN install -d -o hermes -g hermes -m 0755 /opt/data

# Stay as root so bootstrap can chown mounted /opt/data, then exec upstream entrypoint
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/opt/render-tools/bootstrap.sh"]
CMD ["gateway", "run"]
