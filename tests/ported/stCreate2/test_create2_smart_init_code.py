"""
create2SmartInitCode. create2 works different each time you call it

Ported from:
tests/static/state_tests/stCreate2/create2SmartInitCodeFiller.json

callee code:
    push27 0x600060015414601157600a6000f3601a565b60016001556001ff5b
    push1 0x00
    mstore
    push1 0x00
    push1 0x1b
    push1 0x05
    push1 0x01
    create2
    push1 0x01
    sstore
    push1 0x00
    push1 0x1b
    push1 0x05
    push1 0x01
    create2
    push1 0x02
    sstore
    stop

callee_1 code:
    push29 0x600060015414601157600a6000f3601c565b6001600155600a6000f35b
    push1 0x00
    mstore
    push1 0x00
    push1 0x1d
    push1 0x03
    push1 0x01
    create2
    push1 0x01
    sstore
    push1 0x00
    push1 0x1b
    push1 0x05
    push1 0x01
    create2
    push1 0x02
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    call
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
    ["tests/static/state_tests/stCreate2/create2SmartInitCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000000f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
        "0000000000000000000000001f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_create2_smart_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """create2SmartInitCode. create2 works different each time you call it."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
    callee_1 = Address("0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    pre[callee] = Account(
        balance=100,
        nonce=0,
        code=(
        Op.PUSH27[0x600060015414601157600a6000f3601a565b60016001556001ff5b]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1b] + Op.PUSH1[0x5]
        + Op.PUSH1[0x1] + Op.CREATE2 + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x5] + Op.PUSH1[0x1] + Op.CREATE2 + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=100,
        nonce=0,
        code=(
        Op.PUSH29[0x600060015414601157600a6000f3601c565b6001600155600a6000f35b]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1d] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.CREATE2 + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x5] + Op.PUSH1[0x1] + Op.CREATE2 + Op.PUSH1[0x2]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x6400000000, nonce=0)
    pre[contract] = Account(
        balance=0x6400000000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
