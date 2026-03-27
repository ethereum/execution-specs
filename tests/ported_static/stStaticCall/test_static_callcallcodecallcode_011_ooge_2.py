"""
Test_static_callcallcodecallcode_011_ooge_2.

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json
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
    "000000000000000000000000bb2e6e56806816e94a356b0f0c8e53f98e44d6ad",
    "000000000000000000000000f43b4e8b779078758104039080947f8f74e663d3",
]
TX_GAS = [172000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
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
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcodecallcode_011_ooge_2."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x249F0,
                address=0x11A4A9DAD43E6ED44E108EAF7FB160F9835068F4,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6e143211e9d36eaeebe65f6ed69d6c28500040d6"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (CALLCODE 100000 (CALLDATALOAD 0) 0 0 64 0 64 ) (MSTORE 3 1)}  # noqa: E501
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address("0x11a4a9dad43e6ed44e108eaf7fb160f9835068f4"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 11) (CALLCODE 20020 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) (MSTORE 13 1)}  # noqa: E501
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0xB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x4E34,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0xD, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0xbb2e6e56806816e94a356b0f0c8e53f98e44d6ad"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 11) (CALLCODE 20020 <contract:0x1000000000000000000000000000000000000003> 1 0 64 0 64 ) (MSTORE 13 1)}  # noqa: E501
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0xB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x4E34,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0xD, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0xf43b4e8b779078758104039080947f8f74e663d3"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

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

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
