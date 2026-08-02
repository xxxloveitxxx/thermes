#!/usr/bin/env python3
"""
Save/Load Helper for Jupyter notebooks

This script provides reliable save and load functions with clear feedback.
Run this in a notebook cell to get save/load status.

Usage:
    from save_helper import save, load
    save()  # Save to Supabase
    load()  # Load from Supabase
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get script directory
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_SCRIPT = os.path.join(SCRIPTS_DIR, 'sync.py')


def save():
    """Save all files to Supabase with detailed feedback."""
    print("=" * 50)
    print("💾 SAVING TO SUPABASE...")
    print("=" * 50)
    
    # Check credentials first
    if not os.environ.get('SUPABASE_URL'):
        print("❌ ERROR: SUPABASE_URL not set!")
        return False
    if not os.environ.get('SUPABASE_KEY'):
        print("❌ ERROR: SUPABASE_KEY not set!")
        return False
    
    start = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, SYNC_SCRIPT, 'push'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        elapsed = (datetime.now() - start).total_seconds()
        
        if result.returncode == 0:
            print(f"✅ Save completed in {elapsed:.1f}s")
            print("📁 Files uploaded to Supabase Storage")
            return True
        else:
            print(f"❌ Save failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Save timed out (120s limit)")
        return False
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False


def load():
    """Load files from Supabase with detailed feedback."""
    print("=" * 50)
    print("📥 LOADING FROM SUPABASE...")
    print("=" * 50)
    
    # Check credentials first
    if not os.environ.get('SUPABASE_URL'):
        print("❌ ERROR: SUPABASE_URL not set!")
        return False
    if not os.environ.get('SUPABASE_KEY'):
        print("❌ ERROR: SUPABASE_KEY not set!")
        return False
    
    start = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, SYNC_SCRIPT, 'pull'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        elapsed = (datetime.now() - start).total_seconds()
        
        if result.returncode == 0:
            print(f"✅ Load completed in {elapsed:.1f}s")
            print("📁 Files downloaded from Supabase Storage")
            return True
        else:
            print(f"❌ Load failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Load timed out (120s limit)")
        return False
    except Exception as e:
        print(f"❌ Load error: {e}")
        return False


def status():
    """Check Supabase connection status."""
    print("=" * 50)
    print("🔍 SUPABASE STATUS CHECK")
    print("=" * 50)
    
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_KEY', '')
    bucket = os.environ.get('SUPABASE_BUCKET', 'manini')
    
    print(f"URL: {url if url else '❌ NOT SET'}")
    print(f"Key: {'✅ SET' if key else '❌ NOT SET'}")
    print(f"Bucket: {bucket}")
    
    if url and key:
        # Test connection
        try:
            import requests
            headers = {'apikey': key, 'Authorization': f'Bearer {key}'}
            resp = requests.get(
                f"{url}/storage/v1/object/list/{bucket}",
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                files = resp.json()
                print(f"✅ Connection OK - {len(files)} items in bucket")
            else:
                print(f"⚠️  Connection returned: {resp.status_code}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    else:
        print("⚠️  Cannot test connection - missing credentials")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Save/Load helper for Supabase')
    parser.add_argument('action', choices=['save', 'load', 'status'], 
                       help='Action to perform')
    args = parser.parse_args()
    
    if args.action == 'save':
        save()
    elif args.action == 'load':
        load()
    elif args.action == 'status':
        status()
