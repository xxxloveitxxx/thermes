#!/usr/bin/env python3
"""
Jupyter Startup Script - Auto-run on kernel start

This runs automatically when you start a new notebook kernel.
It:
1. Pulls files from Supabase
2. Installs Hermes if not present
3. Sets up auto-save
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Supabase settings
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://opdpexsytsaldlworztz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
BUCKET_NAME = os.environ.get('SUPABASE_BUCKET', 'manini')

# Paths
WORKSPACE = '/workspace'
NOTEBOOKS_DIR = os.path.join(WORKSPACE, 'notebooks')
SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')
HERMES_HOME = os.path.expanduser('~/.hermes')


def log(msg):
    print(f"[Hermes Startup] {msg}")


def ensure_dirs():
    for d in [NOTEBOOKS_DIR, SCRIPTS_DIR, HERMES_HOME]:
        os.makedirs(d, exist_ok=True)
    log(f"Directories ready")


def install_supabase():
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        log("Installing supabase...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "supabase"], check=True)
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)


def install_hermes():
    """Install Hermes agent if not present."""
    hermes_path = os.path.join(HERMES_HOME, 'installed')
    
    if os.path.exists(hermes_path):
        log("Hermes already installed")
        return
    
    log("Installing Hermes Agent...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--break-system-packages",
            "git+https://github.com/NousResearch/hermes-agent.git"
        ], check=True, capture_output=True)
        
        # Mark as installed
        Path(hermes_path).touch()
        log("✓ Hermes installed!")
    except Exception as e:
        log(f"Error installing Hermes: {e}")


def pull_from_supabase(sb):
    """Download files from Supabase."""
    try:
        log("Pulling files from Supabase...")
        files = sb.storage.from_(BUCKET_NAME).list()
        
        pulled = 0
        for file in files:
            name = file.get('name', '')
            if not name or '/' not in name:
                continue
            
            folder, filename = name.split('/', 1)
            if folder not in ['notebooks', 'scripts', 'hermes'] or not filename:
                continue
            
            local_dir = os.path.join(WORKSPACE, folder) if folder != 'hermes' else HERMES_HOME
            local_path = os.path.join(local_dir, filename)
            
            try:
                data = sb.storage.from_(BUCKET_NAME).download(name)
                os.makedirs(local_dir, exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(data)
                pulled += 1
            except:
                pass
        
        log(f"✓ Pulled {pulled} files")
    except Exception as e:
        log(f"Pull error: {e}")


def setup_auto_save():
    """Install auto-save hook."""
    ipython_dir = os.path.expanduser('~/.ipython')
    profile_dir = os.path.join(ipython_dir, 'profile_default')
    startup_dir = os.path.join(profile_dir, 'startup')
    
    auto_save_script = '''#!/usr/bin/env python3
"""
Auto-save hook - runs after each notebook execution
"""

import os
import sys
import subprocess
from datetime import datetime

def auto_save():
    try:
        # Only save every 5 minutes
        save_file = '/tmp/last_auto_save'
        now = datetime.now().timestamp()
        
        if os.path.exists(save_file):
            last = os.path.getmtime(save_file)
            if now - last < 300:  # 5 minutes
                return
        
        # Run sync
        subprocess.Popen([
            sys.executable, '/workspace/scripts/sync.py', 'push'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        Path(save_file).touch()
    except:
        pass

# Register post-execute hook if IPython available
try:
    from IPython import get_ipython
    ip = get_ipython()
    if ip:
        ip.events.register('post_run_cell', auto_save)
except:
    pass
'''
    
    os.makedirs(startup_dir, exist_ok=True)
    with open(os.path.join(startup_dir, 'auto_save.py'), 'w') as f:
        f.write(auto_save_script)
    
    log("Auto-save hook installed")


def main():
    log("Starting...")
    ensure_dirs()
    
    # Pull from Supabase
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            sb = install_supabase()
            pull_from_supabase(sb)
        except Exception as e:
            log(f"Supabase error: {e}")
    
    # Install Hermes
    install_hermes()
    
    # Setup auto-save
    setup_auto_save()
    
    log("✓ Ready! Your files are synced.")


if __name__ == '__main__':
    main()
