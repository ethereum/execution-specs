"""
Test_static_callcallcodecall_010_2.

Ported from:
state_tests/stStaticCall/static_callcallcodecall_010_2Filler.json
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
    "0000000000000000000000006b21d14ffae42852fc3a6f98da6275e551c07008",
    "000000000000000000000000d450d1d19aefb5a30dc4a483db88e86c215c67a0",
]
TX_GAS = [3000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcodecall_010_2Filler.json"],
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
def test_static_callcallcodecall_010_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcodecall_010_2."""
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
    # {  [[ 0 ]] (STATICCALL 350000 (CALLDATALOAD 0) 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x55730,
                address=Op.CALLDATALOAD(offset=0x0),
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
        address=Address("0x04feba02513bfa1cf1456a0f32838b186775d8d4"),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 300000 <contract:0x1000000000000000000000000000000000000002> 2 0 64 0 64 ) }  # noqa: E501
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x493E0,
            address=0xEF859513AE36C397C43170A2980741575916167B,
            value=0x2,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6b21d14ffae42852fc3a6f98da6275e551c07008"),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 300000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x493E0,
            address=0xEF859513AE36C397C43170A2980741575916167B,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd450d1d19aefb5a30dc4a483db88e86c215c67a0"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }  # noqa: E501
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x3D090,
            address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xef859513ae36c397c43170a2980741575916167b"),  # noqa: E501
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
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
