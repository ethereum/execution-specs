"""
The checks a header must pass against its parent, each pinned on both sides.

A random parent gets a child built to be valid from the framework's
calculators: its base fee and excess blob gas, a gas limit within the
allowed step, the next number and a later timestamp. That child must be
valid. Each case then makes the smallest change that breaks one rule, or
moves to the last value a rule still allows.
"""

from dataclasses import dataclass, fields, replace
from types import ModuleType
from typing import Any, Callable, Dict

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint
from execution_testing.forks import Fork
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import validate_header, zeroed
from .strategies import MAX_U64, ints

# Proof of work headers carry checks of their own (EIP-3675).
pytestmark = requires(lambda fork: fork.header_zero_difficulty_required())

# Yellow Paper: a block's gas limit moves less than 1/1024 of its parent's,
# and never below this minimum. The framework's `minimum_block_gas_limit()`
# also counts what an empty block's access list needs from EIP-7928 on,
# which execution enforces, not the header.
GAS_LIMIT_STEP_DIVISOR = 1024
GAS_LIMIT_MINIMUM = 5000
# Yellow Paper: extra data holds at most 32 bytes.
MAX_EXTRA_DATA = 32
# EIP-3675: a proof of stake header has no ommers.
EMPTY_OMMERS_HASH = keccak256(rlp.encode([]))
BLOB_GAS_BOUND = 1 << 30


def header(blocks: ModuleType, **values: Any) -> Any:
    """Return a fork's header with `values` set, where the fork has them."""
    names = {field.name for field in fields(blocks.Header)}
    return zeroed(
        blocks.Header, **{k: v for k, v in values.items() if k in names}
    )


def gas_limit_range(parent_gas_limit: int) -> range:
    """Return the gas limits a child of `parent_gas_limit` may have."""
    step = parent_gas_limit // GAS_LIMIT_STEP_DIVISOR
    lowest = max(parent_gas_limit - step + 1, GAS_LIMIT_MINIMUM)
    return range(lowest, parent_gas_limit + step)


@dataclass(frozen=True)
class Family:
    """A parent header and a child built to be valid against it."""

    parent: Any
    child: Any


@st.composite
def families(draw: st.DrawFn, fork: Fork, blocks: ModuleType) -> Family:
    """Return a random parent and its valid child."""
    parent_gas_limit = draw(
        st.one_of(
            st.just(GAS_LIMIT_MINIMUM),
            st.integers(GAS_LIMIT_MINIMUM, MAX_U64),
        )
    )
    parent_gas_used = draw(ints(parent_gas_limit))
    parent_base_fee = draw(ints(MAX_U64))
    parent_blob_gas_used = parent_excess_blob_gas = 0
    if fork.supports_blobs():
        blobs = draw(st.integers(0, fork.max_blobs_per_block()))
        parent_blob_gas_used = blobs * fork.blob_gas_per_blob()
        parent_excess_blob_gas = draw(ints(BLOB_GAS_BOUND))
    parent = header(
        blocks,
        number=Uint(draw(ints(MAX_U64 - 1))),
        timestamp=U256(draw(ints(MAX_U64 - 1))),
        gas_limit=Uint(parent_gas_limit),
        gas_used=Uint(parent_gas_used),
        base_fee_per_gas=Uint(parent_base_fee),
        blob_gas_used=U64(parent_blob_gas_used),
        excess_blob_gas=U64(parent_excess_blob_gas),
        ommers_hash=EMPTY_OMMERS_HASH,
    )

    gas_limit = draw(st.sampled_from(gas_limit_range(parent_gas_limit)))
    base_fee = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=parent_base_fee,
        parent_gas_used=parent_gas_used,
        parent_gas_limit=parent_gas_limit,
    )
    excess_blob_gas = 0
    if fork.header_excess_blob_gas_required():
        excess_blob_gas = fork.excess_blob_gas_calculator()(
            parent_excess_blob_gas=parent_excess_blob_gas,
            parent_blob_gas_used=parent_blob_gas_used,
            parent_base_fee_per_gas=parent_base_fee,
        )
    child = header(
        blocks,
        parent_hash=keccak256(rlp.encode(parent)),
        number=parent.number + Uint(1),
        timestamp=parent.timestamp + U256(draw(st.integers(1, 1 << 16))),
        gas_limit=Uint(gas_limit),
        gas_used=Uint(draw(ints(gas_limit))),
        base_fee_per_gas=Uint(base_fee),
        excess_blob_gas=U64(excess_blob_gas),
        extra_data=Bytes(draw(st.binary(max_size=MAX_EXTRA_DATA))),
        ommers_hash=EMPTY_OMMERS_HASH,
    )
    return Family(parent, child)


