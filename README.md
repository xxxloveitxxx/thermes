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

## ⚠️ IMPORTANT: Render Free Tier Limitations

**Render Free Plan has ephemeral storage!** This means:
- Your files are stored locally in `/workspace` which is **NOT persistent**
- If the container restarts, crashes, or Render spins it down → **all local files are LOST**
- The cronjob only keeps the instance alive but does NOT restore your files

### How to Prevent Data Loss

1. **Always run `save()` before closing** (see below)
2. **Use the save helper** for reliable saves with feedback
3. **Don't rely on auto-save alone** - it's a safety net, not a backup

## Usage

### Save Helper (Recommended)

Run this in a notebook cell for reliable saves:

```python
import sys
sys.path.insert(0, '/workspace/scripts')
from save_helper import save, load, status

status()  # Check if Supabase is configured
save()    # Save everything to Supabase
load()    # Load everything from Supabase
```

### Manual Sync

```python
!python /workspace/scripts/sync.py push   # Upload to Supabase
!python /workspace/scripts/sync.py pull   # Download from Supabase
```

Or from terminal:
```bash
python /workspace/scripts/save_helper.py save
python /workspace/scripts/save_helper.py load
python /workspace/scripts/save_helper.py status
```

## Auto-Save Behavior

- **Background daemon**: Pushes to Supabase every 5 minutes
- **Cell-run hook**: Triggers save after running notebook cells (every 2 min minimum)
- **Shutdown handler**: Final save on container stop

**Note**: Background saves use silent error handling. Use `save()` for verified saves.

## Troubleshooting

### Check logs
```bash
cat /tmp/auto_save.log    # Auto-save logs
cat /tmp/sync.log         # Manual sync logs (if configured)
```

### Check Supabase status
```python
from save_helper import status
status()
```

### Verify environment variables
```python
import os
print("SUPABASE_URL:", bool(os.environ.get('SUPABASE_URL')))
print("SUPABASE_KEY:", bool(os.environ.get('SUPABASE_KEY')))
```

## License

MIT
