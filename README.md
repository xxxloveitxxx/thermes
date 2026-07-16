# Jupyter Notebook Server with Hermes Agent

A simple JupyterLab server you can deploy anywhere. Install the [Hermes Agent](https://github.com/NousResearch/hermes-agent) directly from Jupyter.

## Features

- 🚀 **JupyterLab** - Full-featured notebook environment
- 💾 **Git-Based Persistence** - Notebooks saved to GitHub
- 🔧 **Install Hermes** - Directly from Jupyter

## Deployment

### 1. Fork this Repository

### 2. Create a GitHub Repo for Your Notebooks

Create a new **empty** private repo on GitHub (e.g., `my-jupyter-notebooks`).

### 3. Generate a GitHub Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scope: `repo` (full control)
4. Copy the token

### 4. Deploy to Render

1. New Service → Connect GitHub → Select this repo
2. Name: `jupyter-hermes`
3. Port: `8888`
4. Add Environment Variables:
   - `GIT_REPO_URL`: `https://YOUR_TOKEN@github.com/YOUR_USERNAME/my-jupyter-notebooks.git`
   - `GIT_NAME`: `Jupyter Hermes`
   - `GIT_EMAIL`: `your@email.com`
5. Deploy

### 5. Access JupyterLab

1. Open `http://your-service:8888`
2. Get token from Render logs
3. Open `hermes.ipynb`

## How Git Persistence Works

1. First run: The notebook clones your GitHub repo into `/data/notebooks`
2. Work on notebooks as normal in JupyterLab
3. Run the **Save & Sync** cell to push changes to GitHub
4. On restart: Run **Pull Latest** to get your notebooks back

## Usage

### Install Hermes Agent

```python
!pip install --break-system-packages git+https://github.com/NousResearch/hermes-agent.git
```

### Use Hermes

```python
from run_agent import AIAgent

agent = AIAgent(
    model="openai/gpt-4o",  # or your preferred model
    quiet_mode=True,
)

response = agent.chat("Hello!")
print(response)
```

## Workflow

| Step | Action |
|------|--------|
| 1 | Open hermes.ipynb |
| 2 | Run first cell (Git setup) |
| 3 | Install Hermes (one-time) |
| 4 | Do your work |
| 5 | Run **Save & Sync** cell to push to GitHub |
| 6 | On restart: Run **Pull Latest**, then continue |

## File Structure

```
├── Dockerfile              # Docker image
├── notebooks/
│   └── hermes.ipynb       # Getting started notebook
└── README.md
```

## License

MIT - See [Hermes Agent](https://github.com/NousResearch/hermes-agent)
