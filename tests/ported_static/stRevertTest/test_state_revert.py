"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stRevertTest/stateRevertFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

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
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/stateRevertFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="revert",
        ),
        pytest.param(
            1, 0, 0,
            id="outOfGas",
        ),
        pytest.param(
            2, 0, 0,
            id="xtremeOOG",
        ),
        pytest.param(
            3, 0, 0,
            id="badOpcode",
        ),
        pytest.param(
            4, 0, 0,
            id="jumpBadly",
        ),
        pytest.param(
            5, 0, 0,
            id="stackUnder",
        ),
        pytest.param(
            6, 0, 0,
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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xa62d63f95900b04ccd3fee13360de78966f24695945e8b2c09e646352bc5af94
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #     [[2]] 0x60A7
    # }
    addr_0x000000000000000000000000000000000000dead = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x60a7) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x4edc28ff01c9f8731ede6d0fd953da91f749a659"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[1]] 0x1000
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (revert 0 0x10)
    # }
    addr_0x0000000000000000000000000000000000001000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1000)
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x7530), address=0xdead, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.REVERT(offset=0x0, size=0x10) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x71a06d553f1ac38b5e568ce5a1b5df253ad08d73"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[1]] 0x1001
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (while 1 (sha3 0 0x1000000))
    # }
    addr_0x0000000000000000000000000000000000001001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1001)
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x7530), address=0xdead, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPDEST + Op.JUMPI(pc=0x2b, condition=Op.ISZERO(0x1))
        + Op.POP(Op.SHA3(offset=0x0, size=0x1000000)) + Op.JUMP(pc=0x18)
        + Op.JUMPDEST + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x16d83da4c22c26f92c5a8d4cedf367e171f60977"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[1]] 0x1002
    #     (delegatecall (- (gas) 30000) 0xDEAD 0 0 0 0)
    #     (sha3 0 (- 0 1))
    # }
    addr_0x0000000000000000000000000000000000001002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1002)
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x7530), address=0xdead, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xebe3a4514feca3eb2819bf83ebd926c5e4143739"),  # noqa: E501
    )
    # Source: raw
    # 0x610103600155600060006000600061dead6175305a03f450BA
    addr_0x0000000000000000000000000000000000001003 = pre.deploy_contract(
        code=bytes.fromhex("610103600155600060006000600061dead6175305a03f450ba"),  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x1985064d96baaf3305fee248de22965fbf7fbab6"),  # noqa: E501
    )
    # Source: raw
    # 0x610104600155600060006000600061dead6175305a03f450600056
    addr_0x0000000000000000000000000000000000001004 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x104)
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x7530), address=0xdead, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMP(pc=0x0),
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xdd77382f06bfeea4258e6f7bffc6d9d31b885815"),  # noqa: E501
    )
    # Source: raw
    # 0x610105600155600060006000600061dead6175305a03f450010101
    addr_0x0000000000000000000000000000000000001005 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x105)
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x7530), address=0xdead, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.ADD(Op.ADD, Op.ADD),
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xbf0fc73e06f3b2eca8cb8094bdb81d4d2aa2f9b0"),  # noqa: E501
    )
    # Source: raw
    # 0x610106600155600060006000600061dead6175305a03f4505b586004580356
    addr_0x0000000000000000000000000000000000001006 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x106)
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x7530), address=0xdead, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPDEST + Op.PC + Op.JUMP(pc=Op.SUB(Op.PC, 0x4)),
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xe08a8de27b3798640d504f1431a360f276b9f2ae"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] 0x60A7
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60a7)
        + Op.DELEGATECALL(gas=Op.GAS, address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x3559afe49654b532b7e67e6acd87deb8c569e7ad"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 2, 3, 4, 5, 6], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 24743, 1: 0, 2: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
