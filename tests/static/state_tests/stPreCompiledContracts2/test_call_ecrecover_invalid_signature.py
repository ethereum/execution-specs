"""
CALL to ECREC precompile with input which is a completely invalid signature and a 32 byte output range in memory. ECREC should return an empty response and the 32 byte output range should be left unchanged.

Ported from:
tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverInvalidSignatureFiller.json

contract code:
    push32 0x1122334455667788991011121314151617181920212223242526272829303132
    push1 0x80
    mstore
    push1 0x20
    push1 0x80
    push1 0x80
    push1 0x00
    push1 0x00
    push1 0x01
    push3 0x0493e0
    call
    pop
    push1 0x80
    mload
    push1 0x00
    sstore
    stop
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverInvalidSignatureFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_invalid_signature(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL to ECREC precompile with input which is a completely invalid signature and a 32 byte output range in memory. ECREC should return an empty response and the 32 byte output range should be left unchanged.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x2b8fd4adb0602fe9ee5823b0576f619daefbd369")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH32[0x1122334455667788991011121314151617181920212223242526272829303132]
        + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH3[0x493e0] + Op.CALL + Op.POP + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3652240,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
