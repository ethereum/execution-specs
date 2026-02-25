"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallSha256_2Filler.json

contract code:
    push5 0xf34578907f
    push1 0x05
    mstore
    push1 0x20
    push1 0x00
    push1 0x25
    push1 0x00
    push1 0x02
    push2 0x01f4
    staticcall
    push1 0x02
    sstore
    push1 0x00
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
    ["tests/static/state_tests/stStaticCall/static_CallSha256_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_sha256_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc3764ef9b916cf39bbc2f0092b1c2e792f160cb1")

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
        Op.PUSH5[0xf34578907f] + Op.PUSH1[0x5] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH1[0x25] + Op.PUSH1[0x0] + Op.PUSH1[0x2]
        + Op.PUSH2[0x1f4] + Op.STATICCALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=365224,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
