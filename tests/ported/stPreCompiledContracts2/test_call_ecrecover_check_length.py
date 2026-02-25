"""
Ported from:
tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthFiller.json

contract code:
    push32 0x1122334455667788990011223344556677889900112233445566778899001122
    push1 0x80
    mstore
    push32 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c
    push1 0x00
    mstore
    push1 0x1c
    push1 0x20
    mstore
    push32 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f
    push1 0x40
    mstore
    push32 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549
    push1 0x60
    mstore
    push1 0x20
    push1 0x80
    push1 0x80
    push1 0x00
    push1 0x00
    ... (13 more instructions)
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
    ["tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_check_length(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

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
        Op.PUSH32[0x1122334455667788990011223344556677889900112233445566778899001122]
        + Op.PUSH1[0x80] + Op.MSTORE
        + Op.PUSH32[0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1c] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH3[0x493e0] + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.MSIZE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
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
