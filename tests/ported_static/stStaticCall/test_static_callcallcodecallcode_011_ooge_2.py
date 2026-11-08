"""
Test_static_callcallcodecallcode_011_ooge_2.

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
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
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json"  # noqa: E501
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
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
def test_static_callcallcodecallcode_011_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcodecallcode_011_ooge_2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (MSTORE 3 1) (CALLCODE 100000 (CALLDATALOAD 0) 0 0 64 0 64 ) (MSTORE 3 1)}  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x186A0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x249F0,
                address=addr,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  (MSTORE 3 11) (CALLCODE 20020 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) (MSTORE 13 1)}  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0xB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x4E34,
                address=addr_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0xD, value=0x1)
        + Op.STOP,
    )
    # Source: lll
    # {  (MSTORE 3 11) (CALLCODE 20020 <contract:0x1000000000000000000000000000000000000003> 1 0 64 0 64 ) (MSTORE 13 1)}  # noqa: E501
    addr_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0xB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x4E34,
                address=addr_4,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0xD, value=0x1)
        + Op.STOP,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
