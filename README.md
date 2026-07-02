# Hermes Agent on Render with Google AI Studio (Gemma 4 31B IT)

Deploy the [Hermes Agent](https://github.com/NousResearch/hermes-agent) on Render's free tier with Google AI Studio API and the Gemma 4 31B IT model.

## Features

- 🚀 **One-click deployment** to Render
- 🤖 **Gemma 4 31B IT** via Google AI Studio (Gemini API)
- 💾 **Persistent storage** support (with paid plan) or ephemeral (free tier)
- 🎛️ **Web Dashboard** with in-browser TUI chat
- 🔧 **Extensible skills** system
- 🔒 **Secure API key management**

## Prerequisites

1. **Google AI Studio Account**: https://aistudio.google.com/
2. **Render Account**: https://render.com/
3. **Google AI Studio API Key**: https://aistudio.google.com/app/apikey

## Quick Start

### 1. Fork this Repository

Fork this repository to your GitHub account.

### 2. Get Google AI Studio API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key" in the sidebar
3. Create a new API key or use an existing one
4. **Important**: Note your API key (you won't be able to see it again)

### 3. Deploy to Render

#### Option A: Deploy via Render Blueprint

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Blueprint"
3. Connect your GitHub account and select this repository
4. Render will automatically detect `render.yaml`
5. Add your environment variables:
   - `GOOGLE_API_KEY`: Your Google AI Studio API key
6. Click "Apply"

#### Option B: Deploy Manually

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `hermes-gemma`
   - **Region**: Oregon (or closest to you)
   - **Runtime**: Docker
   - **Dockerfile Path**: `Dockerfile`
   - **Plan**: Free
5. Add Environment Variables:
   - `HERMES_DASHBOARD`: `1`
   - `HERMES_DASHBOARD_HOST`: `0.0.0.0`
   - `HERMES_DASHBOARD_PORT`: `10000`
   - `HERMES_DASHBOARD_TUI`: `1`
   - `HERMES_GATEWAY_TOKEN`: (Generate a secure random value)
   - `GOOGLE_API_KEY`: (Your Google AI Studio API key)
6. Click "Create Web Service"

### 4. Access the Dashboard

After deployment completes:

1. Click on your service in Render Dashboard
2. Find the public URL (e.g., `https://hermes-gemma.onrender.com`)
3. Open the URL in your browser
4. Enter your `HERMES_GATEWAY_TOKEN` when prompted
5. Start chatting with Hermes!

## Configuration

### Model Settings

The default configuration uses Gemma 4 31B IT. You can customize by editing `config.yaml`:

```yaml
model:
  default: gemini-4-31b-it
  provider: gemini
```

### Alternative Gemma Models

Google AI Studio offers various Gemma models:

| Model | Description |
|-------|-------------|
| `gemini-4-31b-it` | Gemma 4 31B Instruction Tuned |
| `gemini-2.0-flash` | Gemini 2.0 Flash (faster) |
| `gemini-2.0-flash-lite` | Gemini 2.0 Flash Lite (cheapest) |
| `gemini-1.5-pro` | Gemini 1.5 Pro (larger context) |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google AI Studio API key |
| `HERMES_DASHBOARD` | No | Enable dashboard (default: 1) |
| `HERMES_DASHBOARD_HOST` | No | Dashboard bind host (default: 0.0.0.0) |
| `HERMES_DASHBOARD_PORT` | No | Dashboard port (default: 10000) |
| `HERMES_DASHBOARD_TUI` | No | Enable TUI chat (default: 1) |
| `HERMES_GATEWAY_TOKEN` | Yes | Gateway authentication token |

## Render Free Tier Limitations

| Limitation | Free Tier |
|------------|-----------|
| Instance hours | 750/month |
| Idle timeout | 15 minutes |
| Persistent disk | ❌ Not available |
| Cold start | 30-60 seconds |
| RAM | 512 MB |
| CPU | 0.5 vCPU |

### Tips for Free Tier

1. **Cold starts**: Be patient on first request (30-60s)
2. **Memory persistence**: State resets on spin-down (upgrade for persistence)
3. **Usage monitoring**: Keep an eye on monthly hours
4. **API quotas**: Google AI Studio has its own rate limits

## File Structure

```
hermes-render-gemma/
├── Dockerfile              # Docker image definition
├── render.yaml             # Render Blueprint configuration
├── config.yaml             # Hermes agent configuration
├── .env.example            # Environment variables template
├── README.md               # This file
├── .gitignore              # Git ignore rules
└── scripts/
    └── bootstrap.sh        # Container startup script
    └── skills/
        └── render-on-hermes/
            ├── skill.md    # Skill documentation
            └── skill.json  # Skill manifest
```

## Troubleshooting

### Dashboard shows 401/403 errors

1. Verify `HERMES_GATEWAY_TOKEN` is set correctly
2. Clear browser cache and refresh
3. Check browser console for CORS errors

### "Model not found" errors

1. Verify `GOOGLE_API_KEY` is correct
2. Check Google AI Studio has Gemma 4 enabled
3. Verify model name matches available models

### Service won't start

1. Check Render logs for errors
2. Verify Docker build succeeds locally
3. Ensure all environment variables are set

### Cold start timeout

Free tier services spin down after 15 minutes. Options:
- Use a uptime monitor to ping the service
- Upgrade to paid plan for always-on instance
- Accept 30-60s cold starts

## Upgrading

### Update Hermes Version

Edit `Dockerfile` and change `HERMES_IMAGE`:

```dockerfile
ARG HERMES_IMAGE=docker.io/nousresearch/hermes-agent:v2026.5.7
```

Check for new releases at: https://github.com/NousResearch/hermes-agent/releases

### Update Render Skills

Uncomment the skills section in `Dockerfile` and update `RENDER_SKILLS_REF` to a newer commit.

## Security Best Practices

1. **Never commit API keys** to version control
2. Use Render's secret storage for sensitive values
3. Rotate API keys periodically
4. Use least-privilege API keys
5. Enable 2FA on both Google and Render accounts

## License

MIT License - See [Hermes Agent](https://github.com/NousResearch/hermes-agent) for original project license.

## Resources

- [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/)
- [Google AI Studio](https://aistudio.google.com/)
- [Render Documentation](https://render.com/docs)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
