"""Forks that have stateless validation."""

from typing import List

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.loaders.fork_loader import ForkLoad

STATELESS_FORKS: List[Hardfork] = [
    fork for fork in Hardfork.discover() if ForkLoad(fork).has_stateless
]
"""
Forks with a `stateless` module, which also have the `execution_engine`
package that it builds on.
"""
