"""Test phase management for Ethereum tests."""

from contextlib import contextmanager
from enum import Enum
from typing import ClassVar, Iterator, Optional


class TestPhase(str, Enum):
    """Test phase for state and blockchain tests."""

    __test__ = False  # stop pytest from collecting this class as a test

    SETUP = "setup"
    # TODO: Change string to "execution", remain as "testing" for backwards
    # compatibility
    EXECUTION = "testing"
    CLEANUP = "cleanup"
    SYNC = "sync"
    """
    A framework-injected payload that exists only to make the chain
    syncable, such as the empty block the filler adds to a test's
    chain - appended above a valid chain's head, or prepended between
    genesis and a single invalid block - so that sync-based consumers
    can trigger a devp2p sync. Unlike ``SETUP``, a sync payload
    prepares no state a test depends on; consumers that replay
    payloads through the Engine API can treat it like any other block.
    """


class TestPhaseManager:
    """
    Manages test phases for transactions and blocks.

    This singleton class provides context managers for SETUP and
    EXECUTION phases. Transactions automatically detect and tag
    themselves with the current phase.

    Usage:
        with TestPhaseManager.setup():
            # Transactions created here have test_phase = SETUP
            setup_tx = Transaction(...)

        with TestPhaseManager.execution():
            # Transactions created here have test_phase = EXECUTION
            benchmark_tx = Transaction(...)
    """

    _current_phase: ClassVar[Optional[TestPhase]] = None

    @classmethod
    @contextmanager
    def setup(cls) -> Iterator[None]:
        """Context manager for the setup phase of a benchmark test."""
        old_phase = cls._current_phase
        cls._current_phase = TestPhase.SETUP
        try:
            yield
        finally:
            cls._current_phase = old_phase

    @classmethod
    @contextmanager
    def execution(cls) -> Iterator[None]:
        """Context manager for the execution phase of a test."""
        old_phase = cls._current_phase
        cls._current_phase = TestPhase.EXECUTION
        try:
            yield
        finally:
            cls._current_phase = old_phase

    @classmethod
    def get_current_phase(cls) -> Optional[TestPhase]:
        """Get the current test phase."""
        return cls._current_phase

    @classmethod
    def reset(cls) -> None:
        """Reset the phase state to None (primarily for testing)."""
        cls._current_phase = None