def with_child_gas_limit(family: Family, gas_limit: int) -> Family:
    """Return the family with the child's gas limit, and no gas used."""
    child = replace(family.child, gas_limit=Uint(gas_limit), gas_used=Uint(0))
    return Family(family.parent, child)


def change_child(**values: Any) -> Callable[[Family], Family]:
    """Return a case that sets `values` on the child."""
    return lambda family: Family(
        family.parent, replace(family.child, **values)
    )


@dataclass(frozen=True)
class Case:
    """One change from the valid child, and whether the child stays valid."""

    change: Callable[[Family], Family]
    valid: bool
    applies: Callable[[Family], bool] = lambda _: True
    """Whether the change can be made to this family at all."""


CASES: Dict[str, Case] = {
    "number_skips_one": Case(
        lambda f: Family(
            f.parent, replace(f.child, number=f.parent.number + Uint(2))
        ),
        valid=False,
    ),
    "number_zero": Case(change_child(number=Uint(0)), valid=False),
    "timestamp_one_after_the_parent": Case(
        lambda f: Family(
            f.parent,
            replace(f.child, timestamp=f.parent.timestamp + U256(1)),
        ),
        valid=True,
    ),
    "timestamp_equal_to_the_parent": Case(
        lambda f: Family(
            f.parent, replace(f.child, timestamp=f.parent.timestamp)
        ),
        valid=False,
    ),
    "gas_used_at_the_gas_limit": Case(
        lambda f: Family(
            f.parent, replace(f.child, gas_used=f.child.gas_limit)
        ),
        valid=True,
    ),
    "gas_used_past_the_gas_limit": Case(
        lambda f: Family(
            f.parent,
            replace(f.child, gas_used=f.child.gas_limit + Uint(1)),
        ),
        valid=False,
    ),
    "gas_limit_at_the_highest_step": Case(
        lambda f: with_child_gas_limit(
            f, gas_limit_range(int(f.parent.gas_limit))[-1]
        ),
        valid=True,
    ),
    "gas_limit_past_the_highest_step": Case(
        lambda f: with_child_gas_limit(
            f, gas_limit_range(int(f.parent.gas_limit))[-1] + 1
        ),
        valid=False,
    ),
    "gas_limit_at_the_lowest_step": Case(
        lambda f: with_child_gas_limit(
            f, gas_limit_range(int(f.parent.gas_limit))[0]
        ),
        valid=True,
    ),
    "gas_limit_past_the_lowest_step": Case(
        lambda f: with_child_gas_limit(
            f, gas_limit_range(int(f.parent.gas_limit))[0] - 1
        ),
        valid=False,
    ),
    "gas_limit_below_the_minimum": Case(
        lambda f: with_child_gas_limit(f, GAS_LIMIT_MINIMUM - 1),
        valid=False,
        applies=lambda f: int(f.parent.gas_limit) == GAS_LIMIT_MINIMUM,
    ),
    "base_fee_one_too_high": Case(
        lambda f: Family(
            f.parent,
            replace(
                f.child, base_fee_per_gas=f.child.base_fee_per_gas + Uint(1)
            ),
        ),
        valid=False,
    ),
    "base_fee_one_too_low": Case(
        lambda f: Family(
            f.parent,
            replace(
                f.child, base_fee_per_gas=f.child.base_fee_per_gas - Uint(1)
            ),
        ),
        valid=False,
        applies=lambda f: int(f.child.base_fee_per_gas) > 0,
    ),
    "extra_data_at_its_limit": Case(
        change_child(extra_data=Bytes(b"\x01" * MAX_EXTRA_DATA)), valid=True
    ),
    "extra_data_one_byte_too_long": Case(
        change_child(extra_data=Bytes(b"\x01" * (MAX_EXTRA_DATA + 1))),
        valid=False,
    ),
    "difficulty_not_zero": Case(change_child(difficulty=Uint(1)), valid=False),
    "nonce_not_zero": Case(
        change_child(nonce=Bytes8(b"\x00" * 7 + b"\x01")), valid=False
    ),
    "ommers_hash_not_empty": Case(
        change_child(ommers_hash=Bytes32(b"\x01" * 32)), valid=False
    ),
    "parent_hash_of_another_header": Case(
        change_child(parent_hash=Bytes32(b"\x01" * 32)), valid=False
    ),
}
# These rules do not depend on the drawn parent beyond the child being
# valid, so a few families cover them.
FIXED_CASES = {
    "number_skips_one",
    "number_zero",
    "timestamp_one_after_the_parent",
    "timestamp_equal_to_the_parent",
    "extra_data_at_its_limit",
    "extra_data_one_byte_too_long",
    "difficulty_not_zero",
    "nonce_not_zero",
    "ommers_hash_not_empty",
    "parent_hash_of_another_header",
}
FIXED_CASE_FAMILIES = 5
BLOB_CASES: Dict[str, Case] = {
    "excess_blob_gas_one_too_high": Case(
        lambda f: Family(
            f.parent,
            replace(f.child, excess_blob_gas=f.child.excess_blob_gas + U64(1)),
        ),
        valid=False,
    ),
    "excess_blob_gas_one_too_low": Case(
        lambda f: Family(
            f.parent,
            replace(f.child, excess_blob_gas=f.child.excess_blob_gas - U64(1)),
        ),
        valid=False,
        applies=lambda f: int(f.child.excess_blob_gas) > 0,
    ),
}


