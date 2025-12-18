# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
Helpers module - exports utilities for other modules
All modules here use lazy imports internally to avoid circular imports
"""

# These modules don't have top-level anony imports (safe to import)
from anony.helpers._dataclass import Media, Track
from anony.helpers._queue import Queue

# Import classes/functions that use lazy imports internally
from anony.helpers._admins import admin_check, can_manage_vc, is_admin, reload_admins
from anony.helpers._inline import Inline
from anony.helpers._utilities import Utilities

# Create singleton instances
buttons = Inline()
utils = Utilities()

# Export all
__all__ = [
    # Dataclasses
    "Media",
    "Track",
    # Queue
    "Queue",
    # Admin utilities
    "admin_check",
    "can_manage_vc", 
    "is_admin",
    "reload_admins",
    # Instances
    "buttons",
    "utils",
    # Classes
    "Inline",
    "Utilities",
]
