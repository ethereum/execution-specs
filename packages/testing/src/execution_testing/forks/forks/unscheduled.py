"""
Forks for unscheduled features.

Each feature fork enables the EIPs of one unscheduled feature on top of the
latest fork, or on top of the fork that the feature pins as its `base`. The
specs build the matching fork on demand from `src/ethereum/unscheduled/`, so a
feature fork only runs when selected with `--fork`.

Each feature fork also gets a transition fork from its base fork, so tests can
check what changes when the feature activates.
"""

from ..transition_base_fork import TransitionBaseClass, transition_fork
from .eips.unscheduled.eip_7666 import EIP7666
from .forks import Bogota

LatestFork = Bogota
"""
Newest fork, which every feature fork builds on unless the feature pins a
`base` fork. Move it forward whenever a new fork is added, since the specs
build unpinned features on the newest fork.
"""


class EvmifiedIdentity(EIP7666, LatestFork, deployed=False):
    """EIP-7666: EVM-ify the identity precompile."""

    pass


@transition_fork(
    to_fork=EvmifiedIdentity, from_fork=LatestFork, at_timestamp=15_000
)
class BogotaToEvmifiedIdentityAtTime15k(TransitionBaseClass):
    """Bogota to Evmified Identity transition at Timestamp 15k."""

    pass
