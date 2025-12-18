#!/usr/bin/env python3
"""
Comprehensive Import Diagnostic Tool
This will help identify exactly where the import is failing
"""

import sys
import os

def diagnose_imports():
    """Step-by-step import diagnosis"""
    print("=" * 60)
    print("🔍 IMPORT DIAGNOSTIC TOOL")
    print("=" * 60)
    print()
    
    # Step 1: Check basic Python environment
    print("📋 Step 1: Python Environment")
    print(f"   Python version: {sys.version}")
    print(f"   Python path: {sys.executable}")
    print(f"   Working directory: {os.getcwd()}")
    print()
    
    # Step 2: Check if anony directory exists
    print("📋 Step 2: Directory Structure")
    if os.path.exists("anony"):
        print("   ✅ anony/ directory found")
        print(f"   Files in anony/: {len(os.listdir('anony'))}")
        
        # Check for __init__.py
        if os.path.exists("anony/__init__.py"):
            print("   ✅ anony/__init__.py exists")
            size = os.path.getsize("anony/__init__.py")
            print(f"   File size: {size} bytes")
        else:
            print("   ❌ anony/__init__.py NOT FOUND!")
            return False
    else:
        print("   ❌ anony/ directory NOT FOUND!")
        return False
    print()
    
    # Step 3: Try importing config first (no anony dependency)
    print("📋 Step 3: Importing Config")
    try:
        from config import Config
        print("   ✅ config.Config imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import config: {e}")
        return False
    print()
    
    # Step 4: Try importing logging components
    print("📋 Step 4: Basic Imports")
    try:
        import time
        import logging
        print("   ✅ Standard library imports OK")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    print()
    
    # Step 5: Try importing from anony.core
    print("📋 Step 5: Core Modules")
    try:
        from anony.core.bot import Bot
        print("   ✅ anony.core.bot.Bot")
    except Exception as e:
        print(f"   ❌ anony.core.bot.Bot failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from anony.core.mongo import MongoDB
        print("   ✅ anony.core.mongo.MongoDB")
    except Exception as e:
        print(f"   ❌ anony.core.mongo.MongoDB failed: {e}")
        return False
    print()
    
    # Step 6: Try importing Queue directly
    print("📋 Step 6: Queue Class")
    try:
        from anony.helpers._queue import Queue
        print("   ✅ anony.helpers._queue.Queue")
        q = Queue()
        print(f"   ✅ Queue instance created: {q}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # Step 7: Try importing anony package
    print("📋 Step 7: Main anony Package")
    try:
        import anony
        print(f"   ✅ anony imported")
        print(f"   Version: {anony.__version__}")
        print(f"   Has 'queue': {hasattr(anony, 'queue')}")
        print(f"   Has 'config': {hasattr(anony, 'config')}")
        print(f"   Has 'logger': {hasattr(anony, 'logger')}")
    except Exception as e:
        print(f"   ❌ Failed to import anony: {e}")
        print("\n   DETAILED TRACEBACK:")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # Step 8: Try accessing queue from anony
    print("📋 Step 8: Accessing anony.queue")
    try:
        from anony import queue
        print(f"   ✅ anony.queue: {queue}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    print("=" * 60)
    print("✅ ALL DIAGNOSTICS PASSED!")
    print("=" * 60)
    print("\nYour imports are working correctly!")
    print("You should be able to run: python -m anony")
    return True


if __name__ == "__main__":
    success = diagnose_imports()
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ DIAGNOSTIC FAILED")
        print("=" * 60)
        print("\n🔧 SUGGESTED FIXES:\n")
        print("1. Clear Python cache:")
        print("   python clear_cache.py")
        print()
        print("2. Check for naming conflicts:")
        print("   - Make sure no file is named 'queue.py' in top level")
        print("   - Make sure no 'anony.py' file exists")
        print()
        print("3. Reinstall dependencies:")
        print("   pip install --upgrade --force-reinstall -r requirements.txt")
        print()
        print("4. Check Python version (needs 3.8+):")
        print(f"   Current: {sys.version}")
        print()
        sys.exit(1)
    else:
        sys.exit(0)
