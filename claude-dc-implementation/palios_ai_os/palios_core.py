#!/usr/bin/env python3

"""
PALIOS AI OS - Main Module Import

This file provides convenient imports from the core PALIOS implementation.
"""

# Import and re-export core components
from palios_ai_os.core.palios_core import *

# Ensure the singleton instance is accessible
from palios_ai_os.core.palios_core import palios_core as palios_os
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI

# Re-export the main constants and singleton for convenient access
__all__ = ['palios_os', 'PHI', 'BACH_PATTERN', 'FIBONACCI']
