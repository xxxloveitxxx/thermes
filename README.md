# Jupyter Notebook Server with Hermes Agent

A simple JupyterLab server you can deploy anywhere. Install the [Hermes Agent](https://github.com/NousResearch/hermes-agent) directly from Jupyter.

## Features

- 🚀 **JupyterLab** - Full-featured notebook environment
- 💾 **Supabase Persistence** - Notebooks saved to Supabase Storage
- 🔧 **Install Hermes** - Directly from Jupyter

## Deployment

### 1. Fork this Repository

### 2. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up (free tier available)
2. Create a new project
3. Copy your **Project URL** and **anon public key** from Settings → API

### 3. Create a Storage Bucket

1. Go to **Storage** in your Supabase project
2. Click **New bucket**
3. Name it `notebooks`
4. Make it **Public**

### 4. Deploy to Render

1. New Service → Connect GitHub → Select this repo
2. Name: `jupyter-hermes`
3. Port: `8888`
4. Add Environment Variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase anon key
   - `SUPABASE_BUCKET`: `notebooks` (or your bucket name)
5. Deploy

### 5. Access JupyterLab

1. Open `http://your-service:8888`
2. Get token from Render logs
3. Open `hermes.ipynb`

## How Persistence Works

1. First run: Notebooks start in `/data/notebooks`
2. Work on notebooks as normal in JupyterLab
3. Run the **Upload Notebooks** cell to save to Supabase
4. On restart: Run **Download Notebooks** to get your work back

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
| 2 | Run the Supabase setup cell |
| 3 | Run **Download Notebooks** (pull from Supabase) |
| 4 | Install Hermes (one-time) |
| 5 | Do your work |
| 6 | Run **Upload Notebooks** to save to Supabase |
| 7 | On restart: Download again to continue |

## File Structure

```
├── Dockerfile              # Docker image
├── notebooks/
│   └── hermes.ipynb       # Getting started notebook
└── README.md
```

## License

MIT - See [Hermes Agent](https://github.com/NousResearch/hermes-agent)
