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
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SYNC - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
BUCKET_NAME = os.environ.get('SUPABASE_BUCKET', 'manini')

# Validate required credentials
def validate_credentials():
    if not SUPABASE_URL:
        logger.error("❌ SUPABASE_URL is not set!")
        return False
    if not SUPABASE_KEY:
        logger.error("❌ SUPABASE_KEY is not set!")
        return False
    return True

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
            logger.info(f"  ✓ Synchronized {workspace_config} -> {hermes_config}")
        except Exception as e:
            logger.error(f"  ✗ Failed to copy config to hermes: {e}")


def sync_config_hermes_to_local():
    """Copy ~/.hermes/config.yaml back to config.yaml so it is visible in Jupyter Lab."""
    workspace_config = os.path.join(WORKSPACE, 'config.yaml')
    hermes_config = os.path.join(HERMES_HOME, 'config.yaml')
    if os.path.exists(hermes_config):
        os.makedirs(os.path.dirname(workspace_config), exist_ok=True)
        try:
            shutil.copy2(hermes_config, workspace_config)
            logger.info(f"  ✓ Synchronized {hermes_config} -> {workspace_config}")
        except Exception as e:
            logger.error(f"  ✗ Failed to copy config to workspace: {e}")


def download_file(remote_path, local_path):
    """Download a file from Supabase Storage."""
    if not validate_credentials():
        logger.error("Cannot download - credentials not configured")
        return False
        
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=30)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            logger.info(f"      ✓ Downloaded {remote_path}")
            return True
        else:
            logger.error(f"      Download error: {resp.status_code} - {resp.text[:200]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"      Connection error downloading {remote_path}: {e}")
    except Exception as e:
        logger.error(f"      Download exception: {e}")
    return False


def upload_file(local_path, remote_path):
    """Upload a file to Supabase Storage."""
    if not validate_credentials():
        logger.error("Cannot upload - credentials not configured")
        return False
        
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    try:
        with open(local_path, 'rb') as f:
            resp = requests.post(url, headers=get_headers(), files={'file': f}, timeout=30)
        if resp.status_code in [200, 201]:
            logger.info(f"      ✓ Uploaded {remote_path}")
            return True
        # Try update if already exists
        with open(local_path, 'rb') as f:
            resp = requests.put(url, headers=get_headers(), files={'file': f}, timeout=30)
        if resp.status_code in [200, 201]:
            logger.info(f"      ✓ Updated {remote_path}")
            return True
        logger.error(f"      Upload failed: {resp.status_code} - {resp.text[:200]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"      Connection error uploading {remote_path}: {e}")
    except Exception as e:
        logger.error(f"      Upload exception: {e}")
    return False


def list_files_recursive(prefix=''):
    """List all files in the Supabase bucket recursively under the given prefix."""
    if not validate_credentials():
        logger.error("Cannot list files - credentials not configured")
        return []
        
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
                logger.error(f"  List error for prefix '{current_prefix}': {resp.status_code}")
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
        except requests.exceptions.ConnectionError as e:
            logger.error(f"  Connection error listing prefix '{current_prefix}': {e}")
        except Exception as e:
            logger.error(f"  Exception listing prefix '{current_prefix}': {e}")

    return files_list


def ensure_dirs():
    """Create necessary directories."""
    for d in [NOTEBOOKS_DIR, SCRIPTS_DIR, HERMES_HOME]:
        os.makedirs(d, exist_ok=True)


def pull_files():
    """Download files from Supabase."""
    logger.info("📥 Pulling files from Supabase...")
    ensure_dirs()
    
    pulled = 0

    # 1. Pull everything from workspace/ folder
    logger.info(f"  Checking remote workspace/ recursively...")
    files = list_files_recursive(prefix='workspace/')
    
    if files:
        logger.info(f"    Found {len(files)} files in workspace/")
        for f in files:
            full_path = f['full_path']
            filename = f['name']
            
            if filename == '.emptyFolderPlaceholder' or filename.endswith('.emptyFolderPlaceholder'):
                continue
            
            # Extract relative path
            if full_path.startswith("workspace/"):
                rel_path = full_path[len("workspace/"):]
            else:
                rel_path = full_path

            local_path = os.path.join(WORKSPACE, rel_path)
            logger.info(f"    Downloading {full_path} -> {local_path}")
            if download_file(full_path, local_path):
                pulled += 1
    else:
        logger.info(f"    No workspace files found")

    # 2. Pull hermes state & memory
    logger.info(f"  Checking remote hermes/ recursively...")
    files = list_files_recursive(prefix='hermes/')
    
    if files:
        logger.info(f"    Found {len(files)} Hermes files")
        for f in files:
            full_path = f['full_path']
            filename = f['name']
            
            if filename == '.emptyFolderPlaceholder' or filename.endswith('.emptyFolderPlaceholder'):
                continue
            
            if full_path.startswith("hermes/"):
                rel_path = full_path[len("hermes/"):]
            else:
                rel_path = full_path

            local_path = os.path.join(HERMES_HOME, rel_path)
            logger.info(f"    Downloading {full_path} -> {local_path}")
            if download_file(full_path, local_path):
                pulled += 1
    else:
        logger.info(f"    No hermes files found")

    # Copy configuration file from hermes directory back to workspace
    sync_config_hermes_to_local()
    
    logger.info(f"✓ Pull complete! Total files: {pulled}")


def push_files():
    """Upload files to Supabase."""
    logger.info("📤 Pushing files to Supabase...")
    ensure_dirs()
    
    # Sync workspace config to hermes home before uploading so it gets backed up
    sync_config_local_to_hermes()

    def upload_folder(local_dir, remote_folder, extensions=None, exclude_dirs=None):
        """Upload all files from a folder recursively."""
        logger.info(f"  Checking {local_dir}...")
        
        if not os.path.exists(local_dir):
            logger.warning(f"  ❌ {local_dir} does not exist")
            return 0
        
        if exclude_dirs is None:
            exclude_dirs = ['__pycache__', '.git', 'node_modules']
        
        uploaded = 0
        for root, dirs, files in os.walk(local_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for filename in files:
                # Skip Python cache files
                if filename.endswith('.pyc') or filename.startswith('.'):
                    continue
                
                # If extensions filter specified, only upload matched files
                if extensions:
                    if not any(filename.endswith(ext) for ext in extensions):
                        continue
                
                local_path = os.path.join(root, filename)
                rel_path = os.path.relpath(local_path, local_dir)
                remote_name = f"{remote_folder}/{rel_path}"
                
                if upload_file(local_path, remote_name):
                    uploaded += 1
        
        return uploaded
    
    # 1. Upload EVERYTHING from /workspace (user files, Hermes outputs, etc.)
    logger.info("  Uploading ALL files from /workspace...")
    workspace_uploaded = upload_folder(WORKSPACE, 'workspace')
    logger.info(f"  ✅ Uploaded {workspace_uploaded} files from /workspace")

    # 2. Upload hermes state & memory (comprehensive)
    logger.info("  Uploading Hermes state and memory...")
    hermes_extensions = ['.yaml', '.yml', '.json', '.md', '.txt', '.db', '.sqlite', '.env', 
                        '.update_check', '.memory', '.context', '.state']
    hermes_uploaded = upload_folder(HERMES_HOME, 'hermes', hermes_extensions)
    logger.info(f"  ✅ Uploaded {hermes_uploaded} files from ~/.hermes/")
    
    logger.info("✓ Push complete!")


def main():
    logger.info("=== Supabase Sync Starting ===")
    
    if not validate_credentials():
        logger.error("Sync aborted: Missing Supabase credentials!")
        logger.error("Please set SUPABASE_URL and SUPABASE_KEY environment variables")
        sys.exit(1)
    
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
            logger.error(f"Unknown command: {cmd}")
            logger.error("Usage: python sync.py [pull|push|all]")
    else:
        logger.info("Usage: python sync.py [pull|push|all]")


if __name__ == '__main__':
    main()
