#!/usr/bin/env python3
"""
Supabase Sync Script for Hermes on Jupyter

This script syncs notebooks, scripts, and hermes config to/from Supabase.
Uses direct HTTP requests to Supabase Storage API.

Usage:
    python sync.py pull    # Download from Supabase
    python sync.py push    # Upload to Supabase
    python sync.py all     # Pull then push
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://opdpexsytsaldlworztz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
BUCKET_NAME = os.environ.get('SUPABASE_BUCKET', 'manini')

# Local paths
WORKSPACE = '/workspace'
NOTEBOOKS_DIR = os.path.join(WORKSPACE, 'notebooks')
SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')
HERMES_HOME = os.path.expanduser('~/.hermes')


def get_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }


def list_files(prefix=''):
    """List files in bucket with prefix."""
    url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"
    payload = {'limit': 100}
    if prefix:
        payload['prefix'] = prefix
    resp = requests.post(url, headers=get_headers(), json=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  List error: {resp.status_code} - {resp.text}")
        return []


def download_file(remote_path, local_path):
    """Download a file."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(resp.content)
        return True
    return False


def upload_file(local_path, remote_path):
    """Upload a file."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    with open(local_path, 'rb') as f:
        resp = requests.post(url, headers=get_headers(), files={'file': f})
    if resp.status_code in [200, 201]:
        return True
    # Try update
    resp = requests.put(url, headers=get_headers(), files={'file': open(local_path, 'rb')})
    return resp.status_code in [200, 201]


def ensure_dirs():
    """Create necessary directories."""
    for d in [NOTEBOOKS_DIR, SCRIPTS_DIR]:
        os.makedirs(d, exist_ok=True)
        print(f"Directory: {d}")


def pull_files():
    """Download files from Supabase."""
    print("\n📥 Pulling files from Supabase...")
    
    folders = {'notebooks': NOTEBOOKS_DIR, 'scripts': SCRIPTS_DIR, 'hermes': HERMES_HOME}
    
    pulled = 0
    for folder, local_dir in folders.items():
        print(f"\n  Checking {folder}/...")
        # Note: trailing slash required for folder listing!
        files = list_files(prefix=f'{folder}/')
        
        if not files:
            print(f"    Empty")
            continue
        
        for f in files:
            name = f.get('name', '')
            if not name or name.endswith('/'):
                continue
            
            # Extract filename after folder prefix
            filename = name.split('/')[-1]
            
            if not filename or filename == '.emptyFolderPlaceholder':
                continue
            
            local_path = os.path.join(local_dir, filename)
            
            print(f"    Downloading {filename}...")
            if download_file(name, local_path):
                pulled += 1
                print(f"      ✓ Downloaded")
            else:
                print(f"      ✗ Failed")
    
    print(f"\n✓ Pulled {pulled} files")


def push_files():
    """Upload files to Supabase."""
    print("\n📤 Pushing files to Supabase...")
    
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
                if upload_file(local_path, remote_name):
                    uploaded += 1
                    print(f"    ✓ Done")
                else:
                    print(f"    ✗ Failed")
        
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
