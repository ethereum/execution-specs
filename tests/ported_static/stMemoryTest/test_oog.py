"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stMemoryTest/oogFiller.yml
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
    "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004ba",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000032a",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000032a",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000003c00000000000000000000000000000000000000000000000000000000000002bc",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000c02",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000007d0",  # noqa: E501
    "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000c01",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000051000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000510000000000000000000000000000000000000000000000000000000000000190",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000052000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000520000000000000000000000000000000000000000000000000000000000000190",  # noqa: E501
    "1a8451e60000000000000000000000000000000000000000000000000000000000000053000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000530000000000000000000000000000000000000000000000000000000000000190",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000039d0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a100000000000000000000000000000000000000000000000000000000000039d0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a200000000000000000000000000000000000000000000000000000000000039d0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a300000000000000000000000000000000000000000000000000000000000039d0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000a400000000000000000000000000000000000000000000000000000000000039d0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000007d00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000007d00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f300000000000000000000000000000000000000000000000000000000000036b0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f100000000000000000000000000000000000000000000000000000000000002bc",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f200000000000000000000000000000000000000000000000000000000000002bc",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f400000000000000000000000000000000000000000000000000000000000002bc",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000ffff",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000002bc",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stMemoryTest/oogFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(19, 0, 0, id="case0"),
        pytest.param(21, 0, 0, id="case1"),
        pytest.param(23, 0, 0, id="case2"),
        pytest.param(25, 0, 0, id="case3"),
        pytest.param(27, 0, 0, id="case4"),
        pytest.param(29, 0, 0, id="case5"),
        pytest.param(31, 0, 0, id="case6"),
        pytest.param(33, 0, 0, id="case7"),
        pytest.param(35, 0, 0, id="case8"),
        pytest.param(37, 0, 0, id="case9"),
        pytest.param(39, 0, 0, id="case10"),
        pytest.param(41, 0, 0, id="case11"),
        pytest.param(3, 0, 0, id="case12"),
        pytest.param(5, 0, 0, id="case13"),
        pytest.param(7, 0, 0, id="case14"),
        pytest.param(10, 0, 0, id="case15"),
        pytest.param(11, 0, 0, id="case16"),
        pytest.param(13, 0, 0, id="case17"),
        pytest.param(15, 0, 0, id="case18"),
        pytest.param(17, 0, 0, id="case19"),
        pytest.param(1, 0, 0, id="case20"),
        pytest.param(18, 0, 0, id="case21"),
        pytest.param(20, 0, 0, id="case22"),
        pytest.param(22, 0, 0, id="case23"),
        pytest.param(24, 0, 0, id="case24"),
        pytest.param(26, 0, 0, id="case25"),
        pytest.param(28, 0, 0, id="case26"),
        pytest.param(30, 0, 0, id="case27"),
        pytest.param(32, 0, 0, id="case28"),
        pytest.param(34, 0, 0, id="case29"),
        pytest.param(36, 0, 0, id="case30"),
        pytest.param(38, 0, 0, id="case31"),
        pytest.param(40, 0, 0, id="case32"),
        pytest.param(2, 0, 0, id="case33"),
        pytest.param(4, 0, 0, id="case34"),
        pytest.param(6, 0, 0, id="case35"),
        pytest.param(8, 0, 0, id="case36"),
        pytest.param(9, 0, 0, id="case37"),
        pytest.param(12, 0, 0, id="case38"),
        pytest.param(14, 0, 0, id="case39"),
        pytest.param(16, 0, 0, id="case40"),
        pytest.param(0, 0, 0, id="case41"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_oog(
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

    pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0x1000) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000010020"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x1000)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000010037"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    codecopy(0,0,0x1000)
    # }
    pre.deploy_contract(
        code=(
            Op.CODECOPY(dest_offset=Op.DUP1, offset=0x0, size=0x1000) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000010039"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    extcodecopy(address(),0,0,0x1000)
    # }
    pre.deploy_contract(
        code=(
            Op.EXTCODECOPY(
                address=Op.ADDRESS,
                dest_offset=Op.DUP1,
                offset=0x0,
                size=0x1000,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000001003c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // Make sure there is return data to be copied
    #    pop(call(gas(), 0x1113e, 0, 0, 0x20, 0, 0x20))
    #
    #    returndatacopy(0x1000,0,0x10)
    # }
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x1113E,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.RETURNDATACOPY(dest_offset=0x1000, offset=0x0, size=0x10)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000001003e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.MLOAD(offset=0x1000) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000010051"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.MSTORE(offset=0x1000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000010052"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.MSTORE8(offset=0x1000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000010053"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    log0(0x10000, 0x20)
    # }
    pre.deploy_contract(
        code=Op.LOG0(offset=0x10000, size=0x20) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100a0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    log1(0x10000, 0x20, 0x1)
    # }
    pre.deploy_contract(
        code=Op.LOG1(offset=0x10000, size=0x20, topic_1=0x1) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100a1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    log2(0x10000, 0x20, 0x1, 0x2)
    # }
    pre.deploy_contract(
        code=(
            Op.LOG2(offset=0x10000, size=0x20, topic_1=0x1, topic_2=0x2)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100a2"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    log3(0x10000, 0x20, 0x1, 0x2, 0x3)
    # }
    pre.deploy_contract(
        code=(
            Op.LOG3(
                offset=0x10000,
                size=0x20,
                topic_1=0x1,
                topic_2=0x2,
                topic_3=0x3,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100a3"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    log4(0x10000, 0x20, 0x1, 0x2, 0x3, 0x4)
    # }
    pre.deploy_contract(
        code=(
            Op.LOG4(
                offset=0x10000,
                size=0x20,
                topic_1=0x1,
                topic_2=0x2,
                topic_3=0x3,
                topic_4=0x4,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100a4"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(create(0, 0x10000, 0x20))
    # }
    pre.deploy_contract(
        code=Op.CREATE(value=0x0, offset=0x10000, size=0x20) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100f0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(call(gas(), 0x111f1, 0, 0x10000, 0, 0, 0))
    # }
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=0x111F1,
                value=Op.DUP2,
                args_offset=0x10000,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100f1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(callcode(gas(), 0x111f1, 0, 0x10000, 0, 0, 0))
    # }
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0x111F1,
                value=Op.DUP2,
                args_offset=0x10000,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100f2"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    return(0x10000, 0x20)
    # }
    pre.deploy_contract(
        code=Op.RETURN(offset=0x10000, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100f3"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(delegatecall(gas(), 0x111f1, 0x10000, 0, 0, 0))
    # }
    pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0x111F1,
                args_offset=0x10000,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100f4"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(create2(0, 0x10000, 0x20, 0x5a17))
    # }
    pre.deploy_contract(
        code=(
            Op.CREATE2(value=0x0, offset=0x10000, size=0x20, salt=0x5A17)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100f5"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(staticcall(gas(), 0x111f1, 0x10000, 0, 0, 0))
    # }
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x111F1,
                args_offset=0x10000,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000100fa"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore(0, 0x0102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F20)  # noqa: E501
    #    return(0,0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F20,  # noqa: E501
            )
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000001113e"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    stop()
    # }
    pre.deploy_contract(
        code=bytes.fromhex("00"),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000111f1"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: Yul
    # {
    #    let op     := calldataload(0x04)
    #    let gasAmt := calldataload(0x24)
    #
    #    // Call the function that actually goes OOG (or not)
    #    sstore(0, call(gasAmt, add(0x10000,op), 0, 0, 0, 0, 0))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.CALLDATALOAD(offset=0x24),
                    address=Op.ADD(Op.CALLDATALOAD(offset=0x4), 0x10000),
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    2,
                    4,
                    6,
                    8,
                    9,
                    12,
                    14,
                    16,
                    18,
                    20,
                    22,
                    24,
                    26,
                    28,
                    30,
                    32,
                    34,
                    36,
                    38,
                    40,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 1})},
        },
        {
            "indexes": {
                "data": [
                    1,
                    3,
                    5,
                    7,
                    10,
                    11,
                    13,
                    15,
                    17,
                    19,
                    21,
                    23,
                    25,
                    27,
                    29,
                    31,
                    33,
                    35,
                    37,
                    39,
                    41,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

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
