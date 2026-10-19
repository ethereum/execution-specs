"""
Verify the EIP-150 "all but one 64th" rounding at the transaction level: the
gas available when a subcall asks for more than the transaction provided is
floored as `base - base // 64`, probed with the base exactly divisible by
64 and one gas below/above it.

Ported from:
state_tests/stEIP150Specific/Transaction64Rule_d64e0Filler.json
state_tests/stEIP150Specific/Transaction64Rule_d64m1Filler.json
state_tests/stEIP150Specific/Transaction64Rule_d64p1Filler.json

@manually-enhanced: Do not overwrite. Three fillers folded into one
parametrize; the callee reports its observed GAS so the exact forwarded
amount is asserted (`base - base // 64` differs from `base * 63 // 64` by
one whenever the base is not a multiple of 64 — the ported posts could not
see that difference); the tx gas limit is derived from the fork so the
divisibility residue holds on every fork.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_SLOT = 0x1
# Far larger than any gas the frame can hold: the clamp always applies.
OVERSIZED_GAS_ASK = 2**61


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/Transaction64Rule_d64e0Filler.json",
        "state_tests/stEIP150Specific/Transaction64Rule_d64m1Filler.json",
        "state_tests/stEIP150Specific/Transaction64Rule_d64p1Filler.json",
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "residue",
    [
        pytest.param(0, id="d64e0"),
        pytest.param(-1, id="d64m1"),
        pytest.param(1, id="d64p1"),
    ],
)
def test_transaction64_rule(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    residue: int,
) -> None:
    """A subcall asking above the tx budget receives `base - base // 64`."""
    # Callee returns the gas it observed on entry back to the caller.
    gas_return_contract = pre.deploy_contract(
        code=Op.MSTORE(0, Op.GAS, new_memory_size=0x20) + Op.RETURN(0, 0x20),
    )

    call_code = Op.CALL(
        gas=OVERSIZED_GAS_ASK,
        address=gas_return_contract,
        ret_size=0x20,
        address_warm=False,
        account_new=False,
        new_memory_size=0x20,
    )
    # The observed-gas store is the only op after the call; the callee's
    # returned surplus always covers it.
    store_code = Op.SSTORE(
        key=GAS_SLOT,
        value=Op.MLOAD(0),
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    caller = pre.deploy_contract(code=call_code + store_code + Op.STOP)

    # Choose the 63/64 rounding base: large enough that the frame can
    # afford the trailing store from what the callee hands back, shaped to
    # the parametrized residue mod 64. The +1024 margin absorbs the ops
    # around the store.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    min_base = store_code.gas_cost(fork) + 1024
    base = -(-min_base // 64) * 64 + residue
    assert base < OVERSIZED_GAS_ASK, "the 63/64 clamp must apply"
    gas_limit = intrinsic + call_code.gas_cost(fork) + base

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=gas_limit,
    )

    # The EVM floors the forwarded gas as `base - base // 64`; the callee
    # observes it minus its own GAS opcode. An implementation using
    # `base * 63 // 64` is exactly one gas short on the m1/p1 residues.
    forwarded = base - base // 64
    expected_gas = forwarded - Op.GAS.gas_cost(fork)

    post = {caller: Account(storage={GAS_SLOT: expected_gas})}

    state_test(pre=pre, post=post, tx=tx)
