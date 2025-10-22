"""Test phase management for Ethereum tests."""

from contextlib import contextmanager
from enum import Enum
from typing import ClassVar, Iterator, Optional


class TestPhase(Enum):
    """Test phase for state and blockchain tests."""

    SETUP = "setup"
    EXECUTION = "execution"


class TestPhaseManager:
    """
    Manages test phases for transactions and blocks.

    This singleton class provides context managers for "setup" and
    "execution" phases. Transactions automatically detect and tag
    themselves with the current phase.

    Usage:
        with TestPhaseManager.setup():
            # Transactions created here have test_phase = "setup"
            setup_tx = Transaction(...)

        with TestPhaseManager.execution():
            # Transactions created here have test_phase = "execution"
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
