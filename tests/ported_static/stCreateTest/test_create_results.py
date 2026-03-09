"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stCreateTest/CreateResultsFiller.yml
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
    ["tests/static/state_tests/stCreateTest/CreateResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000060a7"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                ),
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 32,
                        17: 24743,
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 32,
                        17: 24743,
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000060a7"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                ),
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        16: 24743,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000060a7"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                ),
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000060a7"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                ),
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000060a7"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                ),
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000060a7"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                ),
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={32: 295, 33: 551}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    }
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_results(
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
        gas_limit=4294967296,
    )

    # Source: LLL
    # {
    #   [[0]] 0x60A7
    # }   ; end of LLL code
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x00000000000000000000000000000000000060a7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'creation          0x100)
    #   (def 'callType          0x120)
    #   (def 'constructor       0x140)
    #   (def 'contractCode      0x200)
    #   (def 'constructorCode   0x300)
    #   (def 'extCode           0x400)
    #   (def 'contractLength    0x520)
    #   (def 'constructorLength 0x540)
    #   (def 'extLength         0x560)
    #   (def 'addr1             0x600)
    #   (def 'addr2             0x620)
    #   (def 'callRet           0x640)
    #   (def 'retData0          0x160)   ; storage for returned data
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [creation]       $0x04
    #   [callType]       $0x24
    #   [constructor]    $0x44
    #   ; The contract code
    #   (def 'contractMacro
    #             (lll
    #                (call 0xFFFF 0x60A7 0 0 0 0 0)
    #                contractCode
    #             ) ; inner lll
    #   )
    #   ; I did not want to rely on knowing the address at which the contract
    # ... (138 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x44))
            + Op.JUMPI(
                pc=Op.PUSH2[0x2F],
                condition=Op.OR(
                    Op.EQ(Op.MLOAD(offset=0x140), 0x0),
                    Op.EQ(Op.MLOAD(offset=0x140), 0x4),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x3E])
            + Op.JUMPDEST
            + Op.PUSH1[0x21]
            + Op.CODECOPY(dest_offset=0x300, offset=0x250, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x51],
                condition=Op.EQ(Op.MLOAD(offset=0x140), 0x1),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x60])
            + Op.JUMPDEST
            + Op.PUSH1[0x29]
            + Op.CODECOPY(dest_offset=0x300, offset=0x271, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x73],
                condition=Op.EQ(Op.MLOAD(offset=0x140), 0x2),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x82])
            + Op.JUMPDEST
            + Op.PUSH1[0x26]
            + Op.CODECOPY(dest_offset=0x300, offset=0x29A, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x95],
                condition=Op.EQ(Op.MLOAD(offset=0x140), 0x3),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xA4])
            + Op.JUMPDEST
            + Op.PUSH1[0x2C]
            + Op.CODECOPY(dest_offset=0x300, offset=0x2C0, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xB7],
                condition=Op.EQ(Op.MLOAD(offset=0x140), 0x5),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xC6])
            + Op.JUMPDEST
            + Op.PUSH1[0x28]
            + Op.CODECOPY(dest_offset=0x300, offset=0x2EC, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xD9],
                condition=Op.EQ(Op.MLOAD(offset=0x140), 0x6),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xE8])
            + Op.JUMPDEST
            + Op.PUSH1[0x2A]
            + Op.CODECOPY(dest_offset=0x300, offset=0x314, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0x33E, size=Op.DUP1)
            + Op.PUSH2[0x520]
            + Op.MSTORE
            + Op.JUMPI(pc=0x117, condition=Op.EQ(Op.MLOAD(offset=0x100), 0x1))
            + Op.MSTORE(
                offset=0x600,
                value=Op.CREATE2(
                    value=0x0,
                    offset=0x300,
                    size=Op.MLOAD(offset=0x540),
                    salt=0x5A17,
                ),
            )
            + Op.JUMP(pc=0x126)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x600,
                value=Op.CREATE(
                    value=0x0,
                    offset=0x300,
                    size=Op.MLOAD(offset=0x540),
                ),
            )
            + Op.JUMPDEST
            + Op.SSTORE(key=0x20, value=Op.PC)
            + Op.SSTORE(key=0x10, value=Op.RETURNDATASIZE)
            + Op.JUMPI(
                pc=0x143,
                condition=Op.OR(
                    Op.RETURNDATASIZE,
                    Op.EQ(Op.MLOAD(offset=0x140), 0x4),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x153)
            + Op.JUMPDEST
            + Op.RETURNDATACOPY(dest_offset=0x160, offset=0x0, size=0x20)
            + Op.SSTORE(key=0x11, value=Op.MLOAD(offset=0x160))
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x560,
                value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x600)),
            )
            + Op.EXTCODECOPY(
                address=Op.MLOAD(offset=0x600),
                dest_offset=0x400,
                offset=0x0,
                size=Op.MLOAD(offset=0x560),
            )
            + Op.SSTORE(
                key=0x12,
                value=Op.SUB(Op.MLOAD(offset=0x520), Op.MLOAD(offset=0x560)),
            )
            + Op.SSTORE(
                key=0x13,
                value=Op.SUB(Op.MLOAD(offset=0x200), Op.MLOAD(offset=0x400)),
            )
            + Op.JUMPI(pc=0x195, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x1))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1AC)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x640,
                value=Op.CALL(
                    gas=0xFFFF,
                    address=Op.MLOAD(offset=0x600),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1BF, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x2))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1D6)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x640,
                value=Op.CALLCODE(
                    gas=0xFFFF,
                    address=Op.MLOAD(offset=0x600),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1E9, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x3))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1FE)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x640,
                value=Op.DELEGATECALL(
                    gas=0xFFFF,
                    address=Op.MLOAD(offset=0x600),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x211, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x4))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x226)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x640,
                value=Op.STATICCALL(
                    gas=0xFFFF,
                    address=Op.MLOAD(offset=0x600),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.SSTORE(key=0x21, value=Op.PC)
            + Op.JUMPI(
                pc=0x23E,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x120), 0x0)),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x24D)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x14, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
            + Op.SSTORE(key=0x15, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.STOP
            + Op.INVALID
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0xF, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0x17, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.REVERT(offset=0x0, size=0x0)
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0x14, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=0x60A7)
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0x1A, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=0x60A7)
            + Op.STOP
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0x16, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=0x60A7)
            + Op.SELFDESTRUCT(address=0x0)
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x200, offset=0x18, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.CALL(
                gas=0xFFFF,
                address=0x60A7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={
            0x10: 0x60A7,
            0x12: 0x60A7,
            0x13: 0x60A7,
            0x14: 0x60A7,
            0x15: 0x60A7,
            0x20: 0x60A7,
            0x21: 0x60A7,
        },
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=9437184,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
