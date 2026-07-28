#!/usr/bin/env python3
"""
IPython Kernel Initialization

This file runs automatically when any notebook kernel starts.
It pulls from Supabase and sets up the environment.
"""

import sys
import os

# Add workspace to path
sys.path.insert(0, '/workspace/scripts')

# Run startup
import startup
startup.main()

# Also run sync.py to ensure files are in place
import sync
sync.ensure_dirs()
