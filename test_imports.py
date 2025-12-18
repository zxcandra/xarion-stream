#!/usr/bin/env python3
"""
Quick test to verify imports are working correctly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing imports...")

try:
    print("1. Testing anony imports...")
    from anony import logger, config, app, db, queue
    print("   ✅ Basic imports OK")
    
    print("2. Testing Queue class...")
    from anony.helpers._queue import Queue
    print(f"   ✅ Queue class: {Queue}")
    
    print("3. Testing queue instance...")
    print(f"   ✅ queue instance: {queue}")
    
    print("4. Testing cleanup...")
    from anony.helpers._cleanup import cleanup
    print(f"   ✅ cleanup: {cleanup}")
    
    print("5. Testing lyrics searcher...")
    from anony.helpers._lyrics import lyrics_searcher
    print(f"   ✅ lyrics_searcher: {lyrics_searcher}")
    
    print("\n✅ All imports successful!")
    print("Bot should start without errors now.")
    
except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
