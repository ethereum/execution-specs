"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stRefundTest/refundMaxFiller.yml

@manually-enhanced: Do not overwrite. The post-state asserts the sender
balance, which equals its start minus `gas_used * gas_price`. The
contract clears eight cold storage slots; EIP-8038 raises each cold
SSTORE-clear charge from 5000 to 13000. The EIP-3529 refund cap
(`gas_used // 5`) binds at both forks (the clear refunds far exceed a
fifth of gas used), so the extra charge raises `gas_used` by exactly
four fifths of itself. Derive the per-clear charge delta from the fork
gas model (0 pre-EIP-8037) and subtract `gas_price * 8 * delta * 4 // 5`
from the Cancun balance; do not hardcode the Amsterdam value.
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
    ["state_tests/stRefundTest/refundMaxFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_max(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D848C3A0, nonce=1)

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
    #    let newVal := 0
    #    sstore(0x00,newVal)
    #    sstore(0x01,newVal)
    #    sstore(0x02,newVal)
    #    sstore(0x03,newVal)
    #    sstore(0x04,newVal)
    #    sstore(0x05,newVal)
    #    sstore(0x06,newVal)
    #    sstore(0x07,newVal)
    #
    #    // Get rid of Yul optimizations
    #    newVal := msize()
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.SSTORE(key=0x2, value=Op.DUP1)
        + Op.SSTORE(key=0x3, value=Op.DUP1)
        + Op.SSTORE(key=0x4, value=Op.DUP1)
        + Op.SSTORE(key=0x5, value=Op.DUP1)
        + Op.SSTORE(key=0x6, value=Op.DUP1)
        + Op.PUSH1[0x7]
        + Op.SSTORE
        + Op.STOP,
        storage={
            0: 24743,
            1: 24743,
            2: 24743,
            3: 24743,
            4: 24743,
            5: 24743,
            6: 24743,
            7: 24743,
        },
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

    # EIP-8038 raises each cold SSTORE-clear charge and EIP-2780
    # shifts the tx intrinsic. With the EIP-3529 refund cap binding,
    # gas_used rises by 4/5 of the gross-gas delta.
    cold_clear_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=1, current_value=1, new_value=0
        ).gas_cost(fork)
        - 5000
    )
    intrinsic_delta = fork.transaction_intrinsic_cost_calculator()() - 21_000
    gross_delta = 8 * cold_clear_delta + intrinsic_delta
    extra_gas_used = gross_delta * 4 // 5

    post = {sender: Account(balance=0xE8D55F7E90 - 1000 * extra_gas_used)}

    state_test(env=env, pre=pre, post=post, tx=tx)
