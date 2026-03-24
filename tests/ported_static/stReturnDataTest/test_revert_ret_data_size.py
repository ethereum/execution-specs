"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stReturnDataTest/revertRetDataSizeFiller.yml
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
    ["tests/static/state_tests/stReturnDataTest/revertRetDataSizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 64, 2: 24743}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_ret_data_size(
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
        code=Op.POP + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.JUMP(pc=0x0),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000300"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.JUMPI(pc=0x1, condition=0x1),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000400"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.INVALID + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000500"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.DIV(Op.SUB(0x0, 0x1), 0x2))
            + Op.MSTORE(offset=0x20, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.RETURN(offset=0x0, size=0x40)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {   ;  $4 is the type of thing that fails
    #     ; $36 is the failure itself
    #
    #     (def 'callType   $4)
    #     (def 'call         0xf1)
    #     (def 'callcode     0xf2)
    #     (def 'delegatecall 0xf4)
    #     (def 'staticcall   0xfa)
    #     (def 'create       0xf0)
    #     (def 'create2      0xf5)
    #
    #     (def 'failureType $36)
    #     (def 'oog 0)
    #
    #     ; We need these values for CREATE(2)
    #     (def 'uf        0x0200)
    #     (def 'jmp       0x0300)
    #     (def 'jmpi      0x0400)
    #     (def 'badOpcode 0x0500)
    #     (def 'badCall   0xFF00)
    #
    #     (def 'NOP 0)
    #
    #     ; Code for CREATE(2) to fail
    #
    #     (def 'codeLoc      0x0000)
    #     (def 'codeLength   0x0100)
    #
    #     (if (= failureType oog)
    #        [codeLength] (lll (sha3 0 (- 0 1)) codeLoc)
    # ... (170 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=Op.PUSH2[0x11],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x1F])
            + Op.JUMPDEST
            + Op.PUSH1[0x9]
            + Op.CODECOPY(dest_offset=0x0, offset=0x391, size=Op.DUP1)
            + Op.PUSH2[0x100]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x32],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xFF00),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x46])
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x100,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xFF00,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x59],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x200),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x6D])
            + Op.JUMPDEST
            + Op.MSTORE8(offset=0x0, value=0x50)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x0)
            + Op.MSTORE(offset=0x100, value=0x2)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x80],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x300),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xA4])
            + Op.JUMPDEST
            + Op.MSTORE8(offset=0x0, value=0x60)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x0)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x2), value=0x56)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x2), value=0x0)
            + Op.MSTORE(offset=0x100, value=0x4)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xB7],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x400),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xEB])
            + Op.JUMPDEST
            + Op.MSTORE8(offset=0x0, value=0x60)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x1)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x2), value=0x60)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x3), value=0x1)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x4), value=0x57)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x5), value=0x0)
            + Op.MSTORE(offset=0x100, value=0x6)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xFE],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x500),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x112)
            + Op.JUMPDEST
            + Op.MSTORE8(offset=0x0, value=0xFE)
            + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x0)
            + Op.MSTORE(offset=0x100, value=0x2)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x12B,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1),
                    Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x155)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x16E,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1),
                    Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x19C)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0xF0000),
                    address=Op.CALLDATALOAD(offset=0x24),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1B5,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2),
                    Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1DF)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x0,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1F8,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2),
                    Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x221)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x24),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x23A,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4),
                    Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x260)
            + Op.JUMPDEST
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0x1000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x0,
                    address=0x1000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x279,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4),
                    Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x2A0)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x24),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2B9,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA),
                    Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x2DF)
            + Op.JUMPDEST
            + Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0x1000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x0,
                    address=0x1000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2F8,
                condition=Op.AND(
                    Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA),
                    Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
                ),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x31F)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x24),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x331,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF0),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x352)
            + Op.JUMPDEST
            + Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0x1000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CREATE(value=0x0, offset=0x0, size=Op.MLOAD(offset=0x100))
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x364,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF5),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x388)
            + Op.JUMPDEST
            + Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0x1000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CREATE2(
                    value=0x5A17,
                    offset=0x0,
                    size=0x0,
                    salt=Op.MLOAD(offset=0x100),
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x2, value=0x60A7)
            + Op.STOP
            + Op.INVALID
            + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1))
            + Op.STOP
        ),
        storage={0x0: 0x60A7, 0x1: 0x60A7},
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
