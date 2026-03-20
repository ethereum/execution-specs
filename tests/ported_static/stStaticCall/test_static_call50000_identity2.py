"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Call50000_identity2Filler.json
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
    "000000000000000000000000cfb4c99d22928822feffa77a1a6de64042e48dd3",
    "000000000000000000000000b02bd8691a1a4f5fd4432b5b17c68dde3013fc35",
]

TX_GAS = [882500000]

TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_Call50000_identity2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call50000_identity2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=8925000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x2A)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x30,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.STATICCALL(
                    gas=0x61C,
                    address=0x4,
                    args_offset=0x0,
                    args_size=0xC350,
                    ret_offset=0x1,
                    ret_size=0xC350,
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x20, value=Op.MLOAD(offset=0x80))
            + Op.MSTORE(offset=0x40, value=Op.MLOAD(offset=0x1))
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xb02bd8691a1a4f5fd4432b5b17c68dde3013fc35"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x2A)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x30,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x61C,
                    address=0x4,
                    args_offset=0x0,
                    args_size=0xC350,
                    ret_offset=0x1,
                    ret_size=0xC350,
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x1))
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xcfb4c99d22928822feffa77a1a6de64042e48dd3"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "602a6001525b61c350608051101560305761c350600161c3506000600461061cfa6000526001608051016080526005565b60805160205260015160405200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_1: Account(
                    storage={1: 50000, 2: 42},
                    code=bytes.fromhex(
                        "602a6001525b61c350608051101560305761c350600161c3506000600461061cfa6000556001608051016080526005565b60805160015560015160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "602a6001525b61c350608051101560305761c350600161c3506000600461061cfa6000526001608051016080526005565b60805160205260015160405200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "602a6001525b61c350608051101560305761c350600161c3506000600461061cfa6000556001608051016080526005565b60805160015560015160025500"  # noqa: E501
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
