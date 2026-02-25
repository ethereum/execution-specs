"""
Ported from:
tests/static/state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json

contract code:
    gas
    push1 0x08
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xfd59abae521384b5731ac657616680219fbc423d
    push3 0x0927c0
    delegatecall
    push1 0x09
    sstore
    gas
    push1 0x08
    mload
    sub
    push1 0x08
    sstore
    stop

callee code:
    push1 0x12
    push1 0x00
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
    ["tests/static/state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x90bc108216940a7ddaf3ba6624f2fdbe4c5e83dc")
    callee = Address("0xfd59abae521384b5731ac657616680219fbc423d")

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
        Op.GAS + Op.PUSH1[0x8] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xfd59abae521384b5731ac657616680219fbc423d] + Op.PUSH3[0x927c0]
        + Op.DELEGATECALL + Op.PUSH1[0x9] + Op.SSTORE + Op.GAS + Op.PUSH1[0x8]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0x8] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x12] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
