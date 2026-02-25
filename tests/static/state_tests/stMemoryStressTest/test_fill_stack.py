"""
Ported from:
tests/static/state_tests/stMemoryStressTest/FillStackFiller.json

coinbase code:
    push1 0x00
    calldataload
    sload
    iszero
    push1 0x09
    jumpi
    stop
    jumpdest
    push1 0x20
    calldataload
    push1 0x00
    calldataload
    sstore

contract code:
    jumpdest
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push32 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
    gaslimit
    push32 0x010000000000000000000000000000000000000000
    push32 0x01
    push32 0xc350
    number
    jumpi
    iszero
    mstore8
    sha3
    dup1
    gasprice
    swap8
    sstore
    push1 0x00
    mload
    sstore
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
    ["tests/static/state_tests/stMemoryStressTest/FillStackFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        3141592,
        16777216,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_fill_stack(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0xded0d7993c3e6100a321e038900a8114c05ddf51")
    contract = Address("0x709ee68118ab00ce0bab659c9aa89744b35703fa")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.GASLIMIT + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x1] + Op.PUSH32[0xc350] + Op.NUMBER + Op.JUMPI + Op.ISZERO
        + Op.MSTORE8 + Op.SHA3 + Op.DUP1 + Op.GASPRICE + Op.SWAP8 + Op.SSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0x152d02c7e14af6800000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x23000fe3d08cdeba75eb2e2e2909f842dbf48aa0c566f49101e8285c8dec62d6"
        ),
        to=contract,
        data=bytes.fromhex("5b7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe457f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3504357155320803a97"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=264050067,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
