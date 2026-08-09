"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stRefundTest/refundSSTOREFiller.yml

@manually-enhanced: Do not overwrite. The post-state asserts the sender
balance, which equals its start minus `gas_used * gas_price`. The
contract clears one cold storage slot (non-zero -> 0); EIP-8038 raises
the cold SSTORE-clear charge from 5000 to 13000 and the storage-clear
refund from 4800 to 12480. The EIP-3529 refund cap (`gas_used // 5`) does
not bind at Cancun but does at Amsterdam, so the shift is modeled from
the fork gas model: reconstruct the cap-bounded `gas_used` from the
fork-invariant non-SSTORE gross gas plus the fork SSTORE charge minus the
capped refund, and subtract the same expression evaluated with the
pre-repricing Cancun charges (so the adjustment is exactly 0
pre-EIP-8037). Do not hardcode the Amsterdam value.
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
    ["state_tests/stRefundTest/refundSSTOREFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D631F190, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    # Source: yul
    # berlin
    # {
    #    sstore(0,0x0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
        nonce=1,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=2601000,
        nonce=1,
        gas_price=1000,
        access_list=[],
    )

    # Gas used = gross gas minus the capped storage-clear refund. The
    # non-SSTORE gross gas comes from the fork's intrinsic calculator
    # (covers TX_BASE, calldata, and any EIP-2780 recipient surcharge)
    # plus the PUSH1 and DUP1 that feed the SSTORE (STOP is free).
    gas_costs = fork.gas_costs()
    # ``return_cost_deducted_prior_execution=True`` returns the
    # upfront-deducted intrinsic only. Without it, Prague's
    # ``intrinsic_calc`` returns ``max(intrinsic, EIP-7623 floor)`` —
    # the floor only binds for data-heavy txs with little execution,
    # which is not the case here.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx.data,
        return_cost_deducted_prior_execution=True,
    )
    base_gross = intrinsic + 2 * gas_costs.VERY_LOW
    # Cancun's intrinsic for this tx shape was 21_004 (TX_BASE +
    # single zero-byte). Capture it as the baseline so the Cancun
    # branch of ``gas_used_delta`` evaluates at the original base.
    cancun_base_gross = 21_004 + 2 * gas_costs.VERY_LOW

    def clear_gas_used(
        sstore_charge: int, clear_refund: int, gross_base: int
    ) -> int:
        gross = gross_base + sstore_charge
        return gross - min(clear_refund, gross // 5)

    sstore_charge = Op.SSTORE.with_metadata(
        key_warm=False, original_value=24743, current_value=24743, new_value=0
    ).gas_cost(fork)
    # Cancun charges 5000 for the clear and refunds 4800; subtracting the
    # same model evaluated at those constants and the Cancun base makes
    # this exactly 0 before the EIP-8037/8038 repricing.
    gas_used_delta = clear_gas_used(
        sstore_charge, gas_costs.REFUND_STORAGE_CLEAR, base_gross
    ) - clear_gas_used(5000, 4800, cancun_base_gross)

    post = {sender: Account(balance=0xE8D4EE4E00 - 1000 * gas_used_delta)}

    state_test(env=env, pre=pre, post=post, tx=tx)
