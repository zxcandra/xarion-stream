# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
Enhanced helpers module with new utilities
"""

from anony.helpers._admins import *
from anony.helpers._cleanup import cleanup
from anony.helpers._dataclass import *
from anony.helpers._decorators import (
    command_limiter,
    play_limiter,
    require_rate_limit,
    safe_execute,
    search_limiter,
)
from anony.helpers._exec import *
from anony.helpers._graceful import (
    FloodWaitHandler,
    GracefulShutdown,
    graceful_handler,
    flood_handler,
    safe_restart,
    with_flood_wait_handler,
)
from anony.helpers._inline import Inline
from anony.helpers._lyrics import lyrics_searcher
from anony.helpers._play import *
from anony.helpers._queue import Queue
from anony.helpers._thumbnails import *
from anony.helpers._utilities import *

# Create button instance
buttons = Inline()

# Export all
__all__ = [
    # Cleanup
    "cleanup",
    # Decorators
    "safe_execute",
    "require_rate_limit",
    "play_limiter",
    "search_limiter",
    "command_limiter",
    # Graceful shutdown
    "graceful_handler",
    "flood_handler",
    "safe_restart",
    "with_flood_wait_handler",
    "GracefulShutdown",
    "FloodWaitHandler",
    # Lyrics
    "lyrics_searcher",
    # Buttons
    "buttons",
    # Queue
    "Queue",
    # Others (from existing modules)
    "Inline",
]
