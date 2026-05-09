"""
Configuration module for TDOA Automation System
Provides centralized configuration management
"""

from config.settings import Settings
from config.constants import Constants
from config.environments import get_environment_config

__all__ = ['Settings', 'Constants', 'get_environment_config']

# Initialize default settings
settings = Settings()
constants = Constants()
