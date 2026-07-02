# Render on Hermes Skill

This skill provides integration with Render's MCP (Model Context Protocol) server, allowing Hermes to interact with your Render account resources.

## Purpose

When this skill is installed, Hermes can:
- List your Render services
- View service metrics
- Fetch service logs
- Manage deployments

## Setup

### Prerequisites

1. **Render API Key**: Generate an API key at:
   https://dashboard.render.com/u/*/settings#api-keys

2. **Set the API Key**: Add to your `/opt/data/.env` file:
   ```
   RENDER_MCP_API_KEY=your_render_api_key_here
   ```

   Or set via Render Dashboard > Environment tab.

### How It Works

The MCP server is registered in `config.yaml` automatically during boot:

```yaml
mcp_servers:
  render:
    url: https://mcp.render.com/mcp
    headers:
      Authorization: Bearer ${RENDER_MCP_API_KEY}
```

## Usage

Once configured, you can ask Hermes to:

- "List all my Render services"
- "Show me the metrics for my web service"
- "Get the recent logs from production"
- "Check the status of my latest deployment"

## Security Notes

- The Render API key provides full access to your Render account
- Treat it like any other sensitive credential
- Rotate keys regularly via Render Dashboard
- Never commit API keys to version control

## Troubleshooting

If Hermes cannot connect to Render MCP:
1. Verify `RENDER_MCP_API_KEY` is set correctly
2. Check your Render account has active services
3. Ensure the Render API key has not expired
4. Restart the service after updating the key
