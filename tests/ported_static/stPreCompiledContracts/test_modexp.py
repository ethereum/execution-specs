"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stPreCompiledContracts/modexpFiller.json
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
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002003fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000002003ffff800000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000002003ffff80",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000002003",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020038000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000080",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000101",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000304",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001020004",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001020300",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010304",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010204",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000203",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000202030006",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001020306",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002020300",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000202030000",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020203",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002023003",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020230",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000202",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001001001010010",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000064",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000010100000000000000000000000000000000000000000000000000000000000000020200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030006",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040000000000",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010035ee4e488f45e64d2f07becd54646357381d32f30b74c299a8c25d5202c04938ef6c4764a04f10fc908b78c4486886000f6d290251a79681a83b950c7e5c37351",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000005000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000cd935b43e42204fcbfb734a6e27735e8e90204fcc1fd2727bb040f9eecb",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000060846813a8d2d451387340fa0597c6545ae63",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000005000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d02534f82b1013f20d9c7d18d62cd95674d2e013f20d9c7d18d62cd95674d2f",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000000120785e45de3d6be050ba3c4d33ff0bb2d010ace3b1dfe9c49f4c7a8075102fa19a86c010ace3b1dfe9c49f4c7a8075102fa19a86d",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000ff2a1e5300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000010001",  # noqa: E501
]

