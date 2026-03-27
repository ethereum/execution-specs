"""
Test_static_callcallcode_01_2.

Ported from:
state_tests/stStaticCall/static_callcallcode_01_2Filler.json
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
    "000000000000000000000000fbe34b488c83765de2f7fefc646710b8f1dcb303",
    "000000000000000000000000c766dcc7257dd2af2b6a354fc922d43d3ad9a390",
]
TX_GAS = [3000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcode_01_2Filler.json"],
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
def test_static_callcallcode_01_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcode_01_2."""
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
    # {  [[ 0 ]] (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xaab59f13d96113334fab5c68e4e62b61f6cbf647"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 32 0 64 ) }  # noqa: E501
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x55730,
            address=0xC42C1601B039F8BB80A155B5B6AFB4CFFEB430A,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xfbe34b488c83765de2f7fefc646710b8f1dcb303"),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000002> 2 0 32 0 64 ) }  # noqa: E501
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x3D090,
            address=0x8AD8D964B0888C5016605939DD13E1BDCF679F05,
            value=0x2,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0c42c1601b039f8bb80a155b5b6afb4cffeb430a"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 0x11223344) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x11223344) + Op.STOP,
        nonce=0,
        address=Address("0x8ad8d964b0888c5016605939dd13e1bdcf679f05"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 32 0 64 ) }  # noqa: E501
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x55730,
            address=0xF686A2E0E79C5FBB3407D5E53F3AB6B0AB21A51A,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc766dcc7257dd2af2b6a354fc922d43d3ad9a390"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) (CALLCODE 250000 <contract:0x2000000000000000000000000000000000000002> 0 0 32 0 64 ) }  # noqa: E501
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALLCODE(
            gas=0x3D090,
            address=0x2FCC143C5267B6C6CE4E1ABD936E84EEDFFD6A4E,
            value=0x0,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xf686a2e0e79c5fbb3407d5e53f3ab6b0ab21a51a"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 0x11223344) }
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x11223344) + Op.STOP,
        nonce=0,
        address=Address("0x2fcc143c5267b6c6ce4e1abd936e84eedffd6a4e"),  # noqa: E501
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
