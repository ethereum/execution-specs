"""Test suite for TestPhaseManager functionality."""

import pytest

from ethereum_test_base_types import Address
from ethereum_test_tools import Transaction

from ..phase_manager import TestPhase, TestPhaseManager


@pytest.fixture(autouse=True)
def reset_phase_manager() -> None:
    """Reset TestPhaseManager singleton state before each test."""
    TestPhaseManager.reset()


def test_test_phase_enum_values() -> None:
    """Test that TestPhase enum has correct values."""
    assert TestPhase.SETUP.value == "setup"
    assert TestPhase.EXECUTION.value == "execution"


def test_phase_manager_class_state() -> None:
    """Test TestPhaseManager uses class-level state."""
    # All access is through class methods, no instance needed
    assert TestPhaseManager.get_current_phase() is None

    # Setting phase through class method
    with TestPhaseManager.setup():
        assert TestPhaseManager.get_current_phase() == TestPhase.SETUP

    # Phase persists at class level
    assert TestPhaseManager.get_current_phase() is None


def test_default_phase_is_none() -> None:
    """Test that default phase is None (no context set)."""
    assert TestPhaseManager.get_current_phase() is None


def test_transaction_auto_detects_default_phase() -> None:
    """Test that transactions default to None when no phase set."""
    tx = Transaction(to=Address(0x123), value=100, gas_limit=21000)
    assert tx.test_phase is None


def test_transaction_auto_detects_setup_phase() -> None:
    """Test that transactions created in setup context get SETUP phase."""
    with TestPhaseManager.setup():
        tx = Transaction(to=Address(0x456), value=50, gas_limit=21000)
        assert tx.test_phase == TestPhase.SETUP


def test_phase_context_switching() -> None:
    """Test that phase switching works correctly."""
    # Start with no phase set (defaults to None)
    tx1 = Transaction(to=Address(0x100), value=100, gas_limit=21000)
    assert tx1.test_phase is None

    # Switch to SETUP
    with TestPhaseManager.setup():
        assert TestPhaseManager.get_current_phase() == TestPhase.SETUP
        tx2 = Transaction(to=Address(0x200), value=200, gas_limit=21000)
        assert tx2.test_phase == TestPhase.SETUP

    # Back to None after context (transactions default to None)
    assert TestPhaseManager.get_current_phase() is None
    tx3 = Transaction(to=Address(0x300), value=300, gas_limit=21000)
    assert tx3.test_phase is None


def test_nested_phase_contexts() -> None:
    """Test that nested phase contexts work correctly."""
    with TestPhaseManager.setup():
        tx1 = Transaction(to=Address(0x100), value=100, gas_limit=21000)
        assert tx1.test_phase == TestPhase.SETUP

        # Nested execution context
        with TestPhaseManager.execution():
            tx2 = Transaction(to=Address(0x200), value=200, gas_limit=21000)
            assert tx2.test_phase == TestPhase.EXECUTION

        # Back to setup after nested context
        tx3 = Transaction(to=Address(0x300), value=300, gas_limit=21000)
        assert tx3.test_phase == TestPhase.SETUP


@pytest.mark.parametrize(
    ["num_setup_txs", "num_exec_txs"],
    [
        pytest.param(0, 1, id="exec_only"),
        pytest.param(1, 0, id="setup_only"),
        pytest.param(3, 5, id="mixed"),
        pytest.param(10, 10, id="many"),
    ],
)
def test_multiple_transactions_phase_tagging(
    num_setup_txs: int, num_exec_txs: int
) -> None:
    """Test that multiple transactions are correctly tagged by phase."""
    setup_txs = []
    exec_txs = []

    # Create setup transactions
    with TestPhaseManager.setup():
        for i in range(num_setup_txs):
            tx = Transaction(
                to=Address(0x1000 + i), value=i * 10, gas_limit=21000
            )
            setup_txs.append(tx)

    # Create execution transactions
    for i in range(num_exec_txs):
        tx = Transaction(to=Address(0x2000 + i), value=i * 20, gas_limit=21000)
        exec_txs.append(tx)

    # Verify all setup transactions have SETUP phase
    for tx in setup_txs:
        assert tx.test_phase == TestPhase.SETUP

    # Verify all execution transactions have None phase (no context set)
    for tx in exec_txs:
        assert tx.test_phase is None


def test_phase_reset() -> None:
    """Test that reset() restores default phase."""
    # Change phase
    with TestPhaseManager.setup():
        pass

    # Manually set to SETUP
    TestPhaseManager._current_phase = TestPhase.SETUP
    assert TestPhaseManager.get_current_phase() == TestPhase.SETUP

    # Reset should restore None
    TestPhaseManager.reset()
    assert TestPhaseManager.get_current_phase() is None


def test_class_state_shared() -> None:
    """Test that phase state is shared at class level."""
    # Phase changes are visible globally since it's class-level state
    assert TestPhaseManager.get_current_phase() is None

    with TestPhaseManager.setup():
        # All access to the class sees the same phase
        assert TestPhaseManager.get_current_phase() == TestPhase.SETUP

        # Transactions created during this context get SETUP phase
        tx = Transaction(to=Address(0x789), value=75, gas_limit=21000)
        assert tx.test_phase == TestPhase.SETUP

    # After context, phase returns to None
    assert TestPhaseManager.get_current_phase() is None
