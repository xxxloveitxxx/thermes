#!/usr/bin/env python3
"""
Debug script - Run this to check Hermes and Supabase sync status.
"""
import os
import sys
import subprocess
import glob

print("=" * 60)
print("🔍 HERMES + SUPABASE SYNC DEBUG")
print("=" * 60)

# Check environment variables
print("\n📋 ENVIRONMENT VARIABLES:")
print(f"  SUPABASE_URL: {'✅ SET' if os.environ.get('SUPABASE_URL') else '❌ NOT SET'}")
print(f"  SUPABASE_KEY: {'✅ SET' if os.environ.get('SUPABASE_KEY') else '❌ NOT SET'}")

# Check Hermes home
print("\n🤖 HERMES STATE:")
hermes_home = os.path.expanduser('~/.hermes')
print(f"  Hermes home: {hermes_home}")
print(f"  Exists: {'✅' if os.path.exists(hermes_home) else '❌ NO'}")

if os.path.exists(hermes_home):
    print(f"\n  Files in ~/.hermes/:")
    for root, dirs, files in os.walk(hermes_home):
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, hermes_home)
            size = os.path.getsize(path)
            print(f"    - {rel} ({size} bytes)")

# Check Hermes agent info
print("\n📦 HERMES AGENT INFO:")
hermes_where = subprocess.run(['which', 'hermes'], capture_output=True, text=True)
print(f"  Hermes location: {hermes_where.stdout.strip() or 'NOT FOUND'}")

# Check last save
print("\n⏰ LAST SAVE:")
save_file = '/tmp/last_save_time'
if os.path.exists(save_file):
    import time
    last = float(open(save_file).read().strip() or 0)
    ago = time.time() - last
    print(f"  Last auto-save: {ago:.0f} seconds ago")
else:
    print("  No auto-save recorded")

# Manual save button
print("\n" + "=" * 60)
print("💾 TO FORCE SAVE, run in cell:")
print("   !python /workspace/scripts/sync.py push")
print("=" * 60)
