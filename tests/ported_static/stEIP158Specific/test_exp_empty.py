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
    Fork,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP158Specific/EXP_EmptyFiller.json"],
)
@pytest.mark.parametrize(
    "base,exponent",
    [
        # (base, exponent) pairs: a zero on either side, exponent widths 1-32.
        (0x0, 0xC),
        (0xC, 0x0),
        (0x0, 2**64 - 1),
        (0x0, 2**128 - 1),
        (0x0, 2**256 - 1),
        (2**64 - 1, 0x0),
        (2**128 - 1, 0x0),
        (2**256 - 1, 0x0),
    ],
)
@pytest.mark.valid_from("Frontier")
def test_exp_empty(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    base: int,
    exponent: int,
) -> None:
    """Measure EXP's cost for zero-base and zero-exponent operands."""
    storage = Storage()

    result = 1 if exponent == 0 else 0

    exp_code = Op.EXP(base, exponent, exponent=exponent)
    code = (
        Op.GAS
        + exp_code
        + Op.GAS  # [gas_1, exp_result, gas_2]
        + Op.SSTORE(
            key=storage.store_next(result), value=Op.SWAP1
        )  # [gas_1, gas_2]
        + Op.SWAP1  # [gas_2, gas_1]
        + Op.SSTORE(
            key=storage.store_next(
                Op.GAS.gas_cost(fork) + exp_code.gas_cost(fork)
            ),
            value=Op.SUB,
        )
        + Op.STOP
    )

    target = pre.deploy_contract(code=code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=target,
        protected=fork.supports_protected_txs(),
    )

    post = {target: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
