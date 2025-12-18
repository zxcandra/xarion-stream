# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import logging
from pathlib import Path
from time import time

# Use direct logging to avoid circular import
logger = logging.getLogger(__name__)


class FileCleanup:
    """Automatic cleanup for downloaded files"""
    
    def __init__(self, max_age_seconds: int = 3600, check_interval: int = 1800):
        """
        Args:
            max_age_seconds: Maximum age of files before deletion (default: 1 hour)
            check_interval: How often to run cleanup (default: 30 minutes)
        """
        self.max_age = max_age_seconds
        self.interval = check_interval
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
    async def cleanup_old_files(self) -> None:
        """Remove files older than max_age"""
        try:
            current_time = time()
            cleaned_count = 0
            freed_space = 0
            
            for file in self.downloads_dir.iterdir():
                if file.is_file():
                    file_age = current_time - file.stat().st_mtime
                    
                    if file_age > self.max_age:
                        file_size = file.stat().st_size
                        file.unlink()
                        cleaned_count += 1
                        freed_space += file_size
                        logger.debug(f"Cleaned up: {file.name} ({file_size / 1024 / 1024:.2f} MB)")
            
            if cleaned_count > 0:
                logger.info(
                    f"Cleanup completed: {cleaned_count} files removed, "
                    f"{freed_space / 1024 / 1024:.2f} MB freed"
                )
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)
    
    async def get_cache_stats(self) -> dict:
        """Get statistics about cached files"""
        total_files = 0
        total_size = 0
        
        try:
            for file in self.downloads_dir.iterdir():
                if file.is_file():
                    total_files += 1
                    total_size += file.stat().st_size
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return {
            "total_files": total_files,
            "total_size_mb": total_size / 1024 / 1024,
            "path": str(self.downloads_dir)
        }
    
    async def clear_all(self) -> None:
        """Clear all cached files (emergency cleanup)"""
        try:
            cleaned_count = 0
            for file in self.downloads_dir.iterdir():
                if file.is_file():
                    file.unlink()
                    cleaned_count += 1
            
            logger.info(f"Emergency cleanup: {cleaned_count} files removed")
        except Exception as e:
            logger.error(f"Emergency cleanup error: {e}", exc_info=True)
    
    async def start(self) -> None:
        """Start the cleanup scheduler"""
        logger.info(f"File cleanup scheduler started (interval: {self.interval}s, max age: {self.max_age}s)")
        
        while True:
            try:
                await asyncio.sleep(self.interval)
                await self.cleanup_old_files()
            except asyncio.CancelledError:
                logger.info("Cleanup scheduler stopped")
                break
            except Exception as e:
                logger.error(f"Cleanup scheduler error: {e}", exc_info=True)


# Global instance
cleanup = FileCleanup(max_age_seconds=3600, check_interval=1800)
