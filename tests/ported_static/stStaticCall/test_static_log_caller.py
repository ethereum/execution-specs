"""
Test_static_log_caller.

Ported from:
state_tests/stStaticCall/static_log_CallerFiller.json
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
    "000000000000000000000000c725abae869e29a5448dca5b51a58f0c960d4069",
    "000000000000000000000000842936958d62030200fbcef4371460d8a9400d05",
    "000000000000000000000000861cccbd560d81a33aac05190e986540663c6bba",
    "0000000000000000000000006c5da6457f756a77c392c72fe884f7f650428aef",
    "000000000000000000000000586cfaa42db8b743452a87549943ac07a09de5cc",
]
TX_GAS = [210000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_log_CallerFiller.json"],
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_log_caller(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_log_caller."""
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
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL 50000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xC350,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd8c1fcdb2990f08e5fe821bf5af85f34201ba79a"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG0 0 32 ) }
    addr_0xa000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG0(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc725abae869e29a5448dca5b51a58f0c960d4069"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG1 0 32 (CALLER) ) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG1(offset=0x0, size=0x20, topic_1=Op.CALLER)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x842936958d62030200fbcef4371460d8a9400d05"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG2 0 32 0 (CALLER) ) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG2(offset=0x0, size=0x20, topic_1=0x0, topic_2=Op.CALLER)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x861cccbd560d81a33aac05190e986540663c6bba"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG3 0 32 0 0 (CALLER) ) }
    addr_0x3000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG3(
            offset=0x0, size=0x20, topic_1=0x0, topic_2=0x0, topic_3=Op.CALLER
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6c5da6457f756a77c392c72fe884f7f650428aef"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG4 0 32 0 0 0 (CALLER) )}
    addr_0x4000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG4(
            offset=0x0,
            size=0x20,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=Op.CALLER,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x586cfaa42db8b743452a87549943ac07a09de5cc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
