"""
Ported from:
tests/static/state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml

callee code:
    gas
    push1 0x00
    gas
    swap1
    swap2
    sub
    swap1
    sstore

callee_1 code:
    gas
    push0
    gas
    swap1
    swap2
    sub
    swap1
    sstore

contract code:
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    dup1
    calldataload
    push1 0x60
    shr
    push3 0x0186a0
    call
    push1 0x00
    sstore
    push1 0x01
    dup1
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
    ["tests/static/state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000000000000000001000",
        "0000000000000000000000000000000000000200",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_push0_gas2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0x0000000000000000000000000000000000000200")
    callee_1 = Address("0x0000000000000000000000000000000000001000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.GAS + Op.SWAP1 + Op.SWAP2 + Op.SUB + Op.SWAP1
        + Op.SSTORE
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.GAS + Op.PUSH0 + Op.GAS + Op.SWAP1 + Op.SWAP2 + Op.SUB + Op.SWAP1 + Op.SSTORE,
    )
    pre[sender] = Account(balance=0x989680, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.CALLDATALOAD + Op.PUSH1[0x60] + Op.SHR + Op.PUSH3[0x186a0] + Op.CALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP1 + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
