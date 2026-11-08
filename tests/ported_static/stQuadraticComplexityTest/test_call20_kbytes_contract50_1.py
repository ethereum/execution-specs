"""
Test_call20_kbytes_contract50_1.

Ported from:
state_tests/stQuadraticComplexityTest/Call20KbytesContract50_1Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stQuadraticComplexityTest/Call20KbytesContract50_1Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_call20_kbytes_contract50_1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_call20_kbytes_contract50_1."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    # Source: raw
    # 0x60016001016001...01600055
    code = (
        Op.PUSH1[1] + ((Op.PUSH1[1] + Op.ADD) * 3727) + Op.PUSH1[0] + Op.SSTORE
    )
    addr = pre.deploy_contract(
        code=code,
        balance=0xFFFFFFFFFFFFF,
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50) [i](+ @i 1) [[ 0 ]] (CALL 88250000000 <contract:0xaaa50000fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) ) [[ 1 ]] @i }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x40, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0x32))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x148C1C2280,
                address=Op.PUSH20[addr],
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(code=code, storage={0: 3728}, nonce=1),
                target: Account(storage={0: 1, 1: 50}, nonce=1),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(code=code, storage={}, nonce=1),
                target: Account(storage={}, nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 12500000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
