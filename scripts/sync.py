#!/usr/bin/env python3
"""
Supabase Sync Script for Hermes on Jupyter

This script syncs notebooks, scripts, and hermes config to/from Supabase.
Run manually or set up auto-sync.

Usage:
    python sync.py pull    # Download from Supabase
    python sync.py push    # Upload to Supabase
    python sync.py all     # Pull then push
"""

import os
import sys
import subprocess
from pathlib import Path

try:
    from supabase import create_client
except ImportError:
    print("Installing supabase...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "supabase"], check=True)
    from supabase import create_client

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://opdpexsytsaldlworztz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
BUCKET_NAME = os.environ.get('SUPABASE_BUCKET', 'manini')

# Local paths
WORKSPACE = '/workspace'
NOTEBOOKS_DIR = os.path.join(WORKSPACE, 'notebooks')
SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')
HERMES_HOME = os.path.expanduser('~/.hermes')


def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Set SUPABASE_URL and SUPABASE_KEY environment variables")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def ensure_dirs():
    """Create necessary directories."""
    for d in [NOTEBOOKS_DIR, SCRIPTS_DIR]:
        os.makedirs(d, exist_ok=True)
        print(f"Directory: {d}")


def pull_files():
    """Download files from Supabase."""
    print("\n📥 Pulling files from Supabase...")
    
    sb = get_supabase()
    if not sb:
        return
    
    try:
        files = sb.storage.from_(BUCKET_NAME).list()
        if not files:
            print("No files in storage")
            return
        
        pulled = 0
        for file in files:
            name = file.get('name', '')
            if not name:
                continue
            
            # Skip folders
            if name.endswith('/'):
                continue
            
            # Determine destination folder
            if name.startswith('notebooks/'):
                local_dir = os.path.join(WORKSPACE, 'notebooks')
                filename = name.replace('notebooks/', '', 1)
            elif name.startswith('scripts/'):
                local_dir = os.path.join(WORKSPACE, 'scripts')
                filename = name.replace('scripts/', '', 1)
            elif name.startswith('hermes/'):
                local_dir = HERMES_HOME
                filename = name.replace('hermes/', '', 1)
            else:
                continue
            
            if not filename:
                continue
            
            print(f"  Downloading {name}...")
            os.makedirs(local_dir, exist_ok=True)
            
            try:
                data = sb.storage.from_(BUCKET_NAME).download(name)
                local_path = os.path.join(local_dir, filename)
                with open(local_path, 'wb') as f:
                    f.write(data)
                pulled += 1
            except Exception as e:
                print(f"    Error: {e}")
        
        print(f"\n✓ Pulled {pulled} files")
        
    except Exception as e:
        print(f"Error: {e}")


def push_files():
    """Upload files to Supabase."""
    print("\n📤 Pushing files to Supabase...")
    
    sb = get_supabase()
    if not sb:
        return
    
    def upload_folder(local_dir, remote_folder, extensions):
        """Upload all files from a folder."""
        if not os.path.exists(local_dir):
            print(f"  {local_dir} does not exist")
            return 0
        
        uploaded = 0
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                if not any(filename.endswith(ext) for ext in extensions):
                    continue
                
                local_path = os.path.join(root, filename)
                rel_path = os.path.relpath(local_path, local_dir)
                remote_name = f"{remote_folder}/{rel_path}"
                
                print(f"  Uploading {remote_name}...")
                
                try:
                    with open(local_path, 'rb') as f:
                        content = f.read()
                    sb.storage.from_(BUCKET_NAME).upload(
                        remote_name, content,
                        {"contentType": "application/octet-stream"}
                    )
                    uploaded += 1
                except Exception as e:
                    try:
                        with open(local_path, 'rb') as f:
                            content = f.read()
                        sb.storage.from_(BUCKET_NAME).update(
                            remote_name, content,
                            {"contentType": "application/octet-stream"}
                        )
                        uploaded += 1
                    except Exception as e2:
                        print(f"    Error: {e2}")
        
        return uploaded
    
    # Upload notebooks
    n = upload_folder(NOTEBOOKS_DIR, 'notebooks', ['.ipynb', '.py', '.md', '.json'])
    print(f"  Uploaded {n} notebooks/scripts")
    
    # Upload hermes config
    h = upload_folder(HERMES_HOME, 'hermes', ['.yaml', '.json', '.md', '.txt', '.db', '.sqlite'])
    print(f"  Uploaded {h} hermes files")
    
    print("\n✓ Push complete!")


def main():
    ensure_dirs()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'pull':
            pull_files()
        elif cmd == 'push':
            push_files()
        elif cmd == 'all':
            pull_files()
            push_files()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python sync.py [pull|push|all]")
    else:
        print("Usage: python sync.py [pull|push|all]")


if __name__ == '__main__':
    main()
