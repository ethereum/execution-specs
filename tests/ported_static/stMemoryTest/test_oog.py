"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stMemoryTest/oogFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
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


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/oogFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="success",
        ),
        pytest.param(
            1,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            2,
            0,
            0,
            id="success",
        ),
        pytest.param(
            3,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            4,
            0,
            0,
            id="success",
        ),
        pytest.param(
            5,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            6,
            0,
            0,
            id="success",
        ),
        pytest.param(
            7,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            8,
            0,
            0,
            id="success",
        ),
        pytest.param(
            9,
            0,
            0,
            id="success",
        ),
        pytest.param(
            10,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            11,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            12,
            0,
            0,
            id="success",
        ),
        pytest.param(
            13,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            14,
            0,
            0,
            id="success",
        ),
        pytest.param(
            15,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            16,
            0,
            0,
            id="success",
        ),
        pytest.param(
            17,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            18,
            0,
            0,
            id="success",
        ),
        pytest.param(
            19,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            20,
            0,
            0,
            id="success",
        ),
        pytest.param(
            21,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            22,
            0,
            0,
            id="success",
        ),
        pytest.param(
            23,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            24,
            0,
            0,
            id="success",
        ),
        pytest.param(
            25,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            26,
            0,
            0,
            id="success",
        ),
        pytest.param(
            27,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            28,
            0,
            0,
            id="success",
        ),
        pytest.param(
            29,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            30,
            0,
            0,
            id="success",
        ),
        pytest.param(
            31,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            32,
            0,
            0,
            id="success",
        ),
        pytest.param(
            33,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            34,
            0,
            0,
            id="success",
        ),
        pytest.param(
            35,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            36,
            0,
            0,
            id="success",
        ),
        pytest.param(
            37,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            38,
            0,
            0,
            id="success",
        ),
        pytest.param(
            39,
            0,
            0,
            id="failure",
        ),
        pytest.param(
            40,
            0,
            0,
            id="success",
        ),
        pytest.param(
            41,
            0,
            0,
            id="failure",
        ),
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
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000010020)
    contract_1 = Address(0x0000000000000000000000000000000000010037)
    contract_2 = Address(0x0000000000000000000000000000000000010039)
    contract_3 = Address(0x000000000000000000000000000000000001003C)
    contract_4 = Address(0x000000000000000000000000000000000001003E)
    contract_5 = Address(0x000000000000000000000000000000000001113E)
    contract_6 = Address(0x0000000000000000000000000000000000010051)
    contract_7 = Address(0x0000000000000000000000000000000000010052)
    contract_8 = Address(0x0000000000000000000000000000000000010053)
    contract_9 = Address(0x00000000000000000000000000000000000100A0)
    contract_10 = Address(0x00000000000000000000000000000000000100A1)
    contract_11 = Address(0x00000000000000000000000000000000000100A2)
    contract_12 = Address(0x00000000000000000000000000000000000100A3)
    contract_13 = Address(0x00000000000000000000000000000000000100A4)
    contract_14 = Address(0x00000000000000000000000000000000000100F0)
    contract_15 = Address(0x00000000000000000000000000000000000100F5)
    contract_16 = Address(0x00000000000000000000000000000000000100F3)
    contract_17 = Address(0x00000000000000000000000000000000000100F1)
    contract_18 = Address(0x00000000000000000000000000000000000100F2)
    contract_19 = Address(0x00000000000000000000000000000000000100F4)
    contract_20 = Address(0x00000000000000000000000000000000000100FA)
    contract_21 = Address(0x00000000000000000000000000000000000111F1)
    contract_22 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    # Source: yul
    # berlin
    # {
    #     // Instead of keccak256, which seems to be optimized into
    #     // not happening
    #     pop(verbatim_2i_1o(hex"20", 0, 0x1000))
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SHA3(offset=0x0, size=0x1000) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000010020),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    calldatacopy(0,0,0x1000)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x1000)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000010037),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    codecopy(0,0,0x1000)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=Op.DUP1, offset=0x0, size=0x1000)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000010039),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    extcodecopy(address(),0,0,0x1000)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.EXTCODECOPY(
            address=Op.ADDRESS, dest_offset=Op.DUP1, offset=0x0, size=0x1000
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000001003C),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // Make sure there is return data to be copied
    #    pop(call(gas(), 0x1113e, 0, 0, 0x20, 0, 0x20))
    #
    #    returndatacopy(0x1000,0,0x10)
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1113E,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x1000, offset=0x0, size=0x10)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000001003E),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    mstore(0, 0x0102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F20)  # noqa: E501
    #    return(0,0x20)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F20,  # noqa: E501
        )
        + Op.RETURN(offset=0x0, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000001113E),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #     pop(verbatim_1i_1o(hex"51", 0x1000))
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MLOAD(offset=0x1000) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000010051),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #     mstore(0x1000, 0xFF)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000010052),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #     mstore8(0x1000, 0xFF)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x1000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000010053),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    log0(0x10000, 0x20)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG0(offset=0x10000, size=0x20) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100A0),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    log1(0x10000, 0x20, 0x1)
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG1(offset=0x10000, size=0x20, topic_1=0x1) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100A1),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    log2(0x10000, 0x20, 0x1, 0x2)
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG2(offset=0x10000, size=0x20, topic_1=0x1, topic_2=0x2)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100A2),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    log3(0x10000, 0x20, 0x1, 0x2, 0x3)
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG3(
            offset=0x10000, size=0x20, topic_1=0x1, topic_2=0x2, topic_3=0x3
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100A3),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    log4(0x10000, 0x20, 0x1, 0x2, 0x3, 0x4)
    # }
    contract_13 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG4(
            offset=0x10000,
            size=0x20,
            topic_1=0x1,
            topic_2=0x2,
            topic_3=0x3,
            topic_4=0x4,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100A4),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    pop(create(0, 0x10000, 0x20))
    # }
    contract_14 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE(value=0x0, offset=0x10000, size=0x20) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100F0),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    pop(create2(0, 0x10000, 0x20, 0x5a17))
    # }
    contract_15 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE2(value=0x0, offset=0x10000, size=0x20, salt=0x5A17)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100F5),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    return(0x10000, 0x20)
    # }
    contract_16 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x10000, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100F3),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    pop(call(gas(), 0x111f1, 0, 0x10000, 0, 0, 0))
    # }
    contract_17 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=0x111F1,
            value=Op.DUP2,
            args_offset=0x10000,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100F1),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    pop(callcode(gas(), 0x111f1, 0, 0x10000, 0, 0, 0))
    # }
    contract_18 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=0x111F1,
            value=Op.DUP2,
            args_offset=0x10000,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100F2),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    pop(delegatecall(gas(), 0x111f1, 0x10000, 0, 0, 0))
    # }
    contract_19 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=0x111F1,
            args_offset=0x10000,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100F4),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    pop(staticcall(gas(), 0x111f1, 0x10000, 0, 0, 0))
    # }
    contract_20 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=Op.GAS,
            address=0x111F1,
            args_offset=0x10000,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000100FA),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    stop()
    # }
    contract_21 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000111F1),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let op     := calldataload(0x04)
    #    let gasAmt := calldataload(0x24)
    #
    #    // Call the function that actually goes OOG (or not)
    #    sstore(0, call(gasAmt, add(0x10000,op), 0, 0, 0, 0, 0))
    # }
    contract_22 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    expect_entries_: list[dict] = [
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
            "result": {contract_22: Account(storage={0: 1})},
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
            "result": {contract_22: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("1a8451e6") + Hash(0x20) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x4BA),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x32A),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x32A),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x2BC),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0xC02),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x7D0),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0xC01),
        Bytes("1a8451e6") + Hash(0x51) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x51) + Hash(0x190),
        Bytes("1a8451e6") + Hash(0x52) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x52) + Hash(0x190),
        Bytes("1a8451e6") + Hash(0x53) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0x53) + Hash(0x190),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x39D0),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x39D0),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x39D0),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x39D0),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x39D0),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x7D00),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x7D00),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x36B0),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x2BC),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x2BC),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x2BC),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0xFFFF),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x2BC),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=contract_22,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
