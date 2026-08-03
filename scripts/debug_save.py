#!/usr/bin/env python3
"""
Debug script - Run this in your notebook to check why auto-save isn't working.
"""
import os
import sys
import subprocess

print("=" * 60)
print("🔍 AUTO-SAVE DEBUG")
print("=" * 60)

# Check environment variables
print("\n📋 ENVIRONMENT VARIABLES:")
print(f"  SUPABASE_URL: {'✅ SET' if os.environ.get('SUPABASE_URL') else '❌ NOT SET'}")
print(f"  SUPABASE_KEY: {'✅ SET' if os.environ.get('SUPABASE_KEY') else '❌ NOT SET'}")
print(f"  SUPABASE_BUCKET: {os.environ.get('SUPABASE_BUCKET', 'NOT SET')}")

if os.environ.get('SUPABASE_URL'):
    print(f"  URL value: {os.environ.get('SUPABASE_URL')[:30]}...")

# Check Supabase connectivity
print("\n🌐 TESTING SUPABASE CONNECTION:")
if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_KEY'):
    try:
        import requests
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        bucket = os.environ.get('SUPABASE_BUCKET', 'manini')
        
        headers = {'apikey': key, 'Authorization': f'Bearer {key}'}
        resp = requests.get(
            f"{url}/storage/v1/object/list/{bucket}",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            items = resp.json()
            print(f"  ✅ Connected! Bucket has {len(items)} items")
            
            # Count files in each folder
            notebooks = [i for i in items if i.get('name', '').startswith('notebooks/')]
            scripts = [i for i in items if i.get('name', '').startswith('scripts/')]
            hermes = [i for i in items if i.get('name', '').startswith('hermes/')]
            
            print(f"    - notebooks/: {len(notebooks)} files")
            print(f"    - scripts/: {len(scripts)} files")
            print(f"    - hermes/: {len(hermes)} files")
            
            if len(items) == 0:
                print("  ⚠️  WARNING: Bucket is EMPTY! Nothing to restore!")
        else:
            print(f"  ❌ Error: {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
            
    except ImportError:
        print("  ⚠️  requests module not available")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
else:
    print("  ❌ Cannot test - credentials not set!")

# Check local files
print("\n📁 LOCAL FILES:")
workspace = '/workspace'
if os.path.exists(workspace):
    notebooks = os.path.join(workspace, 'notebooks')
    if os.path.exists(notebooks):
        files = os.listdir(notebooks)
        print(f"  notebooks/: {len(files)} files")
        for f in files[:5]:
            print(f"    - {f}")
    else:
        print("  notebooks/: NOT FOUND")
else:
    print("  /workspace: NOT FOUND")

# Check last save time
print("\n⏰ LAST SAVE TIME:")
save_file = '/tmp/last_save_time'
if os.path.exists(save_file):
    import time
    last = float(open(save_file).read().strip() or 0)
    ago = time.time() - last
    print(f"  Last save: {ago:.0f} seconds ago")
else:
    print("  No save recorded yet")

# Check auto-save log
print("\n📜 AUTO-SAVE LOG (last 10 lines):")
log_file = '/tmp/auto_save.log'
if os.path.exists(log_file):
    lines = open(log_file).readlines()
    for line in lines[-10:]:
        print(f"  {line.strip()}")
else:
    print("  No log file found")

print("\n" + "=" * 60)
print("💡 RECOMMENDATIONS:")
print("=" * 60)

if not os.environ.get('SUPABASE_URL'):
    print("❌ Set SUPABASE_URL in Render Dashboard > Environment")
if not os.environ.get('SUPABASE_KEY'):
    print("❌ Set SUPABASE_KEY in Render Dashboard > Environment")

print("\n✅ To manually save NOW, run:")
print("   !python /workspace/scripts/sync.py push")
