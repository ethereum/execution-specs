"""
Ported from:
tests/static/state_tests/Shanghai/stEIP3860_limitmeterinitcode/create2InitCodeSizeLimitFiller.yml

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x00
    dup1
    calldatasize
    dup2
    dup1
    push20 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b
    push3 0x989680
    call
    push1 0x00
    sstore
    push1 0x01
    dup1
    sstore
    stop

callee code:
    push10 0x600a80600080396000f3
    push1 0xb0
    shl
    push1 0x00
    swap1
    dup2
    mstore
    calldataload
    push4 0xdeadbeef
    gas
    swap2
    push1 0x00
    dup1
    create2
    swap1
    gas
    swap1
    sub
    push1 0x0a
    sstore
    ... (3 more instructions)
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
    ["tests/static/state_tests/Shanghai/stEIP3860_limitmeterinitcode/create2InitCodeSizeLimitFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000000000000000000000000000000000000000c001",
        "000000000000000000000000000000000000000000000000000000000000c000",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_create2_init_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    pre[sender] = Account(balance=0xbebc200, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.CALLDATASIZE + Op.DUP2 + Op.DUP1
        + Op.PUSH20[0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.PUSH3[0x989680]
        + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP1 + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH10[0x600a80600080396000f3] + Op.PUSH1[0xb0] + Op.SHL + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.CALLDATALOAD + Op.PUSH4[0xdeadbeef]
        + Op.GAS + Op.SWAP2 + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE2 + Op.SWAP1 + Op.GAS
        + Op.SWAP1 + Op.SUB + Op.PUSH1[0xa] + Op.SSTORE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=15000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
