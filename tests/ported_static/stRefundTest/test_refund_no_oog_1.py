"""
Test_refund_no_oog_1.

Ported from:
state_tests/stRefundTest/refund_NoOOG_1Filler.json

@manually-enhanced: Do not overwrite. The transaction supplies exactly
enough gas to clear one cold storage slot (1 -> 0) and no more (the "no
out-of-gas" boundary). EIP-8038 raises the cold SSTORE-clear charge from
5000 to 13000, so the gas limit must rise by that charge delta to keep
the slot clearing instead of running out of gas. The asserted sender
balance equals its start minus `gas_used * gas_price`, and `gas_used`
is the gross gas minus the storage-clear refund (capped by EIP-3529 only
at Amsterdam). Both the gas limit bump and the balance shift are derived
from the fork gas model and are exactly 0 pre-EIP-8037; do not hardcode
the Amsterdam values.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_NoOOG_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_no_oog_1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_refund_no_oog_1."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0xA03F70)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 1 ]] 0 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    # EIP-8038 raises the cold SSTORE-clear charge and EIP-2780 shifts
    # the tx intrinsic; bump the gas limit by both deltas so the clear
    # still lands exactly at the limit (the "no out-of-gas" boundary)
    # instead of running out of gas.
    sstore_charge = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=0
    ).gas_cost(fork)
    cold_clear_delta = sstore_charge - 5000
    # ``return_cost_deducted_prior_execution=True`` returns the
    # upfront-deducted intrinsic only (Prague's calc would otherwise
    # return ``max(intrinsic, EIP-7623 floor)``).
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True,
    )
    intrinsic_delta = intrinsic - 21_000

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=26006 + cold_clear_delta + intrinsic_delta,
    )

    # Gas used = gross gas minus the capped storage-clear refund. The
    # non-SSTORE gross gas comes from the fork's intrinsic calculator
    # (covers TX_BASE and any EIP-2780 recipient surcharge) plus the
    # two PUSH1s that feed the single SSTORE (STOP is free).
    gas_costs = fork.gas_costs()
    base_gross = intrinsic + 2 * gas_costs.VERY_LOW
    cancun_base_gross = 21_000 + 2 * gas_costs.VERY_LOW

    def clear_gas_used(charge: int, clear_refund: int, gross_base: int) -> int:
        gross = gross_base + charge
        return gross - min(clear_refund, gross // 5)

    # Cancun charges 5000 for the clear and refunds 4800; subtracting the
    # same model evaluated at those constants and the Cancun base makes
    # this exactly 0 before the EIP-8037/8038 repricing.
    gas_used_delta = clear_gas_used(
        sstore_charge, gas_costs.REFUND_STORAGE_CLEAR, base_gross
    ) - clear_gas_used(5000, 4800, cancun_base_gross)

    post = {
        target: Account(storage={}),
        coinbase: Account(balance=0),
        sender: Account(balance=0x9D0314 - 10 * gas_used_delta, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
