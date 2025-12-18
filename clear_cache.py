#!/usr/bin/env python3
"""
Clear Python cache files to prevent stale import issues
"""

import os
import shutil
from pathlib import Path

def clear_pycache(directory: str = "."):
    """Remove all __pycache__ directories and .pyc files"""
    removed_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"Removing: {cache_dir}")
            shutil.rmtree(cache_dir)
            removed_count += 1
            dirs.remove('__pycache__')
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                file_path = os.path.join(root, file)
                print(f"Removing: {file_path}")
                os.remove(file_path)
                removed_count += 1
    
    return removed_count


if __name__ == "__main__":
    print("🧹 Clearing Python cache files...\n")
    
    count = clear_pycache()
    
    print(f"\n✅ Removed {count} cache directories/files")
    print("\n💡 Now you can safely restart the bot:")
    print("   python test_imports.py   # Test imports")
    print("   python -m anony          # Start bot")
