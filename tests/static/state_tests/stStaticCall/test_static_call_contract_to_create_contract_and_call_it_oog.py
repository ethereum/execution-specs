"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallContractToCreateContractAndCallItOOGFiller.json

contract code:
    push21 0x600c60005566602060406000f060205260076039f3
    push1 0x00
    mstore
    push1 0x15
    push1 0x0b
    push1 0x01
    create
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    sload
    push2 0x03e8
    staticcall
    pop
    push1 0x00
    push1 0x00
    ... (13 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_CallContractToCreateContractAndCallItOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00",
        "01",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_contract_to_create_contract_and_call_it_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH21[0x600c60005566602060406000f060205260076039f3] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x15] + Op.PUSH1[0xb] + Op.PUSH1[0x1] + Op.CREATE
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH2[0x3e8] + Op.STATICCALL
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.EQ
        + Op.PUSH1[0x40] + Op.JUMPI + Op.GAS + Op.PUSH1[0x48] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3 + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x5f5e100, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=2000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
