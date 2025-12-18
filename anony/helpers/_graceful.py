# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
Graceful Shutdown Handler untuk handle FloodWait dan restart yang aman
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional

from pyrogram.errors import FloodWait

from anony import logger


class GracefulShutdown:
    """Handle graceful shutdown dan FloodWait"""
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.is_shutting_down = False
        self.pending_tasks = []
        
    def setup_signal_handlers(self):
        """Setup signal handlers untuk SIGTERM dan SIGINT"""
        if sys.platform != 'win32':
            # Unix/Linux signals
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.handle_signal(s))
                )
        else:
            # Windows doesn't support add_signal_handler
            # Use signal.signal instead
            signal.signal(signal.SIGTERM, lambda sig, frame: asyncio.create_task(self.handle_signal(sig)))
            signal.signal(signal.SIGINT, lambda sig, frame: asyncio.create_task(self.handle_signal(sig)))
        
        logger.info("✅ Graceful shutdown handlers installed")
    
    async def handle_signal(self, sig):
        """Handle shutdown signal"""
        sig_name = signal.Signals(sig).name if hasattr(signal, 'Signals') else sig
        logger.warning(f"🛑 Received signal: {sig_name}")
        
        if not self.is_shutting_down:
            await self.shutdown()
    
    async def shutdown(self):
        """Perform graceful shutdown"""
        if self.is_shutting_down:
            logger.info("⚠️ Shutdown already in progress...")
            return
        
        self.is_shutting_down = True
        logger.info("🛑 Initiating graceful shutdown...")
        
        # Set shutdown event
        self.shutdown_event.set()
        
        # Import here to avoid circular import
        from anony import stop
        
        try:
            # Give tasks time to finish
            logger.info("⏳ Waiting for tasks to complete (5 seconds)...")
            await asyncio.sleep(5)
            
            # Call main stop function
            await stop()
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}", exc_info=True)
        finally:
            # Force exit
            sys.exit(0)
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self.shutdown_event.wait()


class FloodWaitHandler:
    """Handle FloodWait errors dengan retry mechanism"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.flood_wait_count = 0
    
    async def handle_flood_wait(self, error: FloodWait, operation_name: str = "operation"):
        """
        Handle FloodWait error dengan smart waiting
        
        Args:
            error: FloodWait exception
            operation_name: Name of operation for logging
        """
        wait_time = error.value
        self.flood_wait_count += 1
        
        logger.warning(
            f"⚠️ FloodWait encountered for {operation_name}\n"
            f"   Wait time: {wait_time} seconds\n"
            f"   Count: {self.flood_wait_count}/{self.max_retries}"
        )
        
        if self.flood_wait_count > self.max_retries:
            logger.error(
                f"❌ FloodWait retry limit exceeded ({self.max_retries})\n"
                f"   Initiating graceful shutdown..."
            )
            
            # Trigger graceful shutdown
            from anony.helpers._graceful import graceful_handler
            await graceful_handler.shutdown()
            return False
        
        # Calculate actual wait time with buffer
        actual_wait = wait_time + 5  # Add 5 seconds buffer
        
        logger.info(f"⏳ Waiting {actual_wait} seconds before retry...")
        
        # Wait in chunks to allow for interruption
        chunk_size = 10  # Wait in 10-second chunks
        for i in range(0, actual_wait, chunk_size):
            remaining = actual_wait - i
            wait_chunk = min(chunk_size, remaining)
            
            await asyncio.sleep(wait_chunk)
            
            if i + wait_chunk < actual_wait:
                logger.info(f"⏳ Still waiting... {actual_wait - i - wait_chunk}s remaining")
        
        logger.info(f"✅ FloodWait completed for {operation_name}")
        return True
    
    def reset_counter(self):
        """Reset FloodWait counter after successful operation"""
        self.flood_wait_count = 0


def with_flood_wait_handler(max_retries: int = 3):
    """
    Decorator untuk auto-handle FloodWait errors
    
    Usage:
        @with_flood_wait_handler(max_retries=3)
        async def my_function():
            # Your code that might trigger FloodWait
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            handler = FloodWaitHandler(max_retries=max_retries)
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    handler.reset_counter()
                    return result
                    
                except FloodWait as e:
                    if attempt == max_retries:
                        logger.error(f"❌ FloodWait in {func.__name__}: Max retries exceeded")
                        raise
                    
                    retry_ok = await handler.handle_flood_wait(e, func.__name__)
                    if not retry_ok:
                        raise
                    
                    logger.info(f"🔄 Retrying {func.__name__} (attempt {attempt + 2}/{max_retries + 1})")
                    continue
                    
                except Exception as e:
                    logger.error(f"❌ Error in {func.__name__}: {e}", exc_info=True)
                    raise
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


# Global instances
graceful_handler = GracefulShutdown()
flood_handler = FloodWaitHandler()


async def safe_restart():
    """Safely restart the bot"""
    logger.info("🔄 Initiating safe restart...")
    
    from anony import stop
    
    try:
        # Stop all services
        await stop()
        
        logger.info("✅ Services stopped successfully")
        logger.info("🔄 Restarting in 3 seconds...")
        
        await asyncio.sleep(3)
        
        # Restart using execv
        import os
        python = sys.executable
        os.execv(python, [python] + sys.argv)
        
    except Exception as e:
        logger.error(f"❌ Restart failed: {e}", exc_info=True)
        sys.exit(1)
