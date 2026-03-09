"""Shared StashKey definitions for json_infra tests."""

from pytest import StashKey

from ethereum_spec_tools.evm_tools.t8n import ForkCache

desired_forks_key = StashKey[list[str]]()
fork_cache_key = StashKey[ForkCache]()
