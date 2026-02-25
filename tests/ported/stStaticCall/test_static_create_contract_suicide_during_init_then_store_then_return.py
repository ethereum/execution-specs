"""
Ported from:
tests/static/state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json

contract code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_2 code:
    push1 0x0c
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x0c
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "600060006000600073c94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273d94f5374fce5edbc8e2a8697c15331677e6ebf0bff600060006000600073d94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa50600b600055600e6012f3",
        "600060006000600073094f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273d94f5374fce5edbc8e2a8697c15331677e6ebf0bff600060006000600073194f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa50600b600055600e6012f3",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_create_contract_suicide_during_init_then_store_then_return(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x094f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_1 = Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_2 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_3 = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=tx_data,
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
