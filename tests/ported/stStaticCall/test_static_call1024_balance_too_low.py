"""
Ported from:
tests/static/state_tests/stStaticCall/static_Call1024BalanceTooLowFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
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

callee code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    sload
    push20 0xd395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8
    push6 0x0fffffffffff
    staticcall
    push1 0x01
    sstore
    stop

callee_2 code:
    push1 0x01
    push1 0x00
    mload
    add
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    mload
    push20 0xe8f28ee50521b0388cf0a623b1a89e43d022c039
    push6 0x0fffffffffff
    staticcall
    push1 0x20
    mstore
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
    ["tests/static/state_tests/stStaticCall/static_Call1024BalanceTooLowFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000d395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8",
        "000000000000000000000000e8f28ee50521b0388cf0a623b1a89e43d022c039",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call1024_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0xd395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8")
    callee_1 = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")
    callee_2 = Address("0xe8f28ee50521b0388cf0a623b1a89e43d022c039")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=1024,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.SLOAD + Op.PUSH20[0xd395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8]
        + Op.PUSH6[0xfffffffffff] + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(balance=7000, nonce=0)
    pre[callee_2] = Account(
        balance=1024,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH20[0xe8f28ee50521b0388cf0a623b1a89e43d022c039]
        + Op.PUSH6[0xfffffffffff] + Op.STATICCALL + Op.PUSH1[0x20] + Op.MSTORE
        + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=tx_data,
        gas_limit=17592186099592,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
