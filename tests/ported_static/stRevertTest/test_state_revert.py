"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stRevertTest/stateRevertFiller.yml
"""

import pytest
from execution_testing import (
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
@pytest.mark.pre_alloc_mutable
def test_state_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x100000000000)

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
    #     [[2]] 0x60A7
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x4EDC28FF01C9F8731EDE6D0FD953DA91F749A659),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[1]] 0x1000
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (revert 0 0x10)
    # }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1000)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=0xDEAD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.REVERT(offset=0x0, size=0x10)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x71A06D553F1AC38B5E568CE5A1B5DF253AD08D73),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[1]] 0x1001
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (while 1 (sha3 0 0x1000000))
    # }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1001)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=0xDEAD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x2B, condition=Op.ISZERO(0x1))
        + Op.POP(Op.SHA3(offset=0x0, size=0x1000000))
        + Op.JUMP(pc=0x18)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x16D83DA4C22C26F92C5A8D4CEDF367E171F60977),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[1]] 0x1002
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (sha3 0 (- 0 1))
    # }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1002)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=0xDEAD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xEBE3A4514FECA3EB2819BF83EBD926C5E4143739),  # noqa: E501
    )
    # Source: raw
    # 0x610103600155600060006000600061dead6175305a03f450BA
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "610103600155600060006000600061dead6175305a03f450ba"
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x1985064D96BAAF3305FEE248DE22965FBF7FBAB6),  # noqa: E501
    )
    # Source: raw
    # 0x610104600155600060006000600061dead6175305a03f450600056
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x104)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=0xDEAD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMP(pc=0x0),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xDD77382F06BFEEA4258E6F7BFFC6D9D31B885815),  # noqa: E501
    )
    # Source: raw
    # 0x610105600155600060006000600061dead6175305a03f450010101
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x105)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=0xDEAD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.ADD(Op.ADD, Op.ADD),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xBF0FC73E06F3B2ECA8CB8094BDB81D4D2AA2F9B0),  # noqa: E501
    )
    # Source: raw
    # 0x610106600155600060006000600061dead6175305a03f4505b586004580356
    addr_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x106)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x7530),
                address=0xDEAD,
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
        nonce=0,
        address=Address(0xE08A8DE27B3798640D504F1431A360F276B9F2AE),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] 0x60A7
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x60A7)
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x3559AFE49654B532B7E67E6ACD87DEB8C569E7AD),  # noqa: E501
    )

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x6),
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

    state_test(env=env, pre=pre, post=post, tx=tx)
