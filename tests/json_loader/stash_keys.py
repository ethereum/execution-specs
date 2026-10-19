"""Shared StashKey definitions for json_loader tests."""

from execution_testing.evm_tools.t8n import ForkCache
from pytest import StashKey

desired_forks_key = StashKey[list[str]]()
fork_cache_key = StashKey[ForkCache]()
