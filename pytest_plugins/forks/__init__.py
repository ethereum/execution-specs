"""
A pytest plugin to configure the forks in the test session. It parametrizes
tests based on the user-provided fork range the tests' specified validity
markers.
"""

from .forks import fork_covariant_parametrize

__all__ = ["fork_covariant_parametrize"]
