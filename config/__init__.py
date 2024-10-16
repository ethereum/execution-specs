"""
This module initializes the config package.

The config package is responsible for loading and managing application-wide
environment configurations, making them accessible throughout the application.
"""

# This import is done to facilitate cleaner imports in the project
# `from config import AppConfig` instead of `from config.app import AppConfig`
from .app import AppConfig  # noqa: 401
from .docs import DocsConfig  # noqa: 401
from .env import EnvConfig  # noqa: 401
