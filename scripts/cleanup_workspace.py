#!/usr/bin/env python3
"""
Workspace cleanup utility

This script removes unnecessary files from the workspace:
- Python cache files (__pycache__)
- Temporary files (*.tmp, *.bak)
- Log files older than 7 days
- Empty directories
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_workspace():
    """Clean up unnecessary files and directories"""
    
    workspace = Path.cwd()
    removed_items = []
    
    print(f"Cleaning workspace: {workspace}")
    
    # Remove __pycache__ directories
    for pycache_dir in workspace.rglob("__pycache__"):
        if pycache_dir.is_dir():
            shutil.rmtree(pycache_dir)
            removed_items.append(str(pycache_dir))
            print(f"Removed: {pycache_dir}")
    
    # Remove .pyc files
    for pyc_file in workspace.rglob("*.pyc"):
        pyc_file.unlink()
        removed_items.append(str(pyc_file))
        print(f"Removed: {pyc_file}")
    
    # Remove temporary files
    temp_patterns = ["*.tmp", "*.bak", "*.swp", "*.swo", "*.log~"]
    for pattern in temp_patterns:
        for temp_file in workspace.rglob(pattern):
            temp_file.unlink()
            removed_items.append(str(temp_file))
            print(f"Removed: {temp_file}")
    
    # Remove old log files (older than 7 days)
    cutoff_date = datetime.now() - timedelta(days=7)
    for log_file in workspace.rglob("*.log"):
        if log_file.is_file():
            file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_date < cutoff_date:
                log_file.unlink()
                removed_items.append(str(log_file))
                print(f"Removed old log: {log_file}")
    
    # Remove empty directories (except git/dvc)
    for root, dirs, files in os.walk(workspace, topdown=False):
        root_path = Path(root)
        # Skip special directories
        if any(special in root_path.parts for special in ['.git', '.dvc', '.venv']):
            continue
        
        if not files and not dirs:
            try:
                root_path.rmdir()
                removed_items.append(str(root_path))
                print(f"Removed empty directory: {root_path}")
            except OSError:
                pass  # Directory not empty or permission denied
    
    print(f"\nCleanup complete! Removed {len(removed_items)} items.")
    
    if removed_items:
        print("\nRemoved items:")
        for item in removed_items[:10]:  # Show first 10
            print(f"  - {item}")
        if len(removed_items) > 10:
            print(f"  ... and {len(removed_items) - 10} more items")
    
    return removed_items

if __name__ == "__main__":
    cleanup_workspace()