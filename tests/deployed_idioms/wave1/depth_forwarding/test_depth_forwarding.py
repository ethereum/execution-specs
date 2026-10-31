"""
Class #6: compounded depth forwarding.

`call(gas(), ...)` hands the child all but `avail // 64`
(`max_message_call_gas`, amsterdam/vm/gas.py:861), so down a chain of
depth *n* the leaf runs on roughly `(63/64)**n` of the budget the root
frame had. Proxy chains, routers, hooks and relayer stacks all build such
chains; L5 witnessed **38,325 instances across 142 runtimes**.

The invariant the deepest frame relies on is that it still has enough left
to do its work. Nothing in the chain states a gas literal, so a
frozen-budget test cannot express it: the budget at the leaf is a pure
function of the retention fraction and the chain's length.

Two markers, written by the leaf, sensitive in opposite directions:

  `leaf_committed`        -- the deepest frame completed a fresh storage
                             write. Fails if the retention fraction
                             *tightens*, or if per-frame cost grows.

  `compounded_below_half` -- the leaf's own `GAS` reading is less than half
                             the root's. `ln 2 / ln(64/63) = 44.014`, so
                             the crossing sits between 43 and 45 hops and
                             *is* a measurement of the divisor. Fails if
                             the retention fraction *loosens*: at
                             `63/64 -> 127/128` the crossing moves to
                             ~89 hops, at `63/64 -> 255/256` to ~178.

The second marker contains no gas literal at all -- it compares two `GAS`
readings by a ratio -- which is why it is fork-independent. Measured
identical, to the basis point, on Berlin, Osaka and Amsterdam.

Measurements: `tests/tools/test_cls6_depth_probe.py`; tables in README.md.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SLOT_LEAF = 0x01
SLOT_COMPOUNDED = 0x02

# calldata and memory layout, 0x40 bytes wide:
#   [0x00] hops remaining
#   [0x20] the root frame's `GAS` reading, forwarded down unchanged
#   [0x40] this frame's own entry `GAS` reading (memory only)
OFF_N = 0x00
OFF_ROOT_GAS = 0x20
OFF_MY_GAS = 0x40

# Every measured number in this file was taken at this budget. The budget
# fixes where the cliff is, so it is part of the measurement, not a free
# parameter: see README.md before changing it.
ROOT_GAS = 4_000_000


def _chain_link() -> Bytecode:
    """
    One link of a self-recursive forwarding chain.

    Each frame reads its own `GAS` first, then either recurses with
    `gas=GAS` -- the shape that triggers the 63/64 clamp -- or, at
    `hops == 0`, commits the leaf's two markers. Every frame is the same
    address, so the leaf's writes land in one account the test can assert
    on, and intermediate frames write nothing.
    """
    return (
        Op.MSTORE(OFF_MY_GAS, Op.GAS)
        + Conditional(
            condition=Op.ISZERO(Op.CALLDATALOAD(OFF_N)),
            if_true=(
                Op.SSTORE(SLOT_LEAF, 1)
                + Op.SSTORE(
                    SLOT_COMPOUNDED,
                    Op.LT(
                        Op.MUL(Op.MLOAD(OFF_MY_GAS), 2),
                        Op.CALLDATALOAD(OFF_ROOT_GAS),
                    ),
                )
            ),
            if_false=(
                Op.MSTORE(OFF_N, Op.SUB(Op.CALLDATALOAD(OFF_N), 1))
                + Op.MSTORE(OFF_ROOT_GAS, Op.CALLDATALOAD(OFF_ROOT_GAS))
                + Op.POP(
                    Op.CALL(
                        gas=Op.GAS,
                        address=Op.ADDRESS,
                        value=0,
                        args_offset=OFF_N,
                        args_size=0x40,
                        ret_offset=0,
                        ret_size=0,
                    )
                )
            ),
        )
        + Op.STOP
    )


def _chain_root(chain: Address, hops: int) -> Bytecode:
    """
    The frame that takes the reference `GAS` reading and starts the chain.

    The memory is pre-expanded before the reading so the first `CALL` pays
    no expansion cost after it, keeping the reference reading comparable
    with every frame below.
    """
    return (
        Op.MSTORE(OFF_N, hops - 1)
        + Op.MSTORE(OFF_MY_GAS, 0)
        + Op.MSTORE(OFF_ROOT_GAS, Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=chain,
                value=0,
                args_offset=OFF_N,
                args_size=0x40,
                ret_offset=0,
                ret_size=0,
            )
        )
        + Op.STOP
    )


def _fill(
    state_test: StateTestFiller,
    pre: Alloc,
    hops: int,
    *,
    leaf: int,
    compounded: int,
) -> None:
    chain = pre.deploy_contract(_chain_link())
    root = pre.deploy_contract(_chain_root(chain, hops))
    storage = Storage().set_next_slot(SLOT_LEAF)
    storage.store_next(leaf, "leaf_committed")
    storage.store_next(compounded, "compounded_below_half")
    tx = Transaction(
        to=root,
        gas_limit=ROOT_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={chain: Account(storage=storage)}, tx=tx)


# The expectation table *is* the compounding law. `compounded` is
# `(63/64)**hops < 1/2`, and the measured basis-point ratio at each depth
# is in README.md. The crossing between 43 and 44 is where the divisor
# itself is pinned to within one hop; the 40 and 48 entries are the same
# statement with ~6% of margin on each side, so a failure pattern
# distinguishes "the divisor moved" from "per-frame cost drifted".
DEPTHS = [
    (1, 0),
    (2, 0),
    (4, 0),
    (8, 0),
    (16, 0),
    (32, 0),
    (40, 0),
    (43, 0),
    (44, 1),
    (48, 1),
    (64, 1),
    (96, 1),
    (128, 1),
]


@pytest.mark.parametrize(
    "hops,compounded",
    [pytest.param(h, c, id=f"hops_{h}") for h, c in DEPTHS],
)
@pytest.mark.valid_from("Berlin")
def test_depth_chain_leaf_commits(
    state_test: StateTestFiller,
    pre: Alloc,
    hops: int,
    compounded: int,
) -> None:
    """
    Test the leaf of a `hops`-deep forwarding chain still does its work.

    `leaf_committed` is the survival invariant: the deepest frame creates
    a storage slot that did not exist, which is the most heavily repriced
    operation in Ethereum's history, on whatever `(63/64)**hops` of the
    budget leaves it.

    `compounded_below_half` is the same rule read as a ratio rather than
    an absolute: measured 5,061 basis points at 43 hops and 4,982 at 44,
    identical on Berlin, Osaka and Amsterdam, so the crossing is at 44.
    The ideal powers are 5,080 and 5,001 -- 45 is the first integer power
    strictly below one half -- and the 19-basis-point gap is each hop's own
    per-frame cost. README.md states what each side of the bracket is
    sensitive to; the margins are small by design.

    A failure means either the deepest frame of a realistic call chain no
    longer completes, or the fraction each hop keeps back has changed.
    """
    _fill(state_test, pre, hops, leaf=1, compounded=compounded)


# --------------------------------------------------------------------------
# Where the cliff is, and that EIP-8037 moved it
# --------------------------------------------------------------------------

# Measured cliff at ROOT_GAS with a leaf that creates two fresh slots:
#   Berlin..Osaka   leaf commits at 256 hops, dead by 320
#   Amsterdam       leaf commits at 184 hops, dead at 188
# 192 sits between the two cliffs, so the same chain, at the same depth,
# on the same budget, succeeds before EIP-8037 and fails after it.
CLIFF_HOPS = 192


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_depth_cliff_leaf_commits_at_192_hops(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a 192-hop chain still reaches a committing leaf before EIP-8037.

    At 192 hops the leaf holds 456 basis points of the root's budget, a
    measured ~181,000 gas. Two fresh slots cost 2 x 22,100 = 44,200 here,
    so the leaf clears its work by 4x.
    """
    _fill(state_test, pre, CLIFF_HOPS, leaf=1, compounded=1)


@pytest.mark.valid_from("EIP8037")
def test_depth_cliff_leaf_dies_at_192_hops_from_eip8037(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the identical 192-hop chain no longer reaches its leaf.

    The compounded budget is unchanged -- the ratio measurements are
    identical on every fork -- but the leaf's work is not: EIP-8037 took a
    fresh slot from 22,100 to 110,020, so two of them need 220,040 plus
    the leaf's own arithmetic, where the leaf has ~181,000. **EIP-8037 therefore shortened the maximum
    useful forwarding chain for a fixed budget, from beyond 256 hops to
    between 184 and 187.**

    Pinned as the negative arm of a measured pair: the test above is the
    identical chain on the forks where it survives. If a later fork makes
    this commit again, this test fails and the one above starts applying,
    which is the signal we want rather than silence.
    """
    _fill(state_test, pre, CLIFF_HOPS, leaf=0, compounded=0)
