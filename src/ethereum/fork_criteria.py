"""
Fork Criteria
^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Classes for specifying criteria for Mainnet forks.
"""

import functools
from abc import ABC, abstractmethod
from typing import Final, Tuple


# MyPy doesn't support decorators on abstract classes
# See https://github.com/python/mypy/issues/4717
@functools.total_ordering  # type: ignore
class ForkCriteria(ABC):
    """
    Type that represents the condition required for a fork to occur.
    """

    BLOCK_NUMBER: Final[int] = 0
    TIMESTAMP: Final[int] = 1
    UNSCHEDULED: Final[int] = 2

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
        Ordering for fork criteria. Block number forks are before timestamp
        forks and scheduled forks are before unscheduled forks.
        """
        if isinstance(other, ForkCriteria):
            return self._internal < other._internal
        return NotImplemented

    def __hash__(self) -> int:
        """
        `ForkCriteria` is hashable, so it can be stored in dictionaries.
        """
        return hash(self._internal)

    @abstractmethod
    def check(self, block_number: int, timestamp: int) -> bool:
        """
        Check whether fork criteria have been met.
        """
        ...

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

    block_number: int

    def __init__(self, block_number: int):
        self._internal = (ForkCriteria.BLOCK_NUMBER, block_number)
        self.block_number = block_number

    def check(self, block_number: int, timestamp: int) -> bool:
        """
        Check whether the block number has been reached.
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

    timestamp: int

    def __init__(self, timestamp: int):
        self._internal = (ForkCriteria.TIMESTAMP, timestamp)
        self.timestamp = timestamp

    def check(self, block_number: int, timestamp: int) -> bool:
        """
        Check whether the timestamp has been reached.
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

    def check(self, block_number: int, timestamp: int) -> bool:
        """
        Unscheduled forks never occur.
        """
        return False

    def __repr__(self) -> str:
        """
        String representation of this object.
        """
        return "Unscheduled()"
