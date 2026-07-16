# Jupyter Notebook Server with Hermes Agent

A simple JupyterLab server you can deploy anywhere. Install the [Hermes Agent](https://github.com/NousResearch/hermes-agent) directly from Jupyter.

## Features

- 🚀 **JupyterLab** - Full-featured notebook environment
- 💾 **Persistent Storage** - Notebooks and packages survive restarts
- 🔧 **Install Hermes** - Directly from Jupyter using `!pip install --user`

## Deployment

### 1. Fork this Repository

### 2. Deploy to Your Platform

Deploy the Docker image and mount a volume at `/data` for persistence.

**SnapDeploy example:**
1. New Service → Connect GitHub → Select this repo
2. Name: `jupyter-hermes`
3. Port: `8888`
4. **Volume mount**: `/data` (preserves notebooks & packages)
5. Deploy

### 3. Access JupyterLab

1. Open `http://your-service:8888`
2. Get token from container logs if needed
3. Open `hermes.ipynb`

## Usage

### Install Hermes Agent

In any notebook cell:
```python
!pip install --user git+https://github.com/NousResearch/hermes-agent.git
```

### Use Hermes

```python
import sys
sys.path.insert(0, '/data/.local/lib/python3.11/site-packages')

from run_agent import AIAgent

agent = AIAgent(
    model="openai/gpt-4o",  # or any model you have API access to
    quiet_mode=True,
)

response = agent.chat("Hello!")
print(response)
```

## Persistence

| Path | Contents |
|------|----------|
| `/data/notebooks` | Your notebooks (auto-saved) |
| `/data/.local` | Installed Python packages |

**Important**: Use `!pip install --user` to make packages persist!

## File Structure

```
├── Dockerfile              # Docker image
├── notebooks/
│   └── hermes.ipynb       # Getting started notebook
└── README.md
```

## License

MIT - See [Hermes Agent](https://github.com/NousResearch/hermes-agent)