TX_GAS = [100000000, 90000, 110000, 200000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stPreCompiledContracts/modexpFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 1, 0, id="case1"),
        pytest.param(0, 2, 0, id="case2"),
        pytest.param(0, 3, 0, id="case3"),
        pytest.param(1, 0, 0, id="case4"),
        pytest.param(1, 1, 0, id="case5"),
        pytest.param(1, 2, 0, id="case6"),
        pytest.param(1, 3, 0, id="case7"),
        pytest.param(10, 0, 0, id="case8"),
        pytest.param(10, 1, 0, id="case9"),
        pytest.param(10, 2, 0, id="case10"),
        pytest.param(10, 3, 0, id="case11"),
        pytest.param(11, 0, 0, id="case12"),
        pytest.param(11, 1, 0, id="case13"),
        pytest.param(11, 2, 0, id="case14"),
        pytest.param(11, 3, 0, id="case15"),
        pytest.param(12, 0, 0, id="case16"),
        pytest.param(12, 1, 0, id="case17"),
        pytest.param(12, 2, 0, id="case18"),
        pytest.param(12, 3, 0, id="case19"),
        pytest.param(13, 0, 0, id="case20"),
        pytest.param(13, 1, 0, id="case21"),
        pytest.param(13, 2, 0, id="case22"),
        pytest.param(13, 3, 0, id="case23"),
        pytest.param(14, 0, 0, id="case24"),
        pytest.param(14, 1, 0, id="case25"),
        pytest.param(14, 2, 0, id="case26"),
        pytest.param(14, 3, 0, id="case27"),
        pytest.param(15, 0, 0, id="case28"),
        pytest.param(15, 1, 0, id="case29"),
        pytest.param(15, 2, 0, id="case30"),
        pytest.param(15, 3, 0, id="case31"),
        pytest.param(16, 0, 0, id="case32"),
        pytest.param(16, 1, 0, id="case33"),
        pytest.param(16, 2, 0, id="case34"),
        pytest.param(16, 3, 0, id="case35"),
        pytest.param(17, 0, 0, id="case36"),
        pytest.param(17, 1, 0, id="case37"),
        pytest.param(17, 2, 0, id="case38"),
        pytest.param(17, 3, 0, id="case39"),
        pytest.param(18, 0, 0, id="case40"),
        pytest.param(18, 1, 0, id="case41"),
        pytest.param(18, 2, 0, id="case42"),
        pytest.param(18, 3, 0, id="case43"),
        pytest.param(19, 0, 0, id="case44"),
        pytest.param(19, 1, 0, id="case45"),
        pytest.param(19, 2, 0, id="case46"),
        pytest.param(19, 3, 0, id="case47"),
        pytest.param(2, 0, 0, id="case48"),
        pytest.param(2, 1, 0, id="case49"),
        pytest.param(2, 2, 0, id="case50"),
        pytest.param(2, 3, 0, id="case51"),
        pytest.param(20, 0, 0, id="case52"),
        pytest.param(20, 1, 0, id="case53"),
        pytest.param(20, 2, 0, id="case54"),
        pytest.param(20, 3, 0, id="case55"),
        pytest.param(21, 0, 0, id="case56"),
        pytest.param(21, 1, 0, id="case57"),
        pytest.param(21, 2, 0, id="case58"),
        pytest.param(21, 3, 0, id="case59"),
        pytest.param(22, 0, 0, id="case60"),
        pytest.param(22, 1, 0, id="case61"),
        pytest.param(22, 2, 0, id="case62"),
        pytest.param(22, 3, 0, id="case63"),
        pytest.param(23, 0, 0, id="case64"),
        pytest.param(23, 1, 0, id="case65"),
        pytest.param(23, 2, 0, id="case66"),
        pytest.param(23, 3, 0, id="case67"),
        pytest.param(24, 0, 0, id="case68"),
        pytest.param(24, 1, 0, id="case69"),
        pytest.param(24, 2, 0, id="case70"),
        pytest.param(24, 3, 0, id="case71"),
        pytest.param(25, 0, 0, id="case72"),
        pytest.param(25, 1, 0, id="case73"),
        pytest.param(25, 2, 0, id="case74"),
        pytest.param(25, 3, 0, id="case75"),
        pytest.param(26, 0, 0, id="case76"),
        pytest.param(26, 1, 0, id="case77"),
        pytest.param(26, 2, 0, id="case78"),
        pytest.param(26, 3, 0, id="case79"),
        pytest.param(27, 0, 0, id="case80"),
        pytest.param(27, 1, 0, id="case81"),
        pytest.param(27, 2, 0, id="case82"),
        pytest.param(27, 3, 0, id="case83"),
        pytest.param(28, 0, 0, id="case84"),
        pytest.param(28, 1, 0, id="case85"),
        pytest.param(28, 2, 0, id="case86"),
        pytest.param(28, 3, 0, id="case87"),
        pytest.param(29, 0, 0, id="case88"),
        pytest.param(29, 1, 0, id="case89"),
        pytest.param(29, 2, 0, id="case90"),
        pytest.param(29, 3, 0, id="case91"),
        pytest.param(3, 0, 0, id="case92"),
        pytest.param(3, 1, 0, id="case93"),
        pytest.param(3, 2, 0, id="case94"),
        pytest.param(3, 3, 0, id="case95"),
        pytest.param(30, 0, 0, id="case96"),
        pytest.param(30, 1, 0, id="case97"),
        pytest.param(30, 2, 0, id="case98"),
        pytest.param(30, 3, 0, id="case99"),
        pytest.param(31, 0, 0, id="case100"),
        pytest.param(31, 1, 0, id="case101"),
        pytest.param(31, 2, 0, id="case102"),
        pytest.param(31, 3, 0, id="case103"),
        pytest.param(32, 0, 0, id="case104"),
        pytest.param(32, 1, 0, id="case105"),
        pytest.param(32, 2, 0, id="case106"),
        pytest.param(32, 3, 0, id="case107"),
        pytest.param(33, 0, 0, id="case108"),
        pytest.param(33, 1, 0, id="case109"),
        pytest.param(33, 2, 0, id="case110"),
        pytest.param(33, 3, 0, id="case111"),
        pytest.param(34, 0, 0, id="case112"),
        pytest.param(34, 1, 0, id="case113"),
        pytest.param(34, 2, 0, id="case114"),
        pytest.param(34, 3, 0, id="case115"),
        pytest.param(35, 0, 0, id="case116"),
        pytest.param(35, 1, 0, id="case117"),
        pytest.param(35, 2, 0, id="case118"),
        pytest.param(35, 3, 0, id="case119"),
        pytest.param(36, 0, 0, id="case120"),
        pytest.param(36, 1, 0, id="case121"),
        pytest.param(36, 2, 0, id="case122"),
        pytest.param(36, 3, 0, id="case123"),
        pytest.param(37, 0, 0, id="case124"),
        pytest.param(37, 1, 0, id="case125"),
        pytest.param(37, 2, 0, id="case126"),
        pytest.param(37, 3, 0, id="case127"),
        pytest.param(4, 0, 0, id="case128"),
        pytest.param(4, 1, 0, id="case129"),
        pytest.param(4, 2, 0, id="case130"),
        pytest.param(4, 3, 0, id="case131"),
        pytest.param(5, 0, 0, id="case132"),
        pytest.param(5, 1, 0, id="case133"),
        pytest.param(5, 2, 0, id="case134"),
        pytest.param(5, 3, 0, id="case135"),
        pytest.param(6, 0, 0, id="case136"),
        pytest.param(6, 1, 0, id="case137"),
        pytest.param(6, 2, 0, id="case138"),
        pytest.param(6, 3, 0, id="case139"),
        pytest.param(7, 0, 0, id="case140"),
        pytest.param(7, 1, 0, id="case141"),
        pytest.param(7, 2, 0, id="case142"),
        pytest.param(7, 3, 0, id="case143"),
        pytest.param(8, 0, 0, id="case144"),
        pytest.param(8, 1, 0, id="case145"),
        pytest.param(8, 2, 0, id="case146"),
        pytest.param(8, 3, 0, id="case147"),
        pytest.param(9, 0, 0, id="case148"),
        pytest.param(9, 1, 0, id="case149"),
        pytest.param(9, 2, 0, id="case150"),
        pytest.param(9, 3, 0, id="case151"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_modexp(
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
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: LLL
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) [[1]] (CALLCODE (GAS) 5 0 0 (CALLDATASIZE) 1000 32) [[2]](MLOAD 1000) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
            + Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=Op.GAS,
                    address=0x5,
                    value=0x0,
                    args_offset=0x0,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=0x3E8,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3E8))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2d06ad61919840e4e00f80782dedce12ada1e859"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 0, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 0, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x200000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x200000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x200000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x200000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 22, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 22, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 22, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 23, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 23, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 23, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 24, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 24, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 24, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 25, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 25, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 25, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 26, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 26, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 26, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 27, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 27, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 27, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x2000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 28, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 28, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 28, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 29, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 29, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 29, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 30, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 30, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 30, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x100000000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 31, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x100000000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 31, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x100000000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 31, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x100000000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 32, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 32, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 32, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 33, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 33, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 33, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x10000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 34, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 34, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 34, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x100000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 35, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x10000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 35, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x10000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 35, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x10000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 35, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 0x10000000000000000000000000000},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 36, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 36, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 36, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 36, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 37, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 37, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 37, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 37, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 1,
                        2: 0x3B01B01AC41F2D6E917C6D6A221CE793802469026D9AB7578FA2E79E4DA6AAAB,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 3, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "36600060003760206103e8366000600060055af26001556103e85160025500"  # noqa: E501
                    ),
                )
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
