"""
Test_return50000_2.

Ported from:
state_tests/stQuadraticComplexityTest/Return50000_2Filler.json
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
    ["state_tests/stQuadraticComplexityTest/Return50000_2Filler.json"],
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
def test_return50000_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_return50000_2."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    # Source: lll
    # { [ 0 ] (CALLDATALOAD 49999) (RETURN @0 1) }
    addr_code = (
        Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0xC34F))
        + Op.RETURN(offset=Op.MLOAD(offset=0x0), size=0x1)
        + Op.STOP
    )
    addr = pre.deploy_contract(
        code=addr_code,
        balance=0xFFFFFFFFFFFFF,
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (CALL 1564 <contract:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 50000 0 0) ) [[ 1 ]] @i }  # noqa: E501
    target_code = (
        Op.JUMPDEST
        + Op.JUMPI(
            pc=0x3F, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x61C,
                address=Op.PUSH20[addr],
                value=0x0,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=target_code,
        balance=0xFFFFFFFFFFFFF,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(
                    storage={},
                    code=addr_code,
                    nonce=1,
                ),
                target: Account(
                    storage={0: 1, 1: 50000},
                    code=(target_code),
                    nonce=1,
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(
                    storage={},
                    code=addr_code,
                    nonce=1,
                ),
                target: Account(
                    storage={},
                    code=(target_code),
                    nonce=1,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16000000]
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
