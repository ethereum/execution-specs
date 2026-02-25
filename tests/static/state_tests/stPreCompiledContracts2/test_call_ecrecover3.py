"""
Ported from:
tests/static/state_tests/stPreCompiledContracts2/CallEcrecover3Filler.json

contract code:
    push32 0x2f380a2dea7e778d81affc2443403b8fe4644db442ae4862ff5bb3732829cdb9
    push1 0x00
    mstore
    push1 0x1b
    push1 0x20
    mstore
    push32 0x6b65ccb0558806e9b097f27a396d08f964e37b8b7af6ceeb516ff86739fbea0a
    push1 0x40
    mstore
    push32 0x37cbc8d883e129a4b1ef9d5f1df53c4f21a3ef147cf2a50a4ede0eb06ce092d4
    push1 0x60
    mstore
    push1 0x20
    push1 0x80
    push1 0x80
    push1 0x00
    push1 0x00
    push1 0x01
    push3 0x0186a0
    call
    ... (17 more instructions)
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
    ["tests/static/state_tests/stPreCompiledContracts2/CallEcrecover3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x28d98d7cc227972a80fa4a16964272bf8738d792")

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
        Op.PUSH32[0x2f380a2dea7e778d81affc2443403b8fe4644db442ae4862ff5bb3732829cdb9]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1b] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x6b65ccb0558806e9b097f27a396d08f964e37b8b7af6ceeb516ff86739fbea0a]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x37cbc8d883e129a4b1ef9d5f1df53c4f21a3ef147cf2a50a4ede0eb06ce092d4]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0xa0]
        + Op.PUSH1[0x2] + Op.EXP + Op.PUSH1[0x80] + Op.MLOAD + Op.MOD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.SLOAD + Op.ORIGIN + Op.EQ + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
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
