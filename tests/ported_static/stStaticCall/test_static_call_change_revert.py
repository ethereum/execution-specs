"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callChangeRevertFiller.json
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
    "000000000000000000000000e6f1fdaa1c99007971c641e10af3a8fac0b641c8",
    "000000000000000000000000ea22ec955ac71d8e4380541212bd20818d704567",
    "0000000000000000000000002c004389edaae817e664b6d660f46735756b56d3",
]

TX_GAS = [1000000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callChangeRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_change_revert(
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
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
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
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x47C4ED3D93429CB8304737E2327B522E8928C9F3,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0x47C4ED3D93429CB8304737E2327B522E8928C9F3,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x47C4ED3D93429CB8304737E2327B522E8928C9F3,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x2c004389edaae817e664b6d660f46735756b56d3"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.SSTORE(key=0x1, value=Op.SLOAD(key=0x1))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x47c4ed3d93429cb8304737e2327b522e8928c9f3"),  # noqa: E501
    )
    # Source: LLL
    # {  (CALL 350000 (CALLDATALOAD 0) 0 0 0 0 0)  }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x55730,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x492bb18adce7da2bed3592742fb4e3df9086fb4c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc031fc0aa7b61a5d7d962afee8838dec6948abb7"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xe6f1fdaa1c99007971c641e10af3a8fac0b641c8"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x8F,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x73)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xea22ec955ac71d8e4380541212bd20818d704567"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060017347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0f160005560006000600060007347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0fa600155600060006000600060017347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0f160025500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600160015260015460015500")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060003562055730f100"
                    )
                ),
                callee_2: Account(code=bytes.fromhex("600160015200")),
                callee_3: Account(
                    storage={0: 1, 1: 1, 2: 1},
                    code=bytes.fromhex(
                        "6000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f1600055600060006000600073c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0fa6001556000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f160025500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f1600055600060006000600073c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0fa6001556000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f16002555b61c3506080511015608f5760013b506001608051016080526073565b00"  # noqa: E501
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
                        "600060006000600060017347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0f160005560006000600060007347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0fa600155600060006000600060017347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0f160025500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex("600160015260015460015500")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060003562055730f100"
                    )
                ),
                callee_2: Account(code=bytes.fromhex("600160015200")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f1600055600060006000600073c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0fa6001556000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f160025500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f1600055600060006000600073c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0fa6001556000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f16002555b61c3506080511015608f5760013b506001608051016080526073565b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 1, 2: 1},
                    code=bytes.fromhex(
                        "600060006000600060017347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0f160005560006000600060007347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0fa600155600060006000600060017347c4ed3d93429cb8304737e2327b522e8928c9f3620186a0f160025500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex("600160015260015460015500")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060003562055730f100"
                    )
                ),
                callee_2: Account(code=bytes.fromhex("600160015200")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f1600055600060006000600073c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0fa6001556000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f160025500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f1600055600060006000600073c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0fa6001556000600060006000600173c031fc0aa7b61a5d7d962afee8838dec6948abb7620186a0f16002555b61c3506080511015608f5760013b506001608051016080526073565b00"  # noqa: E501
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
