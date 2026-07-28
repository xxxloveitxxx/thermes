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
import shutil
from pathlib import Path

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://opdpexsytsaldlworztz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
BUCKET_NAME = os.environ.get('SUPABASE_BUCKET', 'manini')

# Local paths
if os.path.exists('/workspace') and os.access('/workspace', os.W_OK):
    WORKSPACE = '/workspace'
elif os.path.exists('/app') and os.access('/app', os.W_OK):
    WORKSPACE = '/app'
else:
    WORKSPACE = os.getcwd()

NOTEBOOKS_DIR = os.path.join(WORKSPACE, 'notebooks')
SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')
HERMES_HOME = os.path.expanduser('~/.hermes')


def get_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }


def sync_config_local_to_hermes():
    """Copy config.yaml to ~/.hermes/config.yaml to ensure they are synchronized."""
    workspace_config = os.path.join(WORKSPACE, 'config.yaml')
    hermes_config = os.path.join(HERMES_HOME, 'config.yaml')
    if os.path.exists(workspace_config):
        os.makedirs(os.path.dirname(hermes_config), exist_ok=True)
        try:
            shutil.copy2(workspace_config, hermes_config)
            print(f"  ✓ Synchronized {workspace_config} -> {hermes_config}")
        except Exception as e:
            print(f"  ✗ Failed to copy config to hermes: {e}")


def sync_config_hermes_to_local():
    """Copy ~/.hermes/config.yaml back to config.yaml so it is visible in Jupyter Lab."""
    workspace_config = os.path.join(WORKSPACE, 'config.yaml')
    hermes_config = os.path.join(HERMES_HOME, 'config.yaml')
    if os.path.exists(hermes_config):
        os.makedirs(os.path.dirname(workspace_config), exist_ok=True)
        try:
            shutil.copy2(hermes_config, workspace_config)
            print(f"  ✓ Synchronized {hermes_config} -> {workspace_config}")
        except Exception as e:
            print(f"  ✗ Failed to copy config to workspace: {e}")


def download_file(remote_path, local_path):
    """Download a file from Supabase Storage."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=30)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return True
        else:
            print(f"      Download error: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"      Download exception: {e}")
    return False


def upload_file(local_path, remote_path):
    """Upload a file to Supabase Storage."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    try:
        with open(local_path, 'rb') as f:
            resp = requests.post(url, headers=get_headers(), files={'file': f}, timeout=30)
        if resp.status_code in [200, 201]:
            return True
        # Try update if already exists
        with open(local_path, 'rb') as f:
            resp = requests.put(url, headers=get_headers(), files={'file': f}, timeout=30)
        return resp.status_code in [200, 201]
    except Exception as e:
        print(f"      Upload exception: {e}")
    return False


def list_files_recursive(prefix=''):
    """List all files in the Supabase bucket recursively under the given prefix."""
    files_list = []
    prefixes_to_check = [prefix]
    checked_prefixes = set()

    headers = get_headers()
    url = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET_NAME}"

    while prefixes_to_check:
        current_prefix = prefixes_to_check.pop(0)
        if current_prefix in checked_prefixes:
            continue
        checked_prefixes.add(current_prefix)

        payload = {
            'limit': 100,
            'prefix': current_prefix,
            'sortBy': {'column': 'name', 'order': 'asc'}
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code != 200:
                print(f"  List error for prefix '{current_prefix}': {resp.status_code}")
                continue

            items = resp.json()
            for item in items:
                name = item.get('name', '')
                if not name:
                    continue

                # Reconstruct full path relative to bucket
                if current_prefix and name.startswith(current_prefix):
                    full_path = name
                else:
                    full_path = f"{current_prefix}{name}" if current_prefix.endswith('/') else f"{current_prefix}/{name}"

                # Check if this item is a folder.
                # In Supabase Storage API, folders typically have id=None, or metadata=None.
                is_folder = (item.get('id') is None) or ('metadata' not in item) or (item.get('metadata') is None)

                if is_folder:
                    folder_prefix = full_path if full_path.endswith('/') else f"{full_path}/"
                    prefixes_to_check.append(folder_prefix)
                else:
                    # It's a file
                    files_list.append({
                        'name': name,
                        'full_path': full_path,
                        'id': item.get('id')
                    })
        except Exception as e:
            print(f"  Exception listing prefix '{current_prefix}': {e}")

    return files_list


def ensure_dirs():
    """Create necessary directories."""
    for d in [NOTEBOOKS_DIR, SCRIPTS_DIR, HERMES_HOME]:
        os.makedirs(d, exist_ok=True)


def pull_files():
    """Download files from Supabase."""
    print("\n📥 Pulling files from Supabase...")
    ensure_dirs()
    
    folders = {'notebooks': NOTEBOOKS_DIR, 'scripts': SCRIPTS_DIR, 'hermes': HERMES_HOME}
    pulled = 0

    for folder, local_dir in folders.items():
        print(f"\n  Checking remote {folder}/ recursively...")
        files = list_files_recursive(prefix=f'{folder}/')
        
        if not files:
            print(f"    No files found")
            continue
        
        for f in files:
            full_path = f['full_path']
            filename = f['name']
            
            # Skip placeholders
            if filename == '.emptyFolderPlaceholder' or filename.endswith('.emptyFolderPlaceholder'):
                continue
            
            # Extract relative path inside this folder prefix
            if full_path.startswith(f"{folder}/"):
                rel_path = full_path[len(f"{folder}/"):]
            else:
                rel_path = full_path

            local_path = os.path.join(local_dir, rel_path)
            
            print(f"    Downloading {full_path} -> {local_path}...")
            if download_file(full_path, local_path):
                pulled += 1
                print(f"      ✓ Downloaded")
            else:
                print(f"      ✗ Failed")

    # Copy configuration file from hermes directory back to workspace
    sync_config_hermes_to_local()
    
    print(f"\n✓ Pull complete! Total files: {pulled}")


def push_files():
    """Upload files to Supabase."""
    print("\n📤 Pushing files to Supabase...")
    ensure_dirs()
    
    # Sync workspace config to hermes home before uploading so it gets backed up
    sync_config_local_to_hermes()

    def upload_folder(local_dir, remote_folder, extensions=None):
        """Upload all files from a folder recursively."""
        if not os.path.exists(local_dir):
            print(f"  {local_dir} does not exist")
            return 0
        
        uploaded = 0
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                # If extensions filter specified, only upload matched files
                if extensions:
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
    
    # Upload notebooks & scripts completely
    n = upload_folder(NOTEBOOKS_DIR, 'notebooks')
    print(f"  Uploaded {n} files from notebooks/")

    s = upload_folder(SCRIPTS_DIR, 'scripts')
    print(f"  Uploaded {s} files from scripts/")
    
    # Upload hermes config & state databases with specific important extensions
    # This prevents uploading massive audio/image cache folders, while saving all configurations/states/memories.
    hermes_extensions = ['.yaml', '.yml', '.json', '.md', '.txt', '.db', '.sqlite', '.env', '.update_check']
    h = upload_folder(HERMES_HOME, 'hermes', hermes_extensions)
    print(f"  Uploaded {h} files from ~/.hermes/")
    
    print("\n✓ Push complete!")


def main():
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
