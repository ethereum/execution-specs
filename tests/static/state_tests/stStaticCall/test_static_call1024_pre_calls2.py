"""
Ported from:
tests/static/state_tests/stStaticCall/static_Call1024PreCalls2Filler.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xeeb613e2a52609ee927be8a5b80ff190f6b71a37
    push2 0xffff
    staticcall
    push1 0x02
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xeeb613e2a52609ee927be8a5b80ff190f6b71a37
    push2 0xffff
    staticcall
    push1 0x03
    sstore
    push1 0x01
    push1 0x00
    ... (14 more instructions)

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

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xeeb613e2a52609ee927be8a5b80ff190f6b71a37
    push2 0xffff
    staticcall
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xeeb613e2a52609ee927be8a5b80ff190f6b71a37
    push2 0xffff
    staticcall
    pop
    push1 0x01
    push1 0x00
    mload
    add
    ... (10 more instructions)

callee_2 code:
    push1 0x01
    push1 0x00
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
    ["tests/static/state_tests/stStaticCall/static_Call1024PreCalls2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000002455231c1be66d57981908f4ac3633dee2e242e0",
        "000000000000000000000000daf588778cbccf0d5636643dbc67b42246b52f4a",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call1024_pre_calls2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x3f13d7fc49b91cdc388f79f861c0f1a0e708dfbf")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x2455231c1be66d57981908f4ac3633dee2e242e0")
    callee_1 = Address("0xdaf588778cbccf0d5636643dbc67b42246b52f4a")
    callee_2 = Address("0xeeb613e2a52609ee927be8a5b80ff190f6b71a37")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[callee] = Account(
        balance=2024,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xeeb613e2a52609ee927be8a5b80ff190f6b71a37] + Op.PUSH2[0xffff]
        + Op.STATICCALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xeeb613e2a52609ee927be8a5b80ff190f6b71a37] + Op.PUSH2[0xffff]
        + Op.STATICCALL + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.SLOAD + Op.ADD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2455231c1be66d57981908f4ac3633dee2e242e0]
        + Op.PUSH6[0xfffffffffff] + Op.DELEGATECALL + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=2024,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xeeb613e2a52609ee927be8a5b80ff190f6b71a37] + Op.PUSH2[0xffff]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xeeb613e2a52609ee927be8a5b80ff190f6b71a37]
        + Op.PUSH2[0xffff] + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdaf588778cbccf0d5636643dbc67b42246b52f4a]
        + Op.PUSH6[0xfffffffffff] + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=7000,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.STOP,
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xcc381c83857b17ca629268ed418e2915a0287b84efe9cf2204c020302e83cda0"
        ),
        to=contract,
        data=tx_data,
        gas_limit=9214364837600034817,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
