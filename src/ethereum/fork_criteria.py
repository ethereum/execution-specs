"""
Activation criteria for forks.

Most generally, a _fork_ is a divergence in a blockchain resulting in multiple
tips. Most forks are short lived, and can be caused by networking issues or the
behavior of block creators. These short-lived forks resolve themselves
according to the rules of the protocol, eventually settling back to a single
tip of the chain.

A second class of forks are intentionally created by changing the rules of the
protocol, and never resolve back to a single tip. Older software will continue
to follow the original fork, while updated software will create and follow a
new fork.

For these intentional forks to succeed, all participants need to agree on
exactly when to switch rules. The agreed upon criteria are represented by
subclasses of [`ForkCriteria`], like [`ByBlockNumber`] and [`ByTimestamp`]. The
special type of [`Unscheduled`] is used for forks in active development that do
not yet have a scheduled deployment.

[`ForkCriteria`]: ref:ethereum.fork_criteria.ForkCriteria
[`ByBlockNumber`]: ref:ethereum.fork_criteria.ByBlockNumber
[`ByTimestamp`]: ref:ethereum.fork_criteria.ByTimestamp
[`Unscheduled`]: ref:ethereum.fork_criteria.Unscheduled
"""

import functools
from abc import ABC, abstractmethod
from typing import Final, Literal, SupportsInt, Tuple

from ethereum_types.numeric import U256, Uint


@functools.total_ordering
class ForkCriteria(ABC):
    """
    Abstract base class for conditions specifying when a fork activates.

    Subclasses override the comparison methods ([`__eq__`] and [`__lt__`]) to
    provide an ordering for forks, and override [`check`] to determine whether
    a particular block meets the activation criteria.

    [`__eq__`]: ref:ethereum.fork_criteria.ForkCriteria.__eq__
    [`__lt__`]: ref:ethereum.fork_criteria.ForkCriteria.__lt__
    [`check`]: ref:ethereum.fork_criteria.ForkCriteria.check
    """

    BLOCK_NUMBER: Final[int] = 0
    """
    Value representing a fork criteria based on the block's number.

    Used for pre-merge blocks.
    """

    TIMESTAMP: Final[int] = 1
    """
    Value representing a fork criteria based on the block's timestamp.

    Used for post-merge blocks.
    """

    UNSCHEDULED: Final[int] = 2
    """
    Value representing a fork criteria that will never be satisfied.

    Used for in-development forks.
    """

    _internal: Tuple[int, int]

    def __eq__(self, other: object) -> bool:
        """
        Equality for fork criteria.
        """
        if isinstance(other, ForkCriteria):
            return self._internal == other._internal
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        """
        Less-than comparison function, with earlier forks being less than later
        forks.

        All [`BLOCK_NUMBER`] forks come before [`TIMESTAMP`] forks, and all
        scheduled forks come before [`UNSCHEDULED`] forks.

        [`BLOCK_NUMBER`]: ref:ethereum.fork_criteria.ForkCriteria.BLOCK_NUMBER
        [`TIMESTAMP`]: ref:ethereum.fork_criteria.ForkCriteria.TIMESTAMP
        [`UNSCHEDULED`]: ref:ethereum.fork_criteria.ForkCriteria.UNSCHEDULED
        """
        if isinstance(other, ForkCriteria):
            return self._internal < other._internal
        return NotImplemented

    def __hash__(self) -> int:
        """
        Compute a hash for this instance, so it can be stored in dictionaries.
        """
        return hash(self._internal)

    @abstractmethod
    def check(self, block_number: Uint, timestamp: U256) -> bool:
        """
        Check whether fork criteria have been met.

        Returns `True` when the current block meets or exceeds the criteria,
        and `False` otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def __repr__(self) -> str:
        """
        String representation of this object.
        """
        raise NotImplementedError()


class ByBlockNumber(ForkCriteria):
    """
    Forks that occur when a specific block number has been reached.
    """

    block_number: Uint
    """
    Number of the first block in this fork.
    """

    def __init__(self, block_number: SupportsInt):
        self._internal = (ForkCriteria.BLOCK_NUMBER, int(block_number))
        self.block_number = Uint(int(block_number))

    def check(self, block_number: Uint, timestamp: U256) -> bool:
        """
        Check whether the block number has been reached.

        Returns `True` when the given `block_number` is equal to or greater
        than [`block_number`], and `False` otherwise.

        [`block_number`]: ref:ethereum.fork_criteria.ByBlockNumber.block_number
        """
        return block_number >= self.block_number

    def __repr__(self) -> str:
        """
        String representation of this object.
        """
        return f"ByBlockNumber({self.block_number})"


class ByTimestamp(ForkCriteria):
    """
    Forks that occur when a specific timestamp has been reached.
    """

    timestamp: U256
    """
    First instance of time that is part of this fork.
    """

    def __init__(self, timestamp: SupportsInt):
        self._internal = (ForkCriteria.TIMESTAMP, int(timestamp))
        self.timestamp = U256(timestamp)

    def check(self, block_number: Uint, timestamp: U256) -> bool:
        """
        Check whether the timestamp has been reached.

        Returns `True` when the given `timestamp` is equal to or greater than
        [`timestamp`], and `False` otherwise.

        [`timestamp`]: ref:ethereum.fork_criteria.ByTimestamp.timestamp
        """
        return timestamp >= self.timestamp

    def __repr__(self) -> str:
        """
        String representation of this object.
        """
        return f"ByTimestamp({self.timestamp})"


class Unscheduled(ForkCriteria):
    """
    Forks that have not been scheduled.
    """

    def __init__(self) -> None:
        self._internal = (ForkCriteria.UNSCHEDULED, 0)

    def check(self, block_number: Uint, timestamp: U256) -> Literal[False]:
        """
        Unscheduled forks never occur; always returns `False`.
        """
        return False

    def __repr__(self) -> str:
        """
        String representation of this object.
        """
        return "Unscheduled()"
