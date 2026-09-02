"""
Test the fork gating of the environment fields some headers lack.
"""

from typing import Any, Dict, Set

import pytest

from execution_testing.forks import Amsterdam, Cancun, Fork, Istanbul, Paris

from ..block_types import Environment

PINS: Dict[str, Any] = {
    "prev_randao": 0x20000,
    "base_fee_per_gas": 10,
    "parent_base_fee_per_gas": 9,
    "withdrawals": [],
    "excess_blob_gas": 3,
    "blob_gas_used": 4,
    "parent_beacon_block_root": 5,
    "slot_number": 7,
}

DROPPED: Dict[Fork, Set[str]] = {
    Istanbul: set(PINS),
    Paris: {
        "withdrawals",
        "excess_blob_gas",
        "blob_gas_used",
        "parent_beacon_block_root",
        "slot_number",
    },
    Cancun: {"slot_number"},
    Amsterdam: set(),
}

fork_cases = pytest.mark.parametrize(
    "fork", list(DROPPED), ids=lambda fork: fork.name()
)


@fork_cases
def test_for_fork_keeps_only_the_fork_fields(fork: Fork) -> None:
    """Pins the fork's header lacks are dropped, the rest kept verbatim."""
    env = Environment.for_fork(fork, **PINS)
    for name, value in PINS.items():
        if name in DROPPED[fork]:
            assert getattr(env, name) is None, name
        else:
            assert getattr(env, name) == value, name


@fork_cases
@pytest.mark.parametrize("name", list(PINS))
def test_check_fork_fields(fork: Fork, name: str) -> None:
    """A pin the fork's header lacks raises and names the field."""
    env = Environment(**{name: PINS[name]})
    if name in DROPPED[fork]:
        with pytest.raises(ValueError, match=name):
            env.check_fork_fields(fork)
    else:
        env.check_fork_fields(fork)


@fork_cases
def test_fork_requirements_pass_the_check(fork: Fork) -> None:
    """The fields a fork requires never trip its own check."""
    Environment().set_fork_requirements(fork).check_fork_fields(fork)
