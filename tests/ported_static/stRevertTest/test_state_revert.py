"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stRevertTest/stateRevertFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/stateRevertFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="revert",
        ),
        pytest.param(
            1,
            0,
            0,
            id="outOfGas",
        ),
        pytest.param(
            2,
            0,
            0,
            id="xtremeOOG",
        ),
        pytest.param(
            3,
            0,
            0,
            id="badOpcode",
        ),
        pytest.param(
            4,
            0,
            0,
            id="jumpBadly",
        ),
        pytest.param(
            5,
            0,
            0,
            id="stackUnder",
        ),
        pytest.param(
            6,
            0,
            0,
            id="stackOver",
        ),
    ],
)
def test_state_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0x100000000000)

    # Source: lll
    # {
    #     [[2]] 0x60A7
    # }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     [[1]] 0x1000
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (revert 0 0x10)
    # }
    addr_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1000)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.REVERT(offset=0x0, size=0x10)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     [[1]] 0x1001
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (while 1 (sha3 0 0x1000000))
    # }
    addr_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1001)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=Op.PUSH20[addr],
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x3D, condition=Op.ISZERO(0x1))
        + Op.POP(Op.SHA3(offset=0x0, size=0x1000000))
        + Op.JUMP(pc=0x2A)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     [[1]] 0x1002
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (sha3 0 (- 0 1))
    # }
    addr_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1002)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: raw
    # 0x610103600155600060006000600061dead6175305a03f450BA
    addr_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x103)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Bytes("ba"),
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: raw
    # 0x610104600155600060006000600061dead6175305a03f450600056
    addr_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x104)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=Op.PUSH20[addr],
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMP(pc=0x0),
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: raw
    # 0x610105600155600060006000600061dead6175305a03f450010101
    addr_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x105)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.ADD(Op.ADD, Op.ADD),
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: raw
    # 0x610106600155600060006000600061dead6175305a03f4505b586004580356
    addr_8 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x106)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.PC
        + Op.JUMP(pc=Op.SUB(Op.PC, 0x4)),
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     [[0]] 0x60A7
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60A7)
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x4),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )

    tx_data = [
        Bytes("693c6139") + Hash(addr_2, left_padding=True),
        Bytes("693c6139") + Hash(addr_3, left_padding=True),
        Bytes("693c6139") + Hash(addr_4, left_padding=True),
        Bytes("693c6139") + Hash(addr_5, left_padding=True),
        Bytes("693c6139") + Hash(addr_6, left_padding=True),
        Bytes("693c6139") + Hash(addr_7, left_padding=True),
        Bytes("693c6139") + Hash(addr_8, left_padding=True),
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

    post = {target: Account(storage={0: 24743, 1: 0, 2: 0})}

    state_test(pre=pre, post=post, tx=tx)
