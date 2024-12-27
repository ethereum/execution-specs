"""
Initializes the config package.

The config package is responsible for loading and managing application-wide
environment configurations, making them accessible throughout the application.
"""

# This import is done to facilitate cleaner imports in the project
# `from config import AppConfig` instead of `from config.app import AppConfig`
from .app import AppConfig
from .docs import DocsConfig
from .env import EnvConfig

__all__ = ["AppConfig", "DocsConfig", "EnvConfig"]
