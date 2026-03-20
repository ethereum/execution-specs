"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodesFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000b4b91c40f3e3a6e5576b0413572b88d535cee7b0",
    "000000000000000000000000e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0",
]

TX_GAS = [50000, 335000]

TX_VALUE = [0, 100]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 0, 1, id="case1"),
        pytest.param(0, 1, 0, id="case2"),
        pytest.param(0, 1, 1, id="case3"),
        pytest.param(1, 0, 0, id="case4"),
        pytest.param(1, 0, 1, id="case5"),
        pytest.param(1, 1, 0, id="case6"),
        pytest.param(1, 1, 1, id="case7"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_check_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0xE4B8BAA7DA1A97BFF89D7DB0AE345DD30CD8C1D0,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2b8b4845acb3ef63f61f109b960754cf76dfbdfd"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x50F628D871A69F2DB31E98D7FBF8AE6F1FC0D55C,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x186A0,
                address=0x2B8B4845ACB3EF63F61F109B960754CF76DFBDFD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe4b8baa7da1a97bff89d7db0ae345dd30cd8c1d0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e4b8baa7da1a97bff89d7db0ae345dd30cd8c1d014604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b337350f628d871a69f2db31e98d7fbf8ae6f1fc0d55c14604b5760026001556051565b60016001525b3073b4b91c40f3e3a6e5576b0413572b88d535cee7b0146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000732b8b4845acb3ef63f61f109b960754cf76dfbdfd620186a0fa00"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
