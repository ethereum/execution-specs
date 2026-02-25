"""
Ported from:
tests/static/state_tests/stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b
    push3 0x0249f0
    call
    pop
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee code:
    push21 0x6d64600c6000556000526005601bf36000526001ff
    push1 0x00
    mstore
    push1 0x00
    push1 0x15
    push1 0x0b
    push1 0x01
    create2
    pop
    push1 0x0b
    push1 0x00
    sstore
    push1 0x0e
    push1 0x12
    return
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
    ["tests/static/state_tests/stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_contract_suicide_during_init_then_store_then_return(
    state_test: StateTestFiller,
    pre: Alloc,
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[contract] = Account(
        balance=0xe8d4a51000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xe8d4a51000,
        nonce=0,
        code=(
        Op.PUSH21[0x6d64600c6000556000526005601bf36000526001ff] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x15] + Op.PUSH1[0xb] + Op.PUSH1[0x1]
        + Op.CREATE2 + Op.POP + Op.PUSH1[0xb] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0xe] + Op.PUSH1[0x12] + Op.RETURN + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
