#!/usr/bin/env python3
"""
Jupyter Startup Script - Auto-run on kernel start and boot

This runs automatically when you start a new notebook kernel or boot the container.
It:
1. Pulls files from Supabase (restores notebooks, scripts, config, and hermes state)
2. Installs Hermes if not present
3. Sets up aggressive auto-save (every 30 seconds + after each cell)
"""

import os
import sys
import subprocess
import shutil
import threading
import time
from pathlib import Path

# Paths
if os.path.exists('/workspace') and os.access('/workspace', os.W_OK):
    WORKSPACE = '/workspace'
elif os.path.exists('/app') and os.access('/app', os.W_OK):
    WORKSPACE = '/app'
else:
    WORKSPACE = os.getcwd()

NOTEBOOKS_DIR = os.path.join(WORKSPACE, 'notebooks')
SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')
HERMES_HOME = os.path.expanduser('~/.hermes')
LAST_SAVE_FILE = '/tmp/last_save_time'
SAVE_LOCK_FILE = '/tmp/save_in_progress'


def log(msg):
    print(f"[Hermes Startup] {msg}", flush=True)


def ensure_dirs():
    for d in [NOTEBOOKS_DIR, SCRIPTS_DIR, HERMES_HOME]:
        os.makedirs(d, exist_ok=True)
    log("Directories ready")


def install_hermes():
    """Install Hermes agent if not present in the current container environment."""
    if shutil.which('hermes') is not None:
        log("Hermes is already installed and available in PATH.")
        return
    
    log("Hermes not detected. Installing Hermes Agent...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--break-system-packages",
            "hermes-agent"
        ], check=True, capture_output=True, timeout=300)
        log("✓ Hermes installed successfully!")
    except Exception as e:
        log(f"Error installing Hermes: {e}")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "--break-system-packages",
                "--no-cache-dir",
                "hermes-agent"
            ], check=True, capture_output=True, timeout=300)
            log("✓ Hermes installed successfully (alternative method)!")
        except Exception as e2:
            log(f"Alternative install failed: {e2}")


def pull_from_supabase():
    """Download files from Supabase - ALWAYS runs on startup."""
    log("📥 Pulling files from Supabase...")
    try:
        sys.path.insert(0, SCRIPTS_DIR)
        import sync
        
        # Check credentials first
        if not sync.SUPABASE_URL or not sync.SUPABASE_KEY:
            log("❌ SUPABASE credentials not set! Cannot pull.")
            log(f"   URL: {sync.SUPABASE_URL}")
            log(f"   KEY: {'SET' if sync.SUPABASE_KEY else 'NOT SET'}")
            return
        
        log(f"   Supabase URL: {sync.SUPABASE_URL[:40]}...")
        log(f"   Bucket: {sync.BUCKET_NAME}")
        
        sync.pull_files()
        log("✓ Files restored from Supabase.")
    except Exception as e:
        log(f"Pull error: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")


def do_save():
    """Perform the actual save to Supabase."""
    # Prevent overlapping saves
    if os.path.exists(SAVE_LOCK_FILE):
        return False
        
    try:
        # Create lock
        Path(SAVE_LOCK_FILE).touch()
        
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, 'sync.py'), 'push'],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result.returncode == 0:
            log("💾 Auto-saved to Supabase")
            return True
        else:
            log(f"✗ Save failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log("✗ Save timed out")
        return False
    except Exception as e:
        log(f"✗ Save error: {e}")
        return False
    finally:
        # Remove lock
        if os.path.exists(SAVE_LOCK_FILE):
            os.remove(SAVE_LOCK_FILE)


def auto_save():
    """Trigger save with rate limiting (30 second minimum between saves)."""
    try:
        now = time.time()
        
        # Rate limit: only save if 30+ seconds since last save
        if os.path.exists(LAST_SAVE_FILE):
            last = float(open(LAST_SAVE_FILE).read().strip() or 0)
            if now - last < 30:
                return
        
        do_save()
        Path(LAST_SAVE_FILE).write_text(str(now))
        
    except Exception as e:
        log(f"Auto-save error: {e}")


def start_timer_save():
    """Start a background thread that saves every 30 seconds."""
    def timer_loop():
        while True:
            time.sleep(30)
            auto_save()
    
    t = threading.Thread(target=timer_loop, daemon=True)
    t.start()
    log("⏱️ Timer save thread started (every 30 seconds)")


def setup_auto_save():
    """Install auto-save hook into IPython startup directory."""
    ipython_dir = os.path.expanduser('~/.ipython')
    profile_dir = os.path.join(ipython_dir, 'profile_default')
    startup_dir = os.path.join(profile_dir, 'startup')
    
    # The actual auto-save script that gets installed
    auto_save_script = '''
import os
import sys
import subprocess
import time
import threading
from pathlib import Path

SCRIPTS_DIR = '/workspace/scripts'
if not os.path.exists(SCRIPTS_DIR) or not os.access(SCRIPTS_DIR, os.W_OK):
    SCRIPTS_DIR = '/app/scripts'

LAST_SAVE_FILE = '/tmp/last_save_time'
SAVE_LOCK_FILE = '/tmp/save_in_progress'

def do_save():
    if os.path.exists(SAVE_LOCK_FILE):
        return
    try:
        Path(SAVE_LOCK_FILE).touch()
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, 'sync.py'), 'push'],
            capture_output=True, timeout=90
        )
        if result.returncode == 0:
            print("💾 Auto-saved", flush=True)
        if os.path.exists(SAVE_LOCK_FILE):
            os.remove(SAVE_LOCK_FILE)
    except:
        if os.path.exists(SAVE_LOCK_FILE):
            os.remove(SAVE_LOCK_FILE)

def auto_save():
    try:
        now = time.time()
        if os.path.exists(LAST_SAVE_FILE):
            last = float(open(LAST_SAVE_FILE).read().strip() or 0)
            if now - last < 30:
                return
        do_save()
        Path(LAST_SAVE_FILE).write_text(str(now))
    except:
        pass

# Start timer save thread - saves every 30 seconds
def timer_loop():
    while True:
        time.sleep(30)
        auto_save()

t = threading.Thread(target=timer_loop, daemon=True)
t.start()

# Register post-cell hook - saves after each cell execution
try:
    from IPython import get_ipython
    ip = get_ipython()
    if ip:
        ip.events.register('post_run_cell', auto_save)
except:
    pass
'''
    
    os.makedirs(startup_dir, exist_ok=True)
    with open(os.path.join(startup_dir, '00_auto_save.py'), 'w') as f:
        f.write(auto_save_script)
    
    log("✅ Auto-save system installed")


def main():
    log("🚀 Initializing Hermès...")
    log(f"📁 Workspace: {WORKSPACE}")
    log(f"📁 Notebooks: {NOTEBOOKS_DIR}")
    log(f"📁 Scripts: {SCRIPTS_DIR}")
    ensure_dirs()
    
    # ALWAYS pull on startup - this restores your files
    pull_from_supabase()
    
    # Install Hermes
    install_hermes()
    
    # Setup aggressive auto-save
    setup_auto_save()
    start_timer_save()
    
    # Verify files are there
    notebooks_files = os.listdir(NOTEBOOKS_DIR) if os.path.exists(NOTEBOOKS_DIR) else []
    log(f"📂 Found {len(notebooks_files)} notebooks in workspace")
    
    if notebooks_files:
        for f in notebooks_files[:5]:
            log(f"   - {f}")
    
    log("✅ Ready! Auto-saving every 30 seconds.")


if __name__ == '__main__':
    main()
