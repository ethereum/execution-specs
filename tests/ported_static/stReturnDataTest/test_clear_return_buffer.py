"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stReturnDataTest/clearReturnBufferFiller.yml
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
    Storage,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def _storage_with_any(base: dict, any_keys: list) -> Storage:
    """Create Storage with set_expect_any for specified keys."""
    s = Storage(base)
    for k in any_keys:
        s.set_expect_any(k)
    return s


@pytest.mark.ported_from(
    ["state_tests/stReturnDataTest/clearReturnBufferFiller.yml"],
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
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
        pytest.param(
            16,
            0,
            0,
            id="d16",
        ),
        pytest.param(
            17,
            0,
            0,
            id="d17",
        ),
        pytest.param(
            18,
            0,
            0,
            id="d18",
        ),
        pytest.param(
            19,
            0,
            0,
            id="d19",
        ),
        pytest.param(
            20,
            0,
            0,
            id="d20",
        ),
        pytest.param(
            21,
            0,
            0,
            id="d21",
        ),
        pytest.param(
            22,
            0,
            0,
            id="d22",
        ),
        pytest.param(
            23,
            0,
            0,
            id="d23",
        ),
        pytest.param(
            24,
            0,
            0,
            id="d24",
        ),
        pytest.param(
            25,
            0,
            0,
            id="d25",
        ),
        pytest.param(
            26,
            0,
            0,
            id="d26",
        ),
        pytest.param(
            27,
            0,
            0,
            id="d27",
        ),
        pytest.param(
            28,
            0,
            0,
            id="d28",
        ),
        pytest.param(
            29,
            0,
            0,
            id="d29",
        ),
        pytest.param(
            30,
            0,
            0,
            id="d30",
        ),
        pytest.param(
            31,
            0,
            0,
            id="d31",
        ),
        pytest.param(
            32,
            0,
            0,
            id="d32",
        ),
        pytest.param(
            33,
            0,
            0,
            id="d33",
        ),
        pytest.param(
            34,
            0,
            0,
            id="d34",
        ),
        pytest.param(
            35,
            0,
            0,
            id="d35",
        ),
        pytest.param(
            36,
            0,
            0,
            id="d36",
        ),
        pytest.param(
            37,
            0,
            0,
            id="d37",
        ),
        pytest.param(
            38,
            0,
            0,
            id="d38",
        ),
        pytest.param(
            39,
            0,
            0,
            id="d39",
        ),
        pytest.param(
            40,
            0,
            0,
            id="d40",
        ),
        pytest.param(
            41,
            0,
            0,
            id="d41",
        ),
        pytest.param(
            42,
            0,
            0,
            id="d42",
        ),
        pytest.param(
            43,
            0,
            0,
            id="d43",
        ),
        pytest.param(
            44,
            0,
            0,
            id="d44",
        ),
        pytest.param(
            45,
            0,
            0,
            id="d45",
        ),
        pytest.param(
            46,
            0,
            0,
            id="d46",
        ),
        pytest.param(
            47,
            0,
            0,
            id="d47",
        ),
        pytest.param(
            48,
            0,
            0,
            id="d48",
        ),
        pytest.param(
            49,
            0,
            0,
            id="d49",
        ),
        pytest.param(
            50,
            0,
            0,
            id="d50",
        ),
        pytest.param(
            51,
            0,
            0,
            id="d51",
        ),
        pytest.param(
            52,
            0,
            0,
            id="d52",
        ),
        pytest.param(
            53,
            0,
            0,
            id="d53",
        ),
        pytest.param(
            54,
            0,
            0,
            id="d54",
        ),
        pytest.param(
            55,
            0,
            0,
            id="d55",
        ),
        pytest.param(
            56,
            0,
            0,
            id="d56",
        ),
        pytest.param(
            57,
            0,
            0,
            id="d57",
        ),
        pytest.param(
            58,
            0,
            0,
            id="d58",
        ),
        pytest.param(
            59,
            0,
            0,
            id="d59",
        ),
        pytest.param(
            60,
            0,
            0,
            id="d60",
        ),
        pytest.param(
            61,
            0,
            0,
            id="d61",
        ),
        pytest.param(
            62,
            0,
            0,
            id="d62",
        ),
        pytest.param(
            63,
            0,
            0,
            id="d63",
        ),
        pytest.param(
            64,
            0,
            0,
            id="d64",
        ),
        pytest.param(
            65,
            0,
            0,
            id="d65",
        ),
        pytest.param(
            66,
            0,
            0,
            id="d66",
        ),
        pytest.param(
            67,
            0,
            0,
            id="d67",
        ),
        pytest.param(
            68,
            0,
            0,
            id="d68",
        ),
        pytest.param(
            69,
            0,
            0,
            id="d69",
        ),
        pytest.param(
            70,
            0,
            0,
            id="d70",
        ),
        pytest.param(
            71,
            0,
            0,
            id="d71",
        ),
        pytest.param(
            72,
            0,
            0,
            id="d72",
        ),
        pytest.param(
            73,
            0,
            0,
            id="d73",
        ),
        pytest.param(
            74,
            0,
            0,
            id="d74",
        ),
        pytest.param(
            75,
            0,
            0,
            id="d75",
        ),
        pytest.param(
            76,
            0,
            0,
            id="d76",
        ),
        pytest.param(
            77,
            0,
            0,
            id="d77",
        ),
        pytest.param(
            78,
            0,
            0,
            id="d78",
        ),
        pytest.param(
            79,
            0,
            0,
            id="d79",
        ),
        pytest.param(
            80,
            0,
            0,
            id="d80",
        ),
        pytest.param(
            81,
            0,
            0,
            id="d81",
        ),
        pytest.param(
            82,
            0,
            0,
            id="d82",
        ),
        pytest.param(
            83,
            0,
            0,
            id="d83",
        ),
        pytest.param(
            84,
            0,
            0,
            id="d84",
        ),
        pytest.param(
            85,
            0,
            0,
            id="d85",
        ),
        pytest.param(
            86,
            0,
            0,
            id="d86",
        ),
        pytest.param(
            87,
            0,
            0,
            id="d87",
        ),
        pytest.param(
            88,
            0,
            0,
            id="d88",
        ),
        pytest.param(
            89,
            0,
            0,
            id="d89",
        ),
        pytest.param(
            90,
            0,
            0,
            id="d90",
        ),
        pytest.param(
            91,
            0,
            0,
            id="d91",
        ),
        pytest.param(
            92,
            0,
            0,
            id="d92",
        ),
        pytest.param(
            93,
            0,
            0,
            id="d93",
        ),
        pytest.param(
            94,
            0,
            0,
            id="d94",
        ),
        pytest.param(
            95,
            0,
            0,
            id="d95",
        ),
        pytest.param(
            96,
            0,
            0,
            id="d96",
        ),
        pytest.param(
            97,
            0,
            0,
            id="d97",
        ),
        pytest.param(
            98,
            0,
            0,
            id="d98",
        ),
        pytest.param(
            99,
            0,
            0,
            id="d99",
        ),
        pytest.param(
            100,
            0,
            0,
            id="d100",
        ),
        pytest.param(
            101,
            0,
            0,
            id="d101",
        ),
        pytest.param(
            102,
            0,
            0,
            id="d102",
        ),
        pytest.param(
            103,
            0,
            0,
            id="d103",
        ),
        pytest.param(
            104,
            0,
            0,
            id="d104",
        ),
        pytest.param(
            105,
            0,
            0,
            id="d105",
        ),
        pytest.param(
            106,
            0,
            0,
            id="d106",
        ),
        pytest.param(
            107,
            0,
            0,
            id="d107",
        ),
        pytest.param(
            108,
            0,
            0,
            id="d108",
        ),
        pytest.param(
            109,
            0,
            0,
            id="d109",
        ),
        pytest.param(
            110,
            0,
            0,
            id="d110",
        ),
        pytest.param(
            111,
            0,
            0,
            id="d111",
        ),
        pytest.param(
            112,
            0,
            0,
            id="d112",
        ),
        pytest.param(
            113,
            0,
            0,
            id="d113",
        ),
        pytest.param(
            114,
            0,
            0,
            id="d114",
        ),
        pytest.param(
            115,
            0,
            0,
            id="d115",
        ),
        pytest.param(
            116,
            0,
            0,
            id="d116",
        ),
        pytest.param(
            117,
            0,
            0,
            id="d117",
        ),
        pytest.param(
            118,
            0,
            0,
            id="d118",
        ),
        pytest.param(
            119,
            0,
            0,
            id="d119",
        ),
        pytest.param(
            120,
            0,
            0,
            id="d120",
        ),
        pytest.param(
            121,
            0,
            0,
            id="d121",
        ),
        pytest.param(
            122,
            0,
            0,
            id="d122",
        ),
        pytest.param(
            123,
            0,
            0,
            id="d123",
        ),
        pytest.param(
            124,
            0,
            0,
            id="d124",
        ),
        pytest.param(
            125,
            0,
            0,
            id="d125",
        ),
        pytest.param(
            126,
            0,
            0,
            id="d126",
        ),
        pytest.param(
            127,
            0,
            0,
            id="d127",
        ),
        pytest.param(
            128,
            0,
            0,
            id="d128",
        ),
        pytest.param(
            129,
            0,
            0,
            id="d129",
        ),
        pytest.param(
            130,
            0,
            0,
            id="d130",
        ),
        pytest.param(
            131,
            0,
            0,
            id="d131",
        ),
        pytest.param(
            132,
            0,
            0,
            id="d132",
        ),
        pytest.param(
            133,
            0,
            0,
            id="d133",
        ),
        pytest.param(
            134,
            0,
            0,
            id="d134",
        ),
        pytest.param(
            135,
            0,
            0,
            id="d135",
        ),
        pytest.param(
            136,
            0,
            0,
            id="d136",
        ),
        pytest.param(
            137,
            0,
            0,
            id="d137",
        ),
        pytest.param(
            138,
            0,
            0,
            id="d138",
        ),
        pytest.param(
            139,
            0,
            0,
            id="d139",
        ),
        pytest.param(
            140,
            0,
            0,
            id="d140",
        ),
        pytest.param(
            141,
            0,
            0,
            id="d141",
        ),
        pytest.param(
            142,
            0,
            0,
            id="d142",
        ),
        pytest.param(
            143,
            0,
            0,
            id="d143",
        ),
        pytest.param(
            144,
            0,
            0,
            id="d144",
        ),
        pytest.param(
            145,
            0,
            0,
            id="d145",
        ),
        pytest.param(
            146,
            0,
            0,
            id="d146",
        ),
        pytest.param(
            147,
            0,
            0,
            id="d147",
        ),
        pytest.param(
            148,
            0,
            0,
            id="d148",
        ),
        pytest.param(
            149,
            0,
            0,
            id="d149",
        ),
        pytest.param(
            150,
            0,
            0,
            id="d150",
        ),
        pytest.param(
            151,
            0,
            0,
            id="d151",
        ),
        pytest.param(
            152,
            0,
            0,
            id="d152",
        ),
        pytest.param(
            153,
            0,
            0,
            id="d153",
        ),
        pytest.param(
            154,
            0,
            0,
            id="d154",
        ),
        pytest.param(
            155,
            0,
            0,
            id="d155",
        ),
        pytest.param(
            156,
            0,
            0,
            id="d156",
        ),
        pytest.param(
            157,
            0,
            0,
            id="d157",
        ),
        pytest.param(
            158,
            0,
            0,
            id="d158",
        ),
        pytest.param(
            159,
            0,
            0,
            id="d159",
        ),
        pytest.param(
            160,
            0,
            0,
            id="d160",
        ),
        pytest.param(
            161,
            0,
            0,
            id="d161",
        ),
        pytest.param(
            162,
            0,
            0,
            id="d162",
        ),
        pytest.param(
            163,
            0,
            0,
            id="d163",
        ),
        pytest.param(
            164,
            0,
            0,
            id="d164",
        ),
        pytest.param(
            165,
            0,
            0,
            id="d165",
        ),
        pytest.param(
            166,
            0,
            0,
            id="d166",
        ),
        pytest.param(
            167,
            0,
            0,
            id="d167",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_clear_return_buffer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
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
    #    // no need to complicate things with an ABI
    #    let bufLen := calldataload(0)
    #    mstore(0, 0x60A7)
    #    return(0, bufLen)
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.PUSH1[0x0]
        + Op.RETURN,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xBD0BB2600F59ACDEE19A917DB4F3F7B00C9C9759),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // no need to complicate things with an ABI
    #    let bufLen := calldataload(0)
    #    mstore(0, 0x60A7)
    #    revert(0, bufLen)
    # }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.PUSH1[0x0]
        + Op.REVERT,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x4C24D17E84F86907F0A33776F83C754D52E46D13),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // no need to complicate things with an ABI
    #    let addr   := calldataload(0x00)
    #    let bufLen := calldataload(0x20)
    #    let static := calldataload(0x40)
    #    mstore(0, bufLen)
    #    pop(call(gas(), addr, 0, 0, 0x20, 0, 0x20))
    #    sstore(0, returndatasize())
    #    sstore(1, address())
    #    stop()
    # }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x20]
        + Op.PUSH1[0x0]
        + Op.DUP2 * 2
        + Op.DUP1
        + Op.CALLDATALOAD(offset=Op.DUP1)
        + Op.MSTORE(offset=Op.DUP3, value=Op.CALLDATALOAD(offset=Op.DUP4))
        + Op.GAS
        + Op.POP(Op.CALL)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x1, value=Op.ADDRESS)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x4940BB1DE279F6B55DC0BF40ED1FDEF517D8C2E9),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // no need to complicate things with an ABI
    #    let addr   := calldataload(0x00)
    #    let bufLen := calldataload(0x20)
    #    let static := calldataload(0x40)
    #    mstore(0, bufLen)
    #    pop(call(gas(), addr, 0, 0, 0x20, 0, 0x20))
    #    sstore(0, returndatasize())
    #    sstore(1, address())
    #    stop()
    # }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x20]
        + Op.PUSH1[0x0]
        + Op.DUP2 * 2
        + Op.DUP1
        + Op.CALLDATALOAD(offset=Op.DUP1)
        + Op.MSTORE(offset=Op.DUP3, value=Op.CALLDATALOAD(offset=Op.DUP4))
        + Op.GAS
        + Op.POP(Op.CALL)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x1, value=Op.ADDRESS)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0FABE6F4DFA10093ECD1C05DF08EE0B199F2F36D),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // no need to complicate things with an ABI
    #    let addr   := calldataload(0x00)
    #    let bufLen := calldataload(0x20)
    #    mstore(0, bufLen)
    #    pop(call(gas(), addr, 0, 0, 0x20, 0, 0x20))
    #
    #    // Crash with an illegal opcode
    #    verbatim_0i_0o("0xFE")
    # }
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("602060008181808035833582525af1503078464500"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x421AB4BF2FF9BD61E45075062AEC737A6F1B726D),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // The operation that we ran and that after which we're supposed
    #    // to have an empty buffer
    #    //
    #    // 0xF0 means CREATE
    #    // 0xF1 means CALL
    #    // 0xF2 means CALLCODE
    #    // 0xF4 means DELEGATECALL
    #    // 0xF5 means CREATE2
    #    // 0xFA means STATICCALL
    #    // 0x11<operation> means that operation, but it fails
    #    let operation := calldataload(0x04)
    #
    #    // 0xF3F3 means the buffer is RETURNed
    #    // 0xFDFD means the buffer is REVERTed
    #    let bufferFrom := calldataload(0x24)
    #
    #    // The length of the buffer that the RETURN or REVERT returns
    #    let bufLen := calldataload(0x44)
    #
    #    let codeLen
    #
    #    // Put the constructor code at 0x00-length, and return that length
    #    function makeConstructor(addr, len) -> retVal {
    #      // The constructor code CALLs the appropriate contract with the specified  # noqa: E501
    #      // buffer length
    #      //
    #      // Write the buffer length to memory (so we can send it)
    #      //    0x0 PUSH32 <bufLen>
    # ... (155 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x44)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMPI(pc=0x19F, condition=Op.EQ(Op.DUP2, 0xF0))
        + Op.JUMPI(pc=0x18A, condition=Op.EQ(0x11F0, Op.DUP1))
        + Op.JUMPI(pc=0x17C, condition=Op.EQ(0xF5, Op.DUP1))
        + Op.JUMPI(pc=0x164, condition=Op.EQ(0x11F5, Op.DUP1))
        + Op.JUMPI(pc=0x147, condition=Op.EQ(0xF1, Op.DUP1))
        + Op.JUMPI(pc=0x129, condition=Op.EQ(0x11F1, Op.DUP1))
        + Op.JUMPI(pc=0x10C, condition=Op.EQ(0xF2, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0xEE], condition=Op.EQ(0x11F2, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0xD2], condition=Op.EQ(0xF4, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0xB5], condition=Op.EQ(0x11F4, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x96], condition=Op.EQ(0xFA, Op.DUP1))
        + Op.PUSH2[0x11FA]
        + Op.JUMPI(pc=Op.PUSH2[0x72], condition=Op.EQ)
        + Op.REVERT(offset=Op.DUP1, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0xBAD0CA11,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x57A700CA11ED,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xBAD0CA11,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA11ED,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xBAD0CA11,
                value=Op.DUP1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA11ED,
                value=Op.DUP1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xBAD0CA11,
                value=Op.DUP1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xCA11ED,
                value=Op.DUP1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP2
        + Op.PUSH2[0x172]
        + Op.SWAP2
        + Op.JUMP(pc=0x23E)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.POP(Op.CREATE2)
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP2
        + Op.PUSH2[0x172]
        + Op.SWAP2
        + Op.JUMP(pc=0x1A6)
        + Op.JUMPDEST
        + Op.POP
        + Op.SWAP1
        + Op.PUSH2[0x195]
        + Op.SWAP2
        + Op.JUMP(pc=0x23E)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.POP(Op.CREATE)
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.POP
        + Op.SWAP1
        + Op.PUSH2[0x195]
        + Op.SWAP2
        + Op.JUMPDEST
        + Op.SWAP1
        + Op.MSTORE8(offset=0x0, value=0x7F)
        + Op.PUSH1[0x1]
        + Op.MSTORE
        + Op.MSTORE8(offset=0x21, value=0x60)
        + Op.MSTORE8(offset=0x22, value=0x0)
        + Op.MSTORE8(offset=0x23, value=0x52)
        + Op.MSTORE8(offset=0x24, value=0x60)
        + Op.MSTORE8(offset=0x25, value=0xFF)
        + Op.MSTORE8(offset=0x26, value=0x60)
        + Op.MSTORE8(offset=0x27, value=0x20)
        + Op.MSTORE8(offset=0x28, value=0x60)
        + Op.MSTORE8(offset=0x29, value=0x20)
        + Op.MSTORE8(offset=0x2A, value=0x60)
        + Op.MSTORE8(offset=0x2B, value=0x0)
        + Op.MSTORE8(offset=0x2C, value=0x60)
        + Op.MSTORE8(offset=0x2D, value=0x0)
        + Op.MSTORE8(offset=0x2E, value=0x7F)
        + Op.PUSH1[0x2F]
        + Op.MSTORE
        + Op.MSTORE8(offset=0x4F, value=0x5A)
        + Op.MSTORE8(offset=0x50, value=0xF1)
        + Op.MSTORE8(offset=0x51, value=0x60)
        + Op.MSTORE8(offset=0x52, value=0x20)
        + Op.MSTORE8(offset=0x53, value=0x51)
        + Op.MSTORE8(offset=0x54, value=0x60)
        + Op.MSTORE8(offset=0x55, value=0x0)
        + Op.MSTORE8(offset=0x56, value=0x55)
        + Op.MSTORE8(offset=0x57, value=0x3D)
        + Op.MSTORE8(offset=0x58, value=0x60)
        + Op.MSTORE8(offset=0x59, value=0x1)
        + Op.MSTORE8(offset=0x5A, value=0x55)
        + Op.MSTORE8(offset=0x5B, value=0x0)
        + Op.PUSH1[0x5C]
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.SWAP1
        + Op.PUSH2[0x248]
        + Op.SWAP2
        + Op.JUMP(pc=0x1A6)
        + Op.JUMPDEST
        + Op.MSTORE8(offset=Op.SUB(Op.DUP3, 0x1), value=0xFE)
        + Op.SWAP1
        + Op.JUMP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x48DB33B0A06DD1E98DF44D8BEF0DA3F1D948571D),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    tx_data = [
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF1) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF2) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xF4) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0xFA) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F1) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F2) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F4) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11FA) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F0) + Hash(0xFDFD) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xFDFD) + Hash(0x20),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3F3) + Hash(0x1000),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xF3FD) + Hash(0x1),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xFDFD) + Hash(0x10),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xFDFD) + Hash(0xFF),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xFDFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xFDFD) + Hash(0xFFF),
        Bytes("048071d3") + Hash(0x11F5) + Hash(0xFDFD) + Hash(0x1000),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        nonce=1,
    )

    post = {target: Account(storage=_storage_with_any({0: 0}, [1]))}

    state_test(env=env, pre=pre, post=post, tx=tx)
