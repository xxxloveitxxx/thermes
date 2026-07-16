# Jupyter + Hermes Agent with Auto-Sync

JupyterLab that auto-syncs notebooks, scripts, and Hermes config to Supabase.

## Features

- 🚀 **JupyterLab** - Full notebook environment
- 💾 **Auto-Sync** - Files sync to Supabase automatically
- 🤖 **Hermes** - Auto-installed and configured
- 📁 **Two folders**: `notebooks/` and `scripts/`

## Setup

### 1. Create Supabase Bucket

1. Go to [supabase.com](https://supabase.com) → Your project → Storage
2. Create bucket named `manini` (or your choice)
3. Add RLS policies (run in SQL Editor):

```sql
CREATE POLICY "public_select" ON storage.objects FOR SELECT TO PUBLIC USING (bucket_id = 'manini');
CREATE POLICY "public_insert" ON storage.objects FOR INSERT TO PUBLIC WITH CHECK (bucket_id = 'manini');
CREATE POLICY "public_update" ON storage.objects FOR UPDATE TO PUBLIC USING (bucket_id = 'manini') WITH CHECK (bucket_id = 'manini');
```

### 2. Deploy

Environment Variables:
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_BUCKET=manini
```

### 3. That's It!

When you open a notebook, it automatically:
- Pulls files from Supabase
- Installs Hermes if needed
- Sets up auto-save

## Manual Sync

In a notebook cell:
```python
!python /workspace/scripts/sync.py push   # Upload to Supabase
!python /workspace/scripts/sync.py pull   # Download from Supabase
```

## File Structure

```
/workspace/
├── notebooks/      # Your .ipynb files (auto-synced)
├── scripts/        # Python scripts (auto-synced)
└── ~/.hermes/     # Hermes config & memory (auto-synced)
```

## Hermes Usage

```python
from run_agent import AIAgent

agent = AIAgent(
    model="openai/gpt-4o",
    quiet_mode=True,
)

response = agent.chat("Hello!")
print(response)
```

## License

MIT
