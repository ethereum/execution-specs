"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stRefundTest/refundFFFiller.yml

@manually-enhanced: Do not overwrite. The post-state asserts the sender
balance, which equals its start minus `gas_used * gas_price`. The
contract self-destructs and sends its (zero) balance to a cold, already
existing beneficiary; EIP-8038 raises the cold account-access surcharge
from 2600 to 3000. No positive balance is moved, so no `ACCOUNT_WRITE`
applies and there is no refund, so `gas_used` rises by exactly the
SELFDESTRUCT charge delta. Derive that delta from the fork gas model
(0 pre-EIP-8037) and subtract `gas_price * delta` from the Cancun
balance; do not hardcode the Amsterdam value.
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
    ["state_tests/stRefundTest/refundFFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_ff(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D6599218, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    addr = pre.fund_eoa(amount=0)  # noqa: F841
    # Source: yul
    # berlin
    # {
    #    selfdestruct(<eoa:0xdddddddddddddddddddddddddddddddddddddddd>)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=addr),
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

    # EIP-8038 raises the cold account-access surcharge applied by
    # SELFDESTRUCT; with no balance transfer and no refund, gas_used
    # rises by exactly this charge delta.
    selfdestruct_delta = (
        Op.SELFDESTRUCT.with_metadata(
            address_warm=False, account_new=False
        ).gas_cost(fork)
        - 7600
    )
    # EIP-2780 lowers the intrinsic for non-self non-value txs; the
    # delta is negative on Amsterdam, so it reduces ``gas_used`` and
    # raises the sender balance correspondingly.
    intrinsic_delta = fork.transaction_intrinsic_cost_calculator()() - 21_000
    gas_used_delta = selfdestruct_delta + intrinsic_delta

    post = {sender: Account(balance=0xE8D4A51000 - 1000 * gas_used_delta)}

    state_test(env=env, pre=pre, post=post, tx=tx)
