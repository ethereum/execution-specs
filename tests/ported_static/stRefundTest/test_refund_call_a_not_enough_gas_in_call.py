"""
Test_refund_call_a_not_enough_gas_in_call.

Ported from:
state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts the sender
fee, `gas_used * gas_price`. The inner CALL is starved of gas so its
SSTORE clear always reverts (no refund survives); the only surviving
repricing is in the outer frame, where EIP-8038 raises the
`COLD_ACCOUNT_ACCESS` charged by the CALL and the cold no-op SSTORE of
slot 0. Derive both deltas from the fork gas model (0 pre-EIP-8037) and
add `call_access_delta + outer_sstore_delta` to the Cancun gas used; do
not hardcode the Amsterdam value.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    GasFee,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_refund_call_a_not_enough_gas_in_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_refund_call_a_not_enough_gas_in_call."""
    sender = pre.fund_eoa()

    # Source: lll
    # { [[ 1 ]] 0 }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
    )
    # Source: lll
    # { [[ 0 ]] (CALL 5005 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x138D,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=85000,
        value=10,
    )

    # The inner SSTORE clear always reverts (gas-starved), so its refund
    # never survives. Only the outer frame reprices under EIP-8038: the
    # cold account access charged by the CALL and the cold no-op SSTORE
    # of slot 0 (original == current == new == 0).
    gas_costs = fork.gas_costs()
    call_access_delta = (
        gas_costs.COLD_ACCOUNT_ACCESS - Cancun.gas_costs().COLD_ACCOUNT_ACCESS
    )
    outer_sstore = Op.SSTORE.with_metadata(
        key_warm=False, original_value=0, current_value=0, new_value=0
    )
    cancun_outer_sstore = outer_sstore.gas_cost(Cancun)
    outer_sstore_delta = outer_sstore.gas_cost(fork) - cancun_outer_sstore
    gas_used_delta = call_access_delta + outer_sstore_delta

    post = {
        target: Account(storage={1: 1}, balance_change=tx.value),
        sender: Account(
            balance_change=-tx.value - GasFee(tx, gas=30829 + gas_used_delta)
        ),
        addr: Account(storage={1: 1}),
    }

    state_test(pre=pre, post=post, tx=tx)
