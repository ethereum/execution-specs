"""
Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodesFiller.json

callee code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0xe4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    stop

callee_1 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x2b8b4845acb3ef63f61f109b960754cf76dfbdfd
    push3 0x0186a0
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value",
    [
        ("000000000000000000000000b4b91c40f3e3a6e5576b0413572b88d535cee7b0", 50000, 0),
        ("000000000000000000000000b4b91c40f3e3a6e5576b0413572b88d535cee7b0", 50000, 100),
        ("000000000000000000000000b4b91c40f3e3a6e5576b0413572b88d535cee7b0", 335000, 0),
        ("000000000000000000000000b4b91c40f3e3a6e5576b0413572b88d535cee7b0", 335000, 100),
        ("000000000000000000000000e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0", 50000, 0),
        ("000000000000000000000000e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0", 50000, 100),
        ("000000000000000000000000e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0", 335000, 0),
        ("000000000000000000000000e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0", 335000, 100),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c")
    callee = Address("0x2b8b4845acb3ef63f61f109b960754cf76dfbdfd")
    callee_1 = Address("0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0")
    callee_2 = Address("0xe4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0xe4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.STATICCALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2b8b4845acb3ef63f61f109b960754cf76dfbdfd] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