@pytest.mark.parametrize("case_name", sorted(CASES.keys() - FIXED_CASES))
@given(data=st.data())
def test_header_rule_boundary(
    spec: Hardfork,
    fork: Fork,
    blocks: ModuleType,
    case_name: str,
    data: st.DataObject,
) -> None:
    """
    A child built from the framework's calculators is valid, and the
    case's change either keeps it valid or makes the spec reject it.
    """
    check_case(spec, data.draw(families(fork, blocks)), CASES[case_name])


@pytest.mark.parametrize("case_name", sorted(FIXED_CASES))
@settings(max_examples=FIXED_CASE_FAMILIES)
@given(data=st.data())
def test_fixed_header_rule(
    spec: Hardfork,
    fork: Fork,
    blocks: ModuleType,
    case_name: str,
    data: st.DataObject,
) -> None:
    """The same, for a rule that ignores the drawn values."""
    check_case(spec, data.draw(families(fork, blocks)), CASES[case_name])


@requires(lambda fork: fork.header_excess_blob_gas_required())
@pytest.mark.parametrize("case_name", sorted(BLOB_CASES))
@given(data=st.data())
def test_blob_header_rule_boundary(
    spec: Hardfork,
    fork: Fork,
    blocks: ModuleType,
    case_name: str,
    data: st.DataObject,
) -> None:
    """The same, for the rules about blob gas."""
    family = data.draw(families(fork, blocks))
    check_case(spec, family, BLOB_CASES[case_name])


def check_case(spec: Hardfork, family: Family, case: Case) -> None:
    """Check the valid child, then the case's change to it."""
    fork_module = spec.module("fork")
    validate_header(fork_module, family.parent, family.child)

    assume(case.applies(family))
    changed = case.change(family)
    if case.valid:
        validate_header(fork_module, changed.parent, changed.child)
    else:
        with pytest.raises(InvalidBlock):
            validate_header(fork_module, changed.parent, changed.child)
