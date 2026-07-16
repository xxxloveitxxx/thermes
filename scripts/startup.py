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
import requests
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
            "hermes-agent"
        ], check=True, capture_output=True, timeout=300)
        
        Path(hermes_path).touch()
        log("✓ Hermes installed!")
    except Exception as e:
        log(f"Error installing Hermes: {e}")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "--break-system-packages",
                "--no-cache-dir",
                "hermes-agent"
            ], check=True, capture_output=True, timeout=300)
            Path(hermes_path).touch()
            log("✓ Hermes installed (alt)!")
        except Exception as e2:
            log(f"Alt install failed: {e2}")


def pull_from_supabase():
    """Download files from Supabase using direct HTTP."""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        
        folders = {'notebooks': NOTEBOOKS_DIR, 'scripts': SCRIPTS_DIR, 'hermes': HERMES_HOME}
        
        pulled = 0
        for folder, local_dir in folders.items():
            # List files with prefix
            url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
            resp = requests.post(url, headers=headers, json={'prefix': folder})
            
            if resp.status_code != 200:
                continue
            
            files = resp.json()
            if not files:
                continue
            
            for f in files:
                name = f.get('name', '')
                if not name or name.endswith('/'):
                    continue
                
                filename = name[len(folder) + 1:]
                if '/' in filename:
                    continue
                
                if filename == '.emptyFolderPlaceholder':
                    continue
                
                # Download file
                download_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{name}"
                download_resp = requests.get(download_url, headers=headers)
                
                if download_resp.status_code == 200:
                    local_path = os.path.join(local_dir, filename)
                    os.makedirs(local_dir, exist_ok=True)
                    with open(local_path, 'wb') as out:
                        out.write(download_resp.content)
                    pulled += 1
        
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
        pull_from_supabase()
    
    # Install Hermes
    install_hermes()
    
    # Setup auto-save
    setup_auto_save()
    
    log("✓ Ready! Your files are synced.")


if __name__ == '__main__':
    main()
