"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest
RevertPrecompiledTouchExactOOG_ParisFiller.json
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
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
    "00000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
]

TX_GAS = [22500, 120000, 69000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertPrecompiledTouchExactOOG_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 1, 0, id="case1"),
        pytest.param(0, 2, 0, id="case2"),
        pytest.param(1, 0, 0, id="case3"),
        pytest.param(1, 1, 0, id="case4"),
        pytest.param(1, 2, 0, id="case5"),
        pytest.param(10, 0, 0, id="case6"),
        pytest.param(10, 1, 0, id="case7"),
        pytest.param(10, 2, 0, id="case8"),
        pytest.param(11, 0, 0, id="case9"),
        pytest.param(11, 1, 0, id="case10"),
        pytest.param(11, 2, 0, id="case11"),
        pytest.param(12, 0, 0, id="case12"),
        pytest.param(12, 1, 0, id="case13"),
        pytest.param(12, 2, 0, id="case14"),
        pytest.param(13, 0, 0, id="case15"),
        pytest.param(13, 1, 0, id="case16"),
        pytest.param(13, 2, 0, id="case17"),
        pytest.param(14, 0, 0, id="case18"),
        pytest.param(14, 1, 0, id="case19"),
        pytest.param(14, 2, 0, id="case20"),
        pytest.param(15, 0, 0, id="case21"),
        pytest.param(15, 1, 0, id="case22"),
        pytest.param(15, 2, 0, id="case23"),
        pytest.param(16, 0, 0, id="case24"),
        pytest.param(16, 1, 0, id="case25"),
        pytest.param(16, 2, 0, id="case26"),
        pytest.param(17, 0, 0, id="case27"),
        pytest.param(17, 1, 0, id="case28"),
        pytest.param(17, 2, 0, id="case29"),
        pytest.param(18, 0, 0, id="case30"),
        pytest.param(18, 1, 0, id="case31"),
        pytest.param(18, 2, 0, id="case32"),
        pytest.param(19, 0, 0, id="case33"),
        pytest.param(19, 1, 0, id="case34"),
        pytest.param(19, 2, 0, id="case35"),
        pytest.param(2, 0, 0, id="case36"),
        pytest.param(2, 1, 0, id="case37"),
        pytest.param(2, 2, 0, id="case38"),
        pytest.param(20, 0, 0, id="case39"),
        pytest.param(20, 1, 0, id="case40"),
        pytest.param(20, 2, 0, id="case41"),
        pytest.param(21, 0, 0, id="case42"),
        pytest.param(21, 1, 0, id="case43"),
        pytest.param(21, 2, 0, id="case44"),
        pytest.param(22, 0, 0, id="case45"),
        pytest.param(22, 1, 0, id="case46"),
        pytest.param(22, 2, 0, id="case47"),
        pytest.param(23, 0, 0, id="case48"),
        pytest.param(23, 1, 0, id="case49"),
        pytest.param(23, 2, 0, id="case50"),
        pytest.param(24, 0, 0, id="case51"),
        pytest.param(24, 1, 0, id="case52"),
        pytest.param(24, 2, 0, id="case53"),
        pytest.param(25, 0, 0, id="case54"),
        pytest.param(25, 1, 0, id="case55"),
        pytest.param(25, 2, 0, id="case56"),
        pytest.param(26, 0, 0, id="case57"),
        pytest.param(26, 1, 0, id="case58"),
        pytest.param(26, 2, 0, id="case59"),
        pytest.param(27, 0, 0, id="case60"),
        pytest.param(27, 1, 0, id="case61"),
        pytest.param(27, 2, 0, id="case62"),
        pytest.param(28, 0, 0, id="case63"),
        pytest.param(28, 1, 0, id="case64"),
        pytest.param(28, 2, 0, id="case65"),
        pytest.param(29, 0, 0, id="case66"),
        pytest.param(29, 1, 0, id="case67"),
        pytest.param(29, 2, 0, id="case68"),
        pytest.param(3, 0, 0, id="case69"),
        pytest.param(3, 1, 0, id="case70"),
        pytest.param(3, 2, 0, id="case71"),
        pytest.param(30, 0, 0, id="case72"),
        pytest.param(30, 1, 0, id="case73"),
        pytest.param(30, 2, 0, id="case74"),
        pytest.param(31, 0, 0, id="case75"),
        pytest.param(31, 1, 0, id="case76"),
        pytest.param(31, 2, 0, id="case77"),
        pytest.param(4, 0, 0, id="case78"),
        pytest.param(4, 1, 0, id="case79"),
        pytest.param(4, 2, 0, id="case80"),
        pytest.param(5, 0, 0, id="case81"),
        pytest.param(5, 1, 0, id="case82"),
        pytest.param(5, 2, 0, id="case83"),
        pytest.param(6, 0, 0, id="case84"),
        pytest.param(6, 1, 0, id="case85"),
        pytest.param(6, 2, 0, id="case86"),
        pytest.param(7, 0, 0, id="case87"),
        pytest.param(7, 1, 0, id="case88"),
        pytest.param(7, 2, 0, id="case89"),
        pytest.param(8, 0, 0, id="case90"),
        pytest.param(8, 1, 0, id="case91"),
        pytest.param(8, 2, 0, id="case92"),
        pytest.param(9, 0, 0, id="case93"),
        pytest.param(9, 1, 0, id="case94"),
        pytest.param(9, 2, 0, id="case95"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_exact_oog_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x0FF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )
    callee = Address("0x1688023d9ae9e25ea02a2447a77b9cc9d22ce57b")
    callee_2 = Address("0x6eb9afcb5d985b12549b7ac2e65c093f7113a0c7")
    callee_4 = Address("0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba")
    callee_5 = Address("0x9e6c35deced6e05eb21d3465b5bbbb57b9cd57d6")
    callee_7 = Address("0xad3df2901b7c6642e397c35e0e9f3dea5d098238")
    callee_8 = Address("0xbe44b82021b08cfecc33a2e57ff5adcb7fe3b049")
    callee_10 = Address("0xd085ab47bc36d1238fc092679b21b10792746640")
    callee_11 = Address("0xf07a794e0f8aab4242b86368503d3c1de15481f8")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[callee] = Account(balance=1, nonce=0)
    callee_1 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=Op.CALLDATASIZE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x33506407e929a3834ea7bfa65f86b41c7b7e57b9"),  # noqa: E501
    )
    # Source: LLL
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 (CALLDATALOAD 32) 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=Op.CALLDATALOAD(offset=0x20),
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x6c7fac59c79986689878e37545df629f68278098"),  # noqa: E501
    )
    pre[callee_2] = Account(balance=1, nonce=0)
    callee_3 = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.CALLDATASIZE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x81f666fdc784482530048e74cee651ea98a0733d"),  # noqa: E501
    )
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    callee_6 = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATASIZE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa2f144d2206204d88e039b31bb7db14a28a06fed"),  # noqa: E501
    )
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    pre[callee_8] = Account(balance=1, nonce=0)
    callee_9 = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=Op.GAS,
                address=Op.CALLDATASIZE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc02fff115e5eee4ff4420eba1cb7cb8772e0598e"),  # noqa: E501
    )
    pre[callee_10] = Account(balance=1, nonce=0)
    pre[callee_11] = Account(balance=1, nonce=0)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    code=bytes.fromhex("60006000600060006000365af200")
                ),
                contract: Account(
                    code=bytes.fromhex("60006000602035600060006000355af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex("6000600060006000365af400")
                ),
                callee_6: Account(
                    code=bytes.fromhex("60006000600060006000365af100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6000600060006000365afa00")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
