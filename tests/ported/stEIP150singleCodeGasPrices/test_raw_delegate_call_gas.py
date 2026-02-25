"""
Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json

contract code:
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xe497cd0909c3691e0b6d2a42e26f36696fc27ba5
    push2 0x7530
    delegatecall
    pop
    gas
    push1 0x00
    mload
    sub
    push1 0x01
    sstore
    stop

callee code:
    gas
    push1 0x02
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
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_delegate_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x8dfc4f381eee03447d510a61a1266821a480bd85")
    callee = Address("0xe497cd0909c3691e0b6d2a42e26f36696fc27ba5")

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
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe497cd0909c3691e0b6d2a42e26f36696fc27ba5] + Op.PUSH2[0x7530]
        + Op.DELEGATECALL + Op.POP + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(balance=0, nonce=0, code=Op.GAS + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP)
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=500000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
