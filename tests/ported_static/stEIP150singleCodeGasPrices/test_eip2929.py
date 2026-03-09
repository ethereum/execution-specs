"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml
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
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 90, 2: 211}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2590, 1: 211, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001800000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2605, 1: 105, 2: 105}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2605, 1: 105, 2: 105}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2605, 1: 105, 2: 105}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000170000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2605, 1: 105, 2: 105}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2608, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2608, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2608, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2608, 1: 108, 2: 108}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2597, 1: 97, 2: 97}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2711, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2711, 1: 211, 2: 211}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2208, 1: 208, 2: 208}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2208, 1: 90, 2: 2891}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2211, 1: 211, 2: 211}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2211, 1: 90, 2: 208}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2090, 1: 211, 2: 208}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2090, 1: 90, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2090, 1: 2891, 2: 208}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2090, 1: 2891, 2: 90}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 4991, 1: 91, 2: 91}
                )
            },
        ),
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
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

    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex("00"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     @@0x100
    # }
    pre.deploy_contract(
        code=Op.SLOAD(key=0x100) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x00000000000000000000000000000000ca110100"),  # noqa: E501
    )
    # Source: LLL
    # {
    #      (balance 0xca11)
    # }
    pre.deploy_contract(
        code=Op.BALANCE(address=0xCA11) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000ca1100ca11"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #    (def 'oper1 $4)
    #    (def 'oper2 $36)
    #    (def 'oper3 $68)
    #
    #    (def 'NOP 0)
    #    (def 'measurementCost 0x022a)
    #
    #    (def 'gasB4     0x00)
    #    (def 'gasAfter  0x20)
    #    (def 'operation 0x40)
    #
    #    ; Write to the memory so memory allocation won't affect the
    #    ; measurement
    #    [gasB4] (gas)
    #    [gasAfter] (gas)
    #
    #    ; Read addresses so that won't affect the measurement
    #    (balance 0xca1100ca11)
    #    (balance   0xca110100)
    #
    #    (def 'tests {
    #        (if (= @operation 1) @@0x100 NOP) ; SLOAD
    #        (if (= @operation 2) [[0x100]] 5 NOP) ; SSTORE
    #        (if (= @operation 11) (balance 0xca11) NOP) ; BALANCE
    #        (if (= @operation 12) (extcodesize 0xca11) NOP) ; EXTCODESIZE
    #        (if (= @operation 13) (extcodecopy 0xca11 0 0 0) NOP) ; EXTCODECOPY  # noqa: E501
    #        (if (= @operation 14) (extcodehash 0xca11) NOP) ; EXTCODEHASH
    #        (if (= @operation 21) (call 0x1000 0xca11 0 0 0 0 0) NOP) ; CALL
    #        (if (= @operation 22) (callcode 0x1000 0xca11 0 0 0 0 0) NOP) ; CALLCODE  # noqa: E501
    # ... (35 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.POP(Op.BALANCE(address=0xCA1100CA11))
            + Op.POP(Op.BALANCE(address=0xCA110100))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.JUMPI(
                pc=Op.PUSH2[0x31],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0x36])
            + Op.JUMPDEST
            + Op.SLOAD(key=0x100)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0x49],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x50])
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x5)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x61],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xB),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0x66])
            + Op.JUMPDEST
            + Op.BALANCE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0x78],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xC),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0x7D])
            + Op.JUMPDEST
            + Op.EXTCODESIZE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0x90],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xD),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x9B])
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xCA11, dest_offset=0x0, offset=0x0, size=0x0
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xAC],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xE),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0xB1])
            + Op.JUMPDEST
            + Op.EXTCODEHASH(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0xC3],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0xD5])
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0xE7],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0xF9])
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x10B, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x11B)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x12D, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x13D)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x14F, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1F))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x164)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA1100CA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x176, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x18A)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA110100,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x19C, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x1AE)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA110100,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x22A,
                ),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.JUMPI(pc=0x1DC, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x1E1)
            + Op.JUMPDEST
            + Op.SLOAD(key=0x100)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x1F4, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1FB)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x5)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x20C, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xB))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x211)
            + Op.JUMPDEST
            + Op.BALANCE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x223, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xC))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x228)
            + Op.JUMPDEST
            + Op.EXTCODESIZE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x23B, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xD))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x246)
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xCA11, dest_offset=0x0, offset=0x0, size=0x0
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x257, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xE))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x25C)
            + Op.JUMPDEST
            + Op.EXTCODEHASH(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x26E, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x280)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x292, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x2A4)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x2B6, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x2C6)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x2D8, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x2E8)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x2FA, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1F))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x30F)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA1100CA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x321, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x335)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA110100,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x347, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x359)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA110100,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x1,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x22A,
                ),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.JUMPI(pc=0x387, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x38C)
            + Op.JUMPDEST
            + Op.SLOAD(key=0x100)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x39F, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x3A6)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x5)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x3B7, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xB))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x3BC)
            + Op.JUMPDEST
            + Op.BALANCE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x3CE, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xC))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x3D3)
            + Op.JUMPDEST
            + Op.EXTCODESIZE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x3E6, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xD))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x3F1)
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xCA11, dest_offset=0x0, offset=0x0, size=0x0
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x402, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xE))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x407)
            + Op.JUMPDEST
            + Op.EXTCODEHASH(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x419, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x42B)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x43D, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x44F)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x461, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x471)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x483, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x493)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x4A5, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1F))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4BA)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA1100CA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x4CC, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4E0)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA110100,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x4F2, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x504)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA110100,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x2,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x22A,
                ),
            )
            + Op.SSTORE(key=0x100, value=0x0)
            + Op.STOP
        ),
        storage={0x100: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
