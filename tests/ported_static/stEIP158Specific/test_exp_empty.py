"""
Measure the gas cost of EXP with a zero base or a zero exponent across
exponent widths (the per-byte exponent charge applies only to the
exponent operand).

Ported from:
state_tests/stEIP158Specific/EXP_EmptyFiller.json

@manually-enhanced: Do not overwrite. The eight measurement windows are
generated from one case list and every stored delta is derived from
opcode metadata (`exponent=` drives the per-byte charge); the transaction
budget is fork-derived.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# (base, exponent) pairs: a zero on either side, exponent widths 1-32.
EXP_CASES = [
    (0x0, 0xC),
    (0xC, 0x0),
    (0x0, 2**64 - 1),
    (0x0, 2**128 - 1),
    (0x0, 2**256 - 1),
    (2**64 - 1, 0x0),
    (2**128 - 1, 0x0),
    (2**256 - 1, 0x0),
]


@pytest.mark.ported_from(
    ["state_tests/stEIP158Specific/EXP_EmptyFiller.json"],
)
@pytest.mark.valid_from("Berlin")
def test_exp_empty(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure EXP's cost for zero-base and zero-exponent operands."""
    code = Bytecode()
    storage: dict = {}
    budget = 0
    for i, (base, exponent) in enumerate(EXP_CASES):
        result = 1 if exponent == 0 else 0
        result_slot = 1 + 2 * i
        # The last window stores its delta at slot 100, as ported.
        delta_slot = 0x64 if i == len(EXP_CASES) - 1 else result_slot + 1

        lead = Op.MSTORE(
            offset=0x0,
            value=Op.GAS,
            new_memory_size=0x20,
            old_memory_size=0x0 if i == 0 else 0x20,
        )
        exp_store = Op.SSTORE(
            key=result_slot,
            value=Op.EXP(base, exponent, exponent=exponent),
            key_warm=False,
            original_value=0,
            new_value=result,
        )
        # The window's measured delta: both GAS reads cancel out of the
        # two composites' sum.
        measured = lead.gas_cost(fork) + exp_store.gas_cost(fork)
        delta_store = Op.SSTORE(
            key=delta_slot,
            value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS),
            key_warm=False,
            original_value=0,
            new_value=measured,
        )
        code += lead + exp_store + delta_store
        storage[result_slot] = result
        storage[delta_slot] = measured
        budget += measured + delta_store.gas_cost(fork) + 9

    target = pre.deploy_contract(code=code + Op.STOP)

    # Fork-derived budget with an EIP-2200 stipend margin for the final
    # store.
    gas_limit = fork.transaction_intrinsic_cost_calculator()() + budget + 5_000

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=target,
        gas_limit=gas_limit,
    )

    post = {target: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
