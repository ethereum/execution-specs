"""
account already has storage X. create -> in init code change that account's...

Ported from:
tests/static/state_tests/stSStoreTest
sstore_changeFromExternalCallInInitCodeFiller.json
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
    "6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
    "6000602580601360003960006000f5500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
    "6000602580601860003960006000f55060006000fd0000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
    "6000602580603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
    "6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
    "6000602580601360003960006000f5500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
    "6000602580601860003960006000f55060006000fd0000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
    "6000602580603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
    "600060006000600073bea0000000000000000000000000000000000000620186a0f400",
    "6000602380601360003960006000f5500000fe600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
    "6000602380601860003960006000f55060006000fd0000fe600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
    "6000602380603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
    "600060006000600073bea0000000000000000000000000000000000000620186a0fa00",
    "6000602380601360003960006000f5500000fe600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
    "6000602380601860003960006000f55060006000fd0000fe600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
    "6000602380603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
]

TX_GAS = [200000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSStoreTest/sstore_changeFromExternalCallInInitCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(10, 0, 0, id="case1"),
        pytest.param(11, 0, 0, id="case2"),
        pytest.param(12, 0, 0, id="case3"),
        pytest.param(13, 0, 0, id="case4"),
        pytest.param(14, 0, 0, id="case5"),
        pytest.param(15, 0, 0, id="case6"),
        pytest.param(1, 0, 0, id="case7"),
        pytest.param(2, 0, 0, id="case8"),
        pytest.param(3, 0, 0, id="case9"),
        pytest.param(4, 0, 0, id="case10"),
        pytest.param(5, 0, 0, id="case11"),
        pytest.param(6, 0, 0, id="case12"),
        pytest.param(7, 0, 0, id="case13"),
        pytest.param(8, 0, 0, id="case14"),
        pytest.param(9, 0, 0, id="case15"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_change_from_external_call_in_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Account already has storage X. create -> in init code change that..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: LLL
    # { (SSTORE 1 0) (SSTORE 1 1) (SSTORE 0 1) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.SSTORE(key=0x0, value=0x1)
            + Op.STOP
        ),
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xbea0000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] 1 [[1]] 0 [[2]] 1 [[2]] 0 [[3]] 1 [[3]] 0 [[4]] 1 [[4]] 0 [[5]] 1 [[5]] 0 [[6]] 1 [[6]] 0 [[7]] 1 [[7]] 0 [[8]] 1 [[8]] 0 [[9]] 1 [[9]] 0 [[10]] 1 [[10]] 0 [[11]] 1 [[11]] 0 [[12]] 1 [[12]] 0 [[13]] 1 [[13]] 0 [[14]] 1 [[14]] 0 [[15]] 1 [[15]] 0 [[16]] 1 [[16]] 0  [[1]] 1 }  # noqa: E501
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x1)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x1)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x1)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x1)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.SSTORE(key=0x6, value=0x1)
            + Op.SSTORE(key=0x6, value=0x0)
            + Op.SSTORE(key=0x7, value=0x1)
            + Op.SSTORE(key=0x7, value=0x0)
            + Op.SSTORE(key=0x8, value=0x1)
            + Op.SSTORE(key=0x8, value=0x0)
            + Op.SSTORE(key=0x9, value=0x1)
            + Op.SSTORE(key=0x9, value=0x0)
            + Op.SSTORE(key=0xA, value=0x1)
            + Op.SSTORE(key=0xA, value=0x0)
            + Op.SSTORE(key=0xB, value=0x1)
            + Op.SSTORE(key=0xB, value=0x0)
            + Op.SSTORE(key=0xC, value=0x1)
            + Op.SSTORE(key=0xC, value=0x0)
            + Op.SSTORE(key=0xD, value=0x1)
            + Op.SSTORE(key=0xD, value=0x0)
            + Op.SSTORE(key=0xE, value=0x1)
            + Op.SSTORE(key=0xE, value=0x0)
            + Op.SSTORE(key=0xF, value=0x1)
            + Op.SSTORE(key=0xF, value=0x0)
            + Op.SSTORE(key=0x10, value=0x1)
            + Op.SSTORE(key=0x10, value=0x0)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xdea0000000000000000000000000000000000000"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                Address("0xc07f1349a887643be65b34e234e1b3161f62dc30"): Account(
                    storage={0: 1, 1: 1}
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 1, 1: 1}
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x0f446e1bd7a5da68b5e3a305c7030e3aa8efc293"): Account(
                    storage={0: 1, 1: 1}
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x0f446e1bd7a5da68b5e3a305c7030e3aa8efc293"): Account(
                    storage={0: 1, 1: 1}
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 1, 1: 1}
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex("60006001556001600155600160005500"),
                ),
                Address("0xc07f1349a887643be65b34e234e1b3161f62dc30"): Account(
                    storage={0: 1, 1: 1}
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
