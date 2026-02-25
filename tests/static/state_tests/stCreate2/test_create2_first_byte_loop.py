"""
Ported from:
tests/static/state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml

contract code:
    push32 0x600060005360016000f300000000000000000000000000000000000000000000
    push1 0x00
    mstore
    push1 0x24
    calldataload
    push1 0x04
    calldataload
    jumpdest
    dup2
    dup2
    lt
    push1 0x38
    jumpi
    push1 0x01
    push2 0x0100
    sstore
    stop
    jumpdest
    dup1
    push1 0x01
    ... (21 more instructions)
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
    ["tests/static/state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "1a8451e6000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000ef00000000000000000000000000000000000000000000000000000000000000f0",
        "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000100",
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_create2_first_byte_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc4a2ca1058df329e5da4755f9921ddaf05cbaa06")
    contract = Address("0x09fdd11d68be787a4c43f692a0778befc011cd35")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0x600060005360016000f300000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x24] + Op.CALLDATALOAD + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.JUMPDEST + Op.DUP2 + Op.DUP2 + Op.LT + Op.PUSH1[0x38]
        + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH2[0x100] + Op.SSTORE + Op.STOP
        + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x1] + Op.SWAP2 + Op.DUP3 + Op.MSTORE8
        + Op.PUSH1[0x0] + Op.PUSH1[0xa] + Op.DUP2 + Op.DUP1 + Op.CREATE2 + Op.ISZERO
        + Op.PUSH1[0x4f] + Op.JUMPI + Op.JUMPDEST + Op.ADD + Op.PUSH1[0x2a] + Op.JUMP
        + Op.JUMPDEST + Op.DUP2 + Op.DUP2 + Op.SSTORE + Op.PUSH1[0x4a] + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0x3b9aca00, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
