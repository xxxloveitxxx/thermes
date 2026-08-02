#!/usr/bin/env python3
"""
Bootstrap Script for Jupyter + Hermes Agent on Render

This process:
1. Executes `startup.py` to pull files from Supabase, install Hermes, and sync config.
2. Starts a background continuous auto-saver daemon (every 30 seconds).
3. Launches Jupyter Lab as a subprocess and monitors it.
4. Listens for SIGTERM / SIGINT (e.g. Render spinning down/sleeping) to gracefully 
   stop Jupyter Lab and trigger a blocking final push of files and state to Supabase.
"""

import os
import sys
import signal
import subprocess
import time
import threading
from pathlib import Path

# Paths
if os.path.exists('/workspace') and os.access('/workspace', os.W_OK):
    WORKSPACE = '/workspace'
elif os.path.exists('/app') and os.access('/app', os.W_OK):
    WORKSPACE = '/app'
else:
    WORKSPACE = os.getcwd()

SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')
SYNC_SCRIPT = os.path.join(SCRIPTS_DIR, 'sync.py')
STARTUP_SCRIPT = os.path.join(SCRIPTS_DIR, 'startup.py')

jupyter_process = None
shutdown_signaled = False
LAST_SAVE_FILE = '/tmp/last_bootstrap_save'
SAVE_LOCK = '/tmp/bootstrap_save_lock'


def log(msg):
    print(f"[Hermes Bootstrap] {msg}", flush=True)


def do_final_save():
    """Perform a blocking final save to Supabase."""
    # Prevent concurrent saves
    if os.path.exists(SAVE_LOCK):
        return False
        
    try:
        Path(SAVE_LOCK).touch()
        log("Running final save to Supabase...")
        result = subprocess.run(
            [sys.executable, SYNC_SCRIPT, 'push'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            log("✓ Final save completed!")
            return True
        else:
            log(f"✗ Final save failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log("✗ Final save timed out")
        return False
    except Exception as e:
        log(f"✗ Final save error: {e}")
        return False
    finally:
        if os.path.exists(SAVE_LOCK):
            os.remove(SAVE_LOCK)


def handle_shutdown(signum, frame):
    global shutdown_signaled, jupyter_process
    if shutdown_signaled:
        return
    shutdown_signaled = True

    log(f"Received signal {signum}. Initiating graceful shutdown...")

    # 1. Terminate Jupyter Lab
    if jupyter_process and jupyter_process.poll() is None:
        log("Stopping Jupyter Lab...")
        jupyter_process.terminate()
        try:
            jupyter_process.wait(timeout=15)
            log("Jupyter Lab stopped.")
        except subprocess.TimeoutExpired:
            log("Forcing Jupyter Lab kill...")
            jupyter_process.kill()
            jupyter_process.wait()

    # 2. FINAL SAVE - This is critical!
    do_final_save()

    sys.exit(0)


def start_auto_save_loop():
    """Starts a background thread that pushes to Supabase every 30 seconds."""
    log("Starting continuous auto-save daemon (every 30 seconds)...")
    
    def save_loop():
        while True:
            time.sleep(30)
            
            # Rate limit
            now = time.time()
            try:
                if os.path.exists(LAST_SAVE_FILE):
                    last = float(open(LAST_SAVE_FILE).read().strip() or 0)
                    if now - last < 30:
                        continue
            except:
                pass
            
            # Do save
            if os.path.exists(SAVE_LOCK):
                continue
                
            try:
                Path(SAVE_LOCK).touch()
                result = subprocess.run(
                    [sys.executable, SYNC_SCRIPT, 'push'],
                    capture_output=True, timeout=90
                )
                if result.returncode == 0:
                    print("💾 [Bootstrap] Auto-saved", flush=True)
                if os.path.exists(SAVE_LOCK):
                    os.remove(SAVE_LOCK)
                Path(LAST_SAVE_FILE).write_text(str(now))
            except:
                if os.path.exists(SAVE_LOCK):
                    os.remove(SAVE_LOCK)
    
    t = threading.Thread(target=save_loop, daemon=True)
    t.start()
    log("✓ Auto-save daemon started")


def main():
    # Register signal handlers for SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    log("Initializing Jupyter Space with Hermes...")

    # 1. Run initial startup & pull files (restores from Supabase)
    if os.path.exists(STARTUP_SCRIPT):
        try:
            log("Running startup script (pulling files from Supabase)...")
            subprocess.run([sys.executable, STARTUP_SCRIPT], check=True, timeout=600)
            log("✓ Startup completed. Files restored.")
        except Exception as e:
            log(f"✗ Warning: Startup script failed: {e}")

    # 2. Start the continuous auto-saver daemon
    try:
        start_auto_save_loop()
    except Exception as e:
        log(f"✗ Warning: Failed to start auto-save daemon: {e}")

    # 3. Start Jupyter Lab
    log("Starting Jupyter Lab...")
    jupyter_cmd = [
        "jupyter", "lab",
        "--ip=0.0.0.0",
        "--port=8888",
        "--no-browser",
        "--allow-root",
        f"--notebook-dir={WORKSPACE}"
    ]

    global jupyter_process
    try:
        jupyter_process = subprocess.Popen(jupyter_cmd)
    except FileNotFoundError:
        log("Jupyter Lab executable not found.")
        jupyter_process = subprocess.Popen(["sleep", "3600"])

    # 4. Monitor Jupyter process loop
    while True:
        try:
            ret_code = jupyter_process.wait(timeout=1.0)
            log(f"Jupyter Lab exited with code {ret_code}.")
            handle_shutdown(signal.SIGTERM, None)
            break
        except subprocess.TimeoutExpired:
            continue
        except (KeyboardInterrupt, SystemExit):
            handle_shutdown(signal.SIGTERM, None)
            break


if __name__ == '__main__':
    main()
