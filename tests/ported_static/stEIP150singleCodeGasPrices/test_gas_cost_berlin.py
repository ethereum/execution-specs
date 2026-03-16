"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostBerlinFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostBerlinFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000",
        "960003",
        "970003",
        "980003",
        "990003",
        "9a0003",
        "9b0003",
        "9c0003",
        "9d0003",
        "9e0003",
        "9f0003",
        "0b0005",
        "100003",
        "110003",
        "120003",
        "130003",
        "140003",
        "150003",
        "160003",
        "170003",
        "180003",
        "010003",
        "190003",
        "1a0003",
        "300002",
        "310a28",
        "320002",
        "330002",
        "340002",
        "350003",
        "360002",
        "380002",
        "020005",
        "3a0002",
        "3b0a28",
        "400014",
        "410002",
        "420002",
        "430002",
        "440002",
        "450002",
        "500002",
        "540834",
        "030003",
        "555654",
        "580002",
        "590002",
        "5a0002",
        "5b0001",
        "ff1db0",
        "600003",
        "610003",
        "620003",
        "630003",
        "040005",
        "640003",
        "650003",
        "660003",
        "670003",
        "680003",
        "690003",
        "6a0003",
        "6b0003",
        "6c0003",
        "6d0003",
        "050005",
        "6e0003",
        "6f0003",
        "700003",
        "710003",
        "720003",
        "730003",
        "740003",
        "750003",
        "760003",
        "770003",
        "060005",
        "780003",
        "790003",
        "7a0003",
        "7b0003",
        "7c0003",
        "7d0003",
        "7e0003",
        "7f0003",
        "800003",
        "810003",
        "070005",
        "820003",
        "830003",
        "840003",
        "850003",
        "860003",
        "870003",
        "880003",
        "890003",
        "8a0003",
        "8b0003",
        "080008",
        "8c0003",
        "8d0003",
        "8e0003",
        "8f0003",
        "900003",
        "910003",
        "920003",
        "930003",
        "940003",
        "950003",
        "090008",
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
        "case24",
        "case25",
        "case26",
        "case27",
        "case28",
        "case29",
        "case30",
        "case31",
        "case32",
        "case33",
        "case34",
        "case35",
        "case36",
        "case37",
        "case38",
        "case39",
        "case40",
        "case41",
        "case42",
        "case43",
        "case44",
        "case45",
        "case46",
        "case47",
        "case48",
        "case49",
        "case50",
        "case51",
        "case52",
        "case53",
        "case54",
        "case55",
        "case56",
        "case57",
        "case58",
        "case59",
        "case60",
        "case61",
        "case62",
        "case63",
        "case64",
        "case65",
        "case66",
        "case67",
        "case68",
        "case69",
        "case70",
        "case71",
        "case72",
        "case73",
        "case74",
        "case75",
        "case76",
        "case77",
        "case78",
        "case79",
        "case80",
        "case81",
        "case82",
        "case83",
        "case84",
        "case85",
        "case86",
        "case87",
        "case88",
        "case89",
        "case90",
        "case91",
        "case92",
        "case93",
        "case94",
        "case95",
        "case96",
        "case97",
        "case98",
        "case99",
        "case100",
        "case101",
        "case102",
        "case103",
        "case104",
        "case105",
        "case106",
        "case107",
        "case108",
        "case109",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_berlin(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x200,
                value=Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xF8)),
            )
            + Op.MSTORE(
                offset=0x340,
                value=Op.AND(
                    Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xE8)),
                    0xFFFF,
                ),
            )
            + Op.MSTORE(offset=0x260, value=0x11)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x76, condition=Op.ISZERO(Op.MLOAD(offset=0x260)))
            + Op.MSTORE(
                offset=0x260, value=Op.SUB(Op.MLOAD(offset=0x260), 0x1)
            )
            + Op.MSTORE8(
                offset=Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
                value=0x61,
            )
            + Op.MSTORE8(
                offset=Op.ADD(
                    Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
                    0x1,
                ),
                value=0xDA,
            )
            + Op.MSTORE8(
                offset=Op.ADD(
                    Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
                    0x2,
                ),
                value=0x7A,
            )
            + Op.MSTORE(
                offset=0x220, value=Op.ADD(Op.MLOAD(offset=0x220), 0x3)
            )
            + Op.JUMP(pc=0x24)
            + Op.JUMPDEST
            + Op.MSTORE8(
                offset=Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
                value=Op.MLOAD(offset=0x200),
            )
            + Op.MSTORE8(
                offset=Op.ADD(
                    Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
                    0x1,
                ),
                value=0x0,
            )
            + Op.MSTORE(
                offset=0x220, value=Op.ADD(Op.MLOAD(offset=0x220), 0x2)
            )
            + Op.PUSH1[0x1B]
            + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xFA], size=Op.DUP1)
            + Op.PUSH2[0x240]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x280,
                value=Op.CREATE(
                    value=0x0, offset=0x0, size=Op.MUL(0x100, 0x2)
                ),
            )
            + Op.MSTORE(offset=0x300, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0x10000,
                    address=Op.MLOAD(offset=0x280),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x320, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(
                        Op.SUB(Op.MLOAD(offset=0x300), Op.MLOAD(offset=0x320)),
                        0xB9,
                    ),
                    Op.MLOAD(offset=0x340),
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x340))
            + Op.STOP
            + Op.INVALID
            + Op.CODECOPY(
                dest_offset=Op.ADD(0x0, 0x100),
                offset=Op.ADD(0x0, 0x100),
                size=0x100,
            )
            + Op.RETURN(offset=Op.ADD(0x0, 0x100), size=0x100)
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x2f170b2347023bb6bf3eec84b53259b96e0268c3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = {
        Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"): Account(
            storage={0: 0, 1: 0},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
