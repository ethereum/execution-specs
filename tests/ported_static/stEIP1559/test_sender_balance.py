"""
The origin balance seen during execution of an EIP-1559 transaction is
computed from the effective gas price, not the maximum gas price used in the
transaction validity check.

Ported from:
state_tests/stEIP1559/senderBalanceFiller.yml

@manually-enhanced: Do not overwrite. Balance derived from gas/fee inputs.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/senderBalanceFiller.yml"],
)
@pytest.mark.valid_from("London")
def test_sender_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Origin balance during execution reflects the effective gas price."""
    base_fee = 11
    priority_fee = 100
    max_fee = 1000
    sender_balance = 0xDE0B6B3A7640000

    # The effective gas price is base + priority (kept below max_fee, so the
    # validity check would reserve more — the point of the test).
    effective_gas_price = base_fee + priority_fee

    env = Environment(base_fee_per_gas=base_fee)
    sender = pre.fund_eoa(amount=sender_balance)

    # Source: yul: { sstore(0, balance(caller())) }
    target_code = (
        Op.SSTORE(
            key=0x0,
            value=Op.BALANCE(address=Op.CALLER, address_warm=False),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.STOP
    )
    target = pre.deploy_contract(code=target_code)

    # Size the gas limit to the work done, so the upfront charge (and thus the
    # observed balance) tracks the fork's costs rather than a magic number.
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + target_code.gas_cost(fork)
        + 1000
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=gas_limit,
        max_fee_per_gas=max_fee,
        max_priority_fee_per_gas=priority_fee,
    )

    post = {
        target: Account(
            storage={0: sender_balance - gas_limit * effective_gas_price}
        )
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
