"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmTests/sha3Filler.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000006",
    "693c61390000000000000000000000000000000000000000000000000000000000000007",
    "693c61390000000000000000000000000000000000000000000000000000000000000008",
    "693c61390000000000000000000000000000000000000000000000000000000000000009",
    "693c6139000000000000000000000000000000000000000000000000000000000000000a",
    "693c6139000000000000000000000000000000000000000000000000000000000000000b",
    "693c6139000000000000000000000000000000000000000000000000000000000000000c",
    "693c6139000000000000000000000000000000000000000000000000000000000000000d",
    "693c61390000000000000000000000000000000000000000000000000000000000000010",
    "693c6139000000000000000000000000000000000000000000000000000000000000000e",
    "693c6139000000000000000000000000000000000000000000000000000000000000000f",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/VMTests/vmTests/sha3Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(8, 0, 0, id="case0"),
        pytest.param(3, 0, 0, id="case1"),
        pytest.param(16, 0, 0, id="case2"),
        pytest.param(11, 0, 0, id="case3"),
        pytest.param(12, 0, 0, id="case4"),
        pytest.param(13, 0, 0, id="case5"),
        pytest.param(14, 0, 0, id="case6"),
        pytest.param(15, 0, 0, id="case7"),
        pytest.param(9, 0, 0, id="case8"),
        pytest.param(10, 0, 0, id="case9"),
        pytest.param(1, 0, 0, id="case10"),
        pytest.param(4, 0, 0, id="case11"),
        pytest.param(5, 0, 0, id="case12"),
        pytest.param(7, 0, 0, id="case13"),
        pytest.param(6, 0, 0, id="case14"),
        pytest.param(0, 0, 0, id="case15"),
        pytest.param(2, 0, 0, id="case16"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sha3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
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
        gas_limit=100000000,
    )

    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x0, size=0x0)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x4, size=0x5)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0xA, size=0xA)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x3E8, size=0xFFFFF))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0xFFFFFFFFF, size=0x64))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x2710, size=0xFFFFFFFFF))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SHA3(
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SHA3(
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    size=0x2,
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     [[0]] (sha3 0x1000000 2)
    # }
    callee_8 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x1000000, size=0x2))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 960 1)
    # }
    callee_9 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x3C0, size=0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 992 1)
    # }
    callee_10 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x3E0, size=0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 1024 1)
    # }
    callee_11 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x400, size=0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100b"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 1984 1)
    # }
    callee_12 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x7C0, size=0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100c"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 2016 1)
    # }
    callee_13 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x7E0, size=0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100d"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 2048 1)
    # }
    callee_14 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x800, size=0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100e"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[ 0 ]] (sha3 1024 0)
    # }
    callee_15 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x400, size=0x0)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100f"),  # noqa: E501
    )
    callee_16 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x7E0, size=0x20))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001010"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     (call (- 0 1) (+ 0x1000 $4) 0
    #        0x0F 0x10   ; arg offset and length to get the 0x1234...f0 value
    #        0x20 0x40)  ; return offset and length
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.SUB(0x0, 0x1),
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                value=0x0,
                args_offset=0xF,
                args_size=0x10,
                ret_offset=0x20,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    storage={
                        0: 0xBE6F1B42B34644F918560A07F959D23E532DEA5338E4B9F63DB0CAEB608018FA,  # noqa: E501
                    },
                    code=bytes.fromhex("620fffff6103e82060005500"),
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(
                    storage={
                        0: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                    code=bytes.fromhex("60006104002060005500"),
                ),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                    code=bytes.fromhex("60016104002060005500"),
                ),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                    code=bytes.fromhex("60016107c02060005500"),
                ),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                    code=bytes.fromhex("60016107e02060005500"),
                ),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(
                    storage={
                        0: 0x290DECD9548B62A8D60345A988386FC84BA6BC95484008F6362F93160EF3E563,  # noqa: E501
                    },
                    code=bytes.fromhex("60206107e02060005500"),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                    code=bytes.fromhex("60016108002060005500"),
                ),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                    code=bytes.fromhex("60016103c02060005500"),
                ),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(
                    storage={
                        0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
                    },
                    code=bytes.fromhex("60016103e02060005500"),
                ),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(
                    storage={
                        0: 0xC41589E7559804EA4A2080DAD19D876A024CCB05117835447D72CE08C1D020EC,  # noqa: E501
                    },
                    code=bytes.fromhex("600560042060005500"),
                ),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={
                        0: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                    code=bytes.fromhex("600060002060005500"),
                ),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(code=bytes.fromhex("600a600a2060005500")),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600060002060005500")),
                callee_1: Account(code=bytes.fromhex("600560042060005500")),
                callee_2: Account(
                    storage={
                        0: 0x6BD2DD6BD408CBEE33429358BF24FDC64612FBF8B1B4DB604518F40FFD34B607,  # noqa: E501
                    },
                    code=bytes.fromhex("600a600a2060005500"),
                ),
                callee_3: Account(
                    code=bytes.fromhex("620fffff6103e82060005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6064640fffffffff2060005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("640fffffffff6127102060005500")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60027fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2060005500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("600263010000002060005500")
                ),
                callee_9: Account(code=bytes.fromhex("60016103c02060005500")),
                callee_10: Account(code=bytes.fromhex("60016103e02060005500")),
                callee_11: Account(code=bytes.fromhex("60016104002060005500")),
                callee_12: Account(code=bytes.fromhex("60016107c02060005500")),
                callee_13: Account(code=bytes.fromhex("60016107e02060005500")),
                callee_14: Account(code=bytes.fromhex("60016108002060005500")),
                callee_15: Account(code=bytes.fromhex("60006104002060005500")),
                callee_16: Account(code=bytes.fromhex("60206107e02060005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "604060206010600f6000600435611000016001600003f100"
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
