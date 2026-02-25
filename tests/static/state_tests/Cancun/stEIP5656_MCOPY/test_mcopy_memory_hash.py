"""
Performs exact the same MCOPY twice and dumps the hash of all memory after each MCOPY

Ported from:
tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_hashFiller.yml

contract code:
    push32 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf
    push2 0x1020
    mstore
    push1 0x32
    push1 0x40
    calldataload
    push1 0x20
    calldataload
    push0
    calldataload
    push1 0x4e
    jump
    jumpdest
    msize
    push0
    sha3
    push1 0x01
    sstore
    push1 0x46
    push1 0x40
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
    ["tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_hashFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000000000000000000000000000000000000000103000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001020",
        "000000000000000000000000000000000000000000000000000000000000101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020",
        "000000000000000000000000000000000000000000000000000000000000102000000000000000000000000000000000000000000000000000000000000010100000000000000000000000000000000000000000000000000000000000000010",
        "000000000000000000000000000000000000000000000000000000000000102000000000000000000000000000000000000000000000000000000000000010400000000000000000000000000000000000000000000000000000000000000010",
        "00000000000000000000000000000000000000000000000000000000000010200000000000000000000000000000000000000000000000000000000000001023000000000000000000000000000000000000000000000000000000000000001d",
        "000000000000000000000000000000000000000000000000000000000000102100000000000000000000000000000000000000000000000000000000000010200000000000000000000000000000000000000000000000000000000000000123",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5'],
)
@pytest.mark.pre_alloc_mutable
def test_mcopy_memory_hash(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Performs exact the same MCOPY twice and dumps the hash of all memory after each MCOPY."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc4a2ca1058df329e5da4755f9921ddaf05cbaa06")
    contract = Address("0xff4c22cd1d160fdc49c752dfb44b55d318d14113")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1687174231,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x3b9aca00, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH32[0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf]
        + Op.PUSH2[0x1020] + Op.MSTORE + Op.PUSH1[0x32] + Op.PUSH1[0x40]
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.CALLDATALOAD + Op.PUSH0
        + Op.CALLDATALOAD + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST + Op.MSIZE
        + Op.PUSH0 + Op.SHA3 + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x46]
        + Op.PUSH1[0x40] + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH0 + Op.CALLDATALOAD + Op.PUSH1[0x4e] + Op.JUMP + Op.JUMPDEST
        + Op.MSIZE + Op.PUSH0 + Op.SHA3 + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
        + Op.JUMPDEST + Op.MCOPY + Op.JUMP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
