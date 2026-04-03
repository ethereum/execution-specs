"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostMemSegFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/gasCostMemSegFiller.yml"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_mem_seg(
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

    # Source: lll
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'gasB4             0x000)  ; Before the action being measured
    #   (def 'gasAfter          0x020)  ; After the action being measured
    #
    #   (def 'afterVars         0x100)  ; Memory after the variables,
    #                                   ; safe to copy into
    #
    #   ; Understand CALLDATA. It is four bytes of function
    #   ; selector (irrelevant) followed by 32 byte words
    #   ; of the parameters
    #   (def 'opcode     $4 )
    #   (def 'length     $36)
    #   (def 'expectedCost $68)
    #
    #   ; NOP for if statements
    #   (def 'NOP     0)
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Run the operation
    #
    #   ; SHA3
    #   (if (= opcode 0x20) {
    #       [gasB4]    (gas)
    #       (sha3 0 length)
    #       [gasAfter] (gas)
    #   } NOP)
    # ... (70 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=Op.PUSH2[0x11],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x20),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x21])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.SHA3(offset=0x0, size=Op.CALLDATALOAD(offset=0x24)))
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x33],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x37),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x45])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.CALLDATACOPY(
            dest_offset=0x100, offset=0x0, size=Op.CALLDATALOAD(offset=0x24)
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x57],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x39),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x69])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.CODECOPY(
            dest_offset=0x100, offset=0x0, size=Op.CALLDATALOAD(offset=0x24)
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x7B],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x8A])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.LOG0(offset=0x0, size=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x9C],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xAD])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.LOG1(offset=0x0, size=Op.CALLDATALOAD(offset=0x24), topic_1=0x1)
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xBF],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA2),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xD2])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.LOG2(
            offset=0x0,
            size=Op.CALLDATALOAD(offset=0x24),
            topic_1=0x1,
            topic_2=0x2,
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xE4],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA3),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xF9])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.LOG3(
            offset=0x0,
            size=Op.CALLDATALOAD(offset=0x24),
            topic_1=0x1,
            topic_2=0x2,
            topic_3=0x3,
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x10B, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA4)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x122)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.LOG4(
            offset=0x0,
            size=Op.CALLDATALOAD(offset=0x24),
            topic_1=0x1,
            topic_2=0x2,
            topic_3=0x3,
            topic_4=0x4,
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                Op.CALLDATALOAD(offset=0x44),
            ),
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x727437E50AF8535411157A4ACA154C81D72BAAD4),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx_data = [
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x1)
        + Hash(0x3A)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x20)
        + Hash(0x3A)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x21)
        + Hash(0x43)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x40)
        + Hash(0x43)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x60)
        + Hash(0x4C)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x80)
        + Hash(0x55)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0xA0)
        + Hash(0x5E)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0xC0)
        + Hash(0x67)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0xE0)
        + Hash(0x70)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x20)
        + Hash(0x100)
        + Hash(0x79)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x1)
        + Hash(0x35)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x20)
        + Hash(0x35)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x21)
        + Hash(0x3B)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x40)
        + Hash(0x3B)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x60)
        + Hash(0x41)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x80)
        + Hash(0x47)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0xA0)
        + Hash(0x4D)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0xC0)
        + Hash(0x53)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0xE0)
        + Hash(0x59)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x37)
        + Hash(0x100)
        + Hash(0x5F)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x1)
        + Hash(0x35)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x20)
        + Hash(0x35)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x21)
        + Hash(0x3B)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x40)
        + Hash(0x3B)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x60)
        + Hash(0x41)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x80)
        + Hash(0x47)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0xA0)
        + Hash(0x4D)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0xC0)
        + Hash(0x53)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0xE0)
        + Hash(0x59)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("98eed7a4")
        + Hash(0x39)
        + Hash(0x100)
        + Hash(0x5F)
        + Hash(0xDEAD60A7)
        + Hash(0xDEADBEEF)
        + Hash(0x60A7BEEF),
        Bytes("d086d23d") + Hash(0xA0) + Hash(0x0) + Hash(0x18B),
        Bytes("d086d23d") + Hash(0xA0) + Hash(0x1) + Hash(0x193),
        Bytes("d086d23d") + Hash(0xA0) + Hash(0x2) + Hash(0x19B),
        Bytes("d086d23d") + Hash(0xA0) + Hash(0x3) + Hash(0x1A3),
        Bytes("d086d23d") + Hash(0xA0) + Hash(0x4) + Hash(0x1AB),
        Bytes("d086d23d") + Hash(0xA1) + Hash(0x0) + Hash(0x305),
        Bytes("d086d23d") + Hash(0xA1) + Hash(0x1) + Hash(0x30D),
        Bytes("d086d23d") + Hash(0xA1) + Hash(0x2) + Hash(0x315),
        Bytes("d086d23d") + Hash(0xA1) + Hash(0x3) + Hash(0x31D),
        Bytes("d086d23d") + Hash(0xA1) + Hash(0x4) + Hash(0x325),
        Bytes("d086d23d") + Hash(0xA2) + Hash(0x0) + Hash(0x47F),
        Bytes("d086d23d") + Hash(0xA2) + Hash(0x1) + Hash(0x487),
        Bytes("d086d23d") + Hash(0xA2) + Hash(0x2) + Hash(0x48F),
        Bytes("d086d23d") + Hash(0xA2) + Hash(0x3) + Hash(0x497),
        Bytes("d086d23d") + Hash(0xA2) + Hash(0x4) + Hash(0x49F),
        Bytes("d086d23d") + Hash(0xA3) + Hash(0x0) + Hash(0x5F9),
        Bytes("d086d23d") + Hash(0xA3) + Hash(0x1) + Hash(0x601),
        Bytes("d086d23d") + Hash(0xA3) + Hash(0x2) + Hash(0x609),
        Bytes("d086d23d") + Hash(0xA3) + Hash(0x3) + Hash(0x611),
        Bytes("d086d23d") + Hash(0xA3) + Hash(0x4) + Hash(0x619),
        Bytes("d086d23d") + Hash(0xA4) + Hash(0x0) + Hash(0x773),
        Bytes("d086d23d") + Hash(0xA4) + Hash(0x1) + Hash(0x77B),
        Bytes("d086d23d") + Hash(0xA4) + Hash(0x2) + Hash(0x783),
        Bytes("d086d23d") + Hash(0xA4) + Hash(0x3) + Hash(0x78B),
        Bytes("d086d23d") + Hash(0xA4) + Hash(0x4) + Hash(0x793),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
