"""
Measurement instrument, not a corpus test (class #6, compounded depth).

Its FAILURES ARE THE MEASUREMENT.

The leaf of a `hops`-deep chain writes two slots:
  `leaf`     = 1   -- asserted 1, so a PASS on this slot means the leaf ran
  `ratio_bp` = 10000 * leaf_gas / root_gas  -- asserted 0, so the failure
               prints the measured basis-point ratio

Reading the result:
  * both slots mismatch           -> leaf ran; `ratio_bp` is the measurement
  * only `leaf` mismatches (0x0)  -> the chain died before the leaf: the
                                     cliff is at or below this `hops`

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
      -k "cls6 and state_test and hops_64" --output /tmp/p6 -q --tb=line \
      -p no:cacheprovider
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

SLOT_LEAF = 0x01
SLOT_RATIO = 0x02

# calldata/memory layout, both 0x40 bytes wide
#   [0x00] hops remaining
#   [0x20] the root frame's `GAS` reading, forwarded unchanged
#   [0x40] this frame's own entry `GAS` reading (memory only)
OFF_N = 0
OFF_ROOT_GAS = 0x20
OFF_MY_GAS = 0x40


def recursive_link() -> Bytecode:
    """One link of a self-recursive forwarding chain."""
    return (
        Op.MSTORE(OFF_MY_GAS, Op.GAS)
        + Conditional(
            condition=Op.ISZERO(Op.CALLDATALOAD(OFF_N)),
            if_true=(
                Op.SSTORE(SLOT_LEAF, 1)
                + Op.SSTORE(
                    SLOT_RATIO,
                    Op.DIV(
                        Op.MUL(Op.MLOAD(OFF_MY_GAS), 10000),
                        Op.CALLDATALOAD(OFF_ROOT_GAS),
                    ),
                )
            ),
            if_false=(
                Op.MSTORE(OFF_N, Op.SUB(Op.CALLDATALOAD(OFF_N), 1))
                + Op.MSTORE(
                    OFF_ROOT_GAS, Op.CALLDATALOAD(OFF_ROOT_GAS)
                )
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


def root_link(chain: object, hops: int) -> Bytecode:
    """The frame that takes the reference `GAS` reading and forwards it."""
    return (
        Op.MSTORE(OFF_N, hops - 1)
        + Op.MSTORE(OFF_MY_GAS, 0)  # pre-expand memory, so the CALL below
        + Op.MSTORE(OFF_ROOT_GAS, Op.GAS)  # pays no expansion after the read
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


@pytest.mark.parametrize(
    "hops",
    # fmt: off
    [1, 2, 4, 8, 16, 32, 40, 43, 44, 45, 48, 64, 96, 128,
     176, 180, 184, 188, 192, 256, 320],
    # fmt: on
)
@pytest.mark.valid_from("Berlin")
def test_cls6_depth(
    state_test: StateTestFiller, pre: Alloc, hops: int
) -> None:
    """Probe."""
    chain = pre.deploy_contract(recursive_link())
    root = pre.deploy_contract(root_link(chain, hops))
    s = Storage().set_next_slot(SLOT_LEAF)
    s.store_next(1, "leaf")
    s.store_next(0, "ratio_bp")
    tx = Transaction(
        to=root,
        gas_limit=4_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={chain: Account(storage=s)}, tx=tx)
