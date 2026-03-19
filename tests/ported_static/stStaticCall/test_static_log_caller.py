"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_log_CallerFiller.json
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
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_log_CallerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(4, 0, 0, id="case4"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_log_caller(
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
        gas_limit=1000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.LOG4(
                offset=0x0,
                size=0x20,
                topic_1=0x0,
                topic_2=0x0,
                topic_3=0x0,
                topic_4=Op.CALLER,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x586cfaa42db8b743452a87549943ac07a09de5cc"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.LOG3(
                offset=0x0,
                size=0x20,
                topic_1=0x0,
                topic_2=0x0,
                topic_3=Op.CALLER,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6c5da6457f756a77c392c72fe884f7f650428aef"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.LOG1(offset=0x0, size=0x20, topic_1=Op.CALLER)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x842936958d62030200fbcef4371460d8a9400d05"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.LOG2(offset=0x0, size=0x20, topic_1=0x0, topic_2=Op.CALLER)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x861cccbd560d81a33aac05190e986540663c6bba"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.LOG0(offset=0x0, size=0x20)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc725abae869e29a5448dca5b51a58f0c960d4069"),  # noqa: E501
    )
    # Source: LLL
    # { [[ 0 ]] (STATICCALL 50000 (CALLDATALOAD 0) 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
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
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd8c1fcdb2990f08e5fe821bf5af85f34201ba79a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60ff6000533360006000600060206000a400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("60ff600053336000600060206000a300")
                ),
                callee_2: Account(
                    code=bytes.fromhex("60ff6000533360206000a100")
                ),
                callee_3: Account(
                    code=bytes.fromhex("60ff60005333600060206000a200")
                ),
                callee_4: Account(
                    code=bytes.fromhex("60ff60005360206000a000")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060003561c350fa60005500"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60ff6000533360006000600060206000a400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("60ff600053336000600060206000a300")
                ),
                callee_2: Account(
                    code=bytes.fromhex("60ff6000533360206000a100")
                ),
                callee_3: Account(
                    code=bytes.fromhex("60ff60005333600060206000a200")
                ),
                callee_4: Account(
                    code=bytes.fromhex("60ff60005360206000a000")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060003561c350fa60005500"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60ff6000533360006000600060206000a400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("60ff600053336000600060206000a300")
                ),
                callee_2: Account(
                    code=bytes.fromhex("60ff6000533360206000a100")
                ),
                callee_3: Account(
                    code=bytes.fromhex("60ff60005333600060206000a200")
                ),
                callee_4: Account(
                    code=bytes.fromhex("60ff60005360206000a000")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060003561c350fa60005500"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60ff6000533360006000600060206000a400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("60ff600053336000600060206000a300")
                ),
                callee_2: Account(
                    code=bytes.fromhex("60ff6000533360206000a100")
                ),
                callee_3: Account(
                    code=bytes.fromhex("60ff60005333600060206000a200")
                ),
                callee_4: Account(
                    code=bytes.fromhex("60ff60005360206000a000")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060003561c350fa60005500"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60ff6000533360006000600060206000a400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("60ff600053336000600060206000a300")
                ),
                callee_2: Account(
                    code=bytes.fromhex("60ff6000533360206000a100")
                ),
                callee_3: Account(
                    code=bytes.fromhex("60ff60005333600060206000a200")
                ),
                callee_4: Account(
                    code=bytes.fromhex("60ff60005360206000a000")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060003561c350fa60005500"
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
