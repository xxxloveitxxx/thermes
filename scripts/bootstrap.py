#!/usr/bin/env python3
"""
Bootstrap Script for Jupyter + Hermes Agent on Render

This process:
1. Executes `startup.py` to pull files from Supabase, install Hermes, and sync config.
2. Starts a background continuous auto-saver daemon (every 5 minutes).
3. Launches Jupyter Lab as a subprocess and monitors it.
4. Listens for SIGTERM / SIGINT (e.g. Render spinning down/sleeping) to gracefully stop Jupyter Lab and trigger a blocking final push of files and state database to Supabase.
"""

import os
import sys
import signal
import subprocess
import time
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


def log(msg):
    print(f"[Hermes Bootstrap] {msg}", flush=True)


def handle_shutdown(signum, frame):
    global shutdown_signaled, jupyter_process
    if shutdown_signaled:
        return
    shutdown_signaled = True

    log(f"Received signal {signum}. Initiating graceful shutdown and save...")

    # 1. Terminate Jupyter Lab
    if jupyter_process and jupyter_process.poll() is None:
        log("Stopping Jupyter Lab...")
        jupyter_process.terminate()
        try:
            jupyter_process.wait(timeout=15)
            log("Jupyter Lab stopped successfully.")
        except subprocess.TimeoutExpired:
            log("Jupyter Lab did not stop in time, forcing kill...")
            jupyter_process.kill()
            jupyter_process.wait()

    # 2. Perform blocking, final save to Supabase
    log("Running final push to Supabase before shutdown...")
    try:
        # Run sync.py push
        subprocess.run([sys.executable, SYNC_SCRIPT, 'push'], check=True, timeout=120)
        log("✓ Final push completed successfully!")
    except Exception as e:
        log(f"✗ Final push failed: {e}")

    sys.exit(0)


def start_auto_save_loop():
    """Starts a background process that pushes to Supabase every 5 minutes."""
    log("Starting background continuous auto-save daemon...")
    pid = os.fork()
    if pid == 0:
        # Detach child process
        os.setsid()
        # Close standard file descriptors and redirect to log file
        sys.stdout = open('/tmp/auto_save.log', 'a')
        sys.stderr = open('/tmp/auto_save.log', 'a')

        while True:
            try:
                time.sleep(300)  # Pushes every 5 minutes
                subprocess.run([sys.executable, SYNC_SCRIPT, 'push'], timeout=120)
            except Exception:
                pass


def main():
    # Register signal handlers for SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    log("Initializing Jupyter Space with Hermes...")

    # 1. Run initial startup & pull files
    if os.path.exists(STARTUP_SCRIPT):
        try:
            log("Running startup script (Pulling files and checking Hermes installation)...")
            subprocess.run([sys.executable, STARTUP_SCRIPT], check=True, timeout=600)
            log("✓ Startup initialization completed.")
        except Exception as e:
            log(f"✗ Warning: Startup script failed: {e}")

    # 2. Start the background auto-saver daemon
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
    # In sandbox we might not want to run jupyter if it's not installed or if we just want to mock.
    # But let's run it or handle gracefully if not installed.
    try:
        jupyter_process = subprocess.Popen(jupyter_cmd)
    except FileNotFoundError:
        log("Jupyter Lab executable not found. Running in mock mode.")
        # Start a dummy process to simulate jupyter running
        jupyter_process = subprocess.Popen(["sleep", "3600"])

    # 4. Monitor Jupyter process loop
    while True:
        try:
            ret_code = jupyter_process.wait(timeout=1.0)
            log(f"Jupyter Lab exited with code {ret_code}.")
            # Trigger push and shutdown
            handle_shutdown(signal.SIGTERM, None)
            break
        except subprocess.TimeoutExpired:
            continue
        except (KeyboardInterrupt, SystemExit):
            handle_shutdown(signal.SIGTERM, None)
            break


if __name__ == '__main__':
    main()
