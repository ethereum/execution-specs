"""
Ported from:
tests/static/state_tests/stStaticCall/static_ABAcalls1Filler.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc1eb8f73f2e1e269acd146c961210b665078841b
    push3 0x0186a0
    gas
    sub
    staticcall
    push1 0x01
    add
    pc
    mstore
    stop

callee_1 code:
    pc
    push1 0x01
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x5e75046384134a4554c3c7061d4637cb978d5699
    push3 0x0186a0
    gas
    sub
    staticcall
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xd0a73d84aa7112e8d5179cae211b268d16dafd73
    push3 0x0186a0
    gas
    sub
    staticcall
    push1 0x01
    add
    pc
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xcc7901b70dcec81d198ac6cf196ef14bca9870be
    push3 0x0186a0
    gas
    sub
    staticcall
    pc
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
    push1 0x00
    sstore
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_ABAcalls1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000d0a73d84aa7112e8d5179cae211b268d16dafd73",
        "000000000000000000000000c1eb8f73f2e1e269acd146c961210b665078841b",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_ab_acalls1(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xe7fe01f115e85f0487086659fa9bbf09579b0e3a")
    callee = Address("0x5e75046384134a4554c3c7061d4637cb978d5699")
    callee_1 = Address("0xc1eb8f73f2e1e269acd146c961210b665078841b")
    callee_2 = Address("0xcc7901b70dcec81d198ac6cf196ef14bca9870be")
    callee_3 = Address("0xd0a73d84aa7112e8d5179cae211b268d16dafd73")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc1eb8f73f2e1e269acd146c961210b665078841b] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.PUSH1[0x1] + Op.ADD + Op.PC + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PC + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5e75046384134a4554c3c7061d4637cb978d5699] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd0a73d84aa7112e8d5179cae211b268d16dafd73] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.PUSH1[0x1] + Op.ADD + Op.PC + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xcc7901b70dcec81d198ac6cf196ef14bca9870be] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.PC + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1000000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
