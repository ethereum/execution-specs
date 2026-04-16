"""
Test_static_callcallcodecallcode_011_2.

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_011_2Filler.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcodecallcode_011_2Filler.json"],
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
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcodecallcode_011_2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (CALLCODE 300000 (CALLDATALOAD 0) 0 0 64 0 64 ) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x493E0,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x21A2D07156B4F874F3B25DFD175145C9CCEC1E19),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x2A142C79A9B097C111CE945214226126B75E332C),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x55730,
                address=0x21A2D07156B4F874F3B25DFD175145C9CCEC1E19,
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
        address=Address(0x023AE6338FBE9709A6449BFB0821F5AA83987B26),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x3D090,
            address=0x2A142C79A9B097C111CE945214226126B75E332C,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x709EB538153D5F98F0B8482C462070C26DB1CBAE),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000003> 1 0 64 0 64 ) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x3D090,
            address=0x2A142C79A9B097C111CE945214226126B75E332C,
            value=0x1,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x3CEA889FD03A922CC673D25E5DB4E72743AA4878),  # noqa: E501
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
    tx_gas = [3000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
