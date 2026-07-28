#!/usr/bin/env python3
"""
Jupyter Startup Script - Auto-run on kernel start and boot

This runs automatically when you start a new notebook kernel or boot the container.
It:
1. Pulls files from Supabase (restores notebooks, scripts, config, and hermes state)
2. Installs Hermes if not present
3. Sets up IPython auto-save post-cell-execute hook
"""

import os
import sys
import subprocess
import shutil
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
    """Download files from Supabase using direct sync helper."""
    log("Pulling latest files and session state from Supabase...")
    try:
        sys.path.insert(0, SCRIPTS_DIR)
        import sync
        sync.pull_files()
        log("✓ Sync/pull completed.")
    except Exception as e:
        log(f"Pull error: {e}")


def setup_auto_save():
    """Install auto-save hook into IPython startup directory."""
    ipython_dir = os.path.expanduser('~/.ipython')
    profile_dir = os.path.join(ipython_dir, 'profile_default')
    startup_dir = os.path.join(profile_dir, 'startup')
    
    auto_save_script = f'''#!/usr/bin/env python3
"""
Auto-save hook - runs after each notebook execution
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def auto_save():
    try:
        # Only save every 5 minutes from the cell-run hook to avoid rate limits
        save_file = '/tmp/last_auto_save'
        now = datetime.now().timestamp()
        
        if os.path.exists(save_file):
            last = os.path.getmtime(save_file)
            if now - last < 300:  # 5 minutes
                return
        
        # Run sync push in background
        subprocess.Popen([
            sys.executable, '{SCRIPTS_DIR}/sync.py', 'push'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        Path(save_file).touch()
    except Exception:
        pass

# Register post-execute hook if IPython is available
try:
    from IPython import get_ipython
    ip = get_ipython()
    if ip:
        ip.events.register('post_run_cell', auto_save)
except Exception:
    pass
'''
    
    os.makedirs(startup_dir, exist_ok=True)
    with open(os.path.join(startup_dir, 'auto_save.py'), 'w') as f:
        f.write(auto_save_script)
    
    log("Auto-save cell-run hook installed")


def main():
    log("Starting...")
    ensure_dirs()
    
    # Pull from Supabase
    pull_from_supabase()
    
    # Install Hermes
    install_hermes()
    
    # Setup auto-save
    setup_auto_save()
    
    log("✓ Ready! Your files are fully synced.")


if __name__ == '__main__':
    main()
