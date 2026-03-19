"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStackTests/shallowStackFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "600101600055",
    "600102600055",
    "600103600055",
    "600104600055",
    "600105600055",
    "600106600055",
    "600107600055",
    "6002600108600055",
    "6002600109600055",
    "60010a600055",
    "60010b600055",
    "600110600055",
    "600111600055",
    "600112600055",
    "600113600055",
    "600114600055",
    "15600055",
    "600116600055",
    "600117600055",
    "600118600055",
    "19600055",
    "60011a600055",
    "600120600055",
    "31600055",
    "35600055",
    "6001600237600055",
    "6001600239600055",
    "3b600055",
    "6001600260033c600055",
    "40600055",
    "50600055",
    "51600055",
    "600152600055",
    "600153600055",
    "54600055",
    "600155600055",
    "56600055",
    "600157600055",
    "80600055",
    "600181600055",
    "6002600182600055",
    "60036002600183600055",
    "600460036002600184600055",
    "6005600460036002600185600055",
    "60066005600460036002600186600055",
    "600760066005600460036002600187600055",
    "6008600760066005600460036002600188600055",
    "60096008600760066005600460036002600189600055",
    "60106009600860076006600560046003600260018a600055",
    "601160106009600860076006600560046003600260018b600055",
    "6012601160106009600860076006600560046003600260018c600055",
    "60136012601160106009600860076006600560046003600260018d600055",
    "601460136012601160106009600860076006600560046003600260018e600055",
    "60136012601160106009600860076006600560046003600260018f600055",
    "600190600055",
    "6002600191600055",
    "60036002600192600055",
    "600460036002600193600055",
    "6005600460036002600194600055",
    "60066005600460036002600195600055",
    "600760066005600460036002600196600055",
    "6008600760066005600460036002600197600055",
    "60096008600760066005600460036002600198600055",
    "601060096008600760066005600460036002600199600055",
    "601160106009600860076006600560046003600260019a600055",
    "6012601160106009600860076006600560046003600260019b600055",
    "60136012601160106009600860076006600560046003600260019c600055",
    "601460136012601160106009600860076006600560046003600260019d600055",
    "6015601460136012601160106009600860076006600560046003600260019e600055",
    "6012601160106009600860076006600560046003600260019f600055",
    "6001a0600055",
    "60026001a1600055",
    "600360026001a2600055",
    "6004600360026001a3600055",
    "60056004600360026001a4600055",
    "60026001f0600055",
    "600660056004600360026001f1600055",
    "600660056004600360026001f2600055",
    "6001f3600055",
    "60056004600360026001f4600055",
    "ff600055",
]

TX_GAS = [300000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStackTests/shallowStackFiller.json"],
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
        pytest.param(16, 0, 0, id="case7"),
        pytest.param(17, 0, 0, id="case8"),
        pytest.param(18, 0, 0, id="case9"),
        pytest.param(19, 0, 0, id="case10"),
        pytest.param(1, 0, 0, id="case11"),
        pytest.param(20, 0, 0, id="case12"),
        pytest.param(21, 0, 0, id="case13"),
        pytest.param(22, 0, 0, id="case14"),
        pytest.param(23, 0, 0, id="case15"),
        pytest.param(24, 0, 0, id="case16"),
        pytest.param(25, 0, 0, id="case17"),
        pytest.param(26, 0, 0, id="case18"),
        pytest.param(27, 0, 0, id="case19"),
        pytest.param(28, 0, 0, id="case20"),
        pytest.param(29, 0, 0, id="case21"),
        pytest.param(2, 0, 0, id="case22"),
        pytest.param(30, 0, 0, id="case23"),
        pytest.param(31, 0, 0, id="case24"),
        pytest.param(32, 0, 0, id="case25"),
        pytest.param(33, 0, 0, id="case26"),
        pytest.param(34, 0, 0, id="case27"),
        pytest.param(35, 0, 0, id="case28"),
        pytest.param(36, 0, 0, id="case29"),
        pytest.param(37, 0, 0, id="case30"),
        pytest.param(38, 0, 0, id="case31"),
        pytest.param(39, 0, 0, id="case32"),
        pytest.param(3, 0, 0, id="case33"),
        pytest.param(40, 0, 0, id="case34"),
        pytest.param(41, 0, 0, id="case35"),
        pytest.param(42, 0, 0, id="case36"),
        pytest.param(43, 0, 0, id="case37"),
        pytest.param(44, 0, 0, id="case38"),
        pytest.param(45, 0, 0, id="case39"),
        pytest.param(46, 0, 0, id="case40"),
        pytest.param(47, 0, 0, id="case41"),
        pytest.param(48, 0, 0, id="case42"),
        pytest.param(49, 0, 0, id="case43"),
        pytest.param(4, 0, 0, id="case44"),
        pytest.param(50, 0, 0, id="case45"),
        pytest.param(51, 0, 0, id="case46"),
        pytest.param(52, 0, 0, id="case47"),
        pytest.param(53, 0, 0, id="case48"),
        pytest.param(54, 0, 0, id="case49"),
        pytest.param(55, 0, 0, id="case50"),
        pytest.param(56, 0, 0, id="case51"),
        pytest.param(57, 0, 0, id="case52"),
        pytest.param(58, 0, 0, id="case53"),
        pytest.param(59, 0, 0, id="case54"),
        pytest.param(5, 0, 0, id="case55"),
        pytest.param(60, 0, 0, id="case56"),
        pytest.param(61, 0, 0, id="case57"),
        pytest.param(62, 0, 0, id="case58"),
        pytest.param(63, 0, 0, id="case59"),
        pytest.param(64, 0, 0, id="case60"),
        pytest.param(65, 0, 0, id="case61"),
        pytest.param(66, 0, 0, id="case62"),
        pytest.param(67, 0, 0, id="case63"),
        pytest.param(68, 0, 0, id="case64"),
        pytest.param(69, 0, 0, id="case65"),
        pytest.param(6, 0, 0, id="case66"),
        pytest.param(70, 0, 0, id="case67"),
        pytest.param(71, 0, 0, id="case68"),
        pytest.param(72, 0, 0, id="case69"),
        pytest.param(73, 0, 0, id="case70"),
        pytest.param(74, 0, 0, id="case71"),
        pytest.param(75, 0, 0, id="case72"),
        pytest.param(76, 0, 0, id="case73"),
        pytest.param(77, 0, 0, id="case74"),
        pytest.param(78, 0, 0, id="case75"),
        pytest.param(79, 0, 0, id="case76"),
        pytest.param(7, 0, 0, id="case77"),
        pytest.param(80, 0, 0, id="case78"),
        pytest.param(8, 0, 0, id="case79"),
        pytest.param(9, 0, 0, id="case80"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_shallow_stack(
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
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    pre[sender] = Account(balance=0x271000000000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 35, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 36, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 37, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 38, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 39, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 40, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 41, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 42, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 43, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 44, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 45, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 46, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 47, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 48, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 49, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 50, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 51, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 52, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 53, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 54, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 55, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 56, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 57, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 58, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 59, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 60, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 61, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 62, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 63, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 64, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 65, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 66, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 67, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 68, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 69, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 70, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 71, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 72, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 73, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 74, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 75, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 76, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 77, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 78, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 79, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 80, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {},
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
