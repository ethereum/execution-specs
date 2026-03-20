"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stRevertTest/stateRevertFiller.yml
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
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/stateRevertFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(3, 0, 0, id="case0"),
        pytest.param(4, 0, 0, id="case1"),
        pytest.param(1, 0, 0, id="case2"),
        pytest.param(0, 0, 0, id="case3"),
        pytest.param(6, 0, 0, id="case4"),
        pytest.param(5, 0, 0, id="case5"),
        pytest.param(2, 0, 0, id="case6"),
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
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA62D63F95900B04CCD3FEE13360DE78966F24695945E8B2C09E646352BC5AF94
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1001)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=0xDEAD,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x2B, condition=Op.ISZERO(0x1))
            + Op.POP(Op.SHA3(offset=0x0, size=0x1000000))
            + Op.JUMP(pc=0x18)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x16d83da4c22c26f92c5a8d4cedf367e171f60977"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_1 = pre.deploy_contract(
        code=bytes.fromhex(
            "610103600155600060006000600061dead6175305a03f450ba"
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x1985064d96baaf3305fee248de22965fbf7fbab6"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     [[0]] 0x60A7
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x60A7)
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x3559afe49654b532b7e67e6acd87deb8c569e7ad"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x4edc28ff01c9f8731ede6d0fd953da91f749a659"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1000)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=0xDEAD,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.REVERT(offset=0x0, size=0x10)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x71a06d553f1ac38b5e568ce5a1b5df253ad08d73"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x105)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=0xDEAD,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.ADD(Op.ADD, Op.ADD)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xbf0fc73e06f3b2eca8cb8094bdb81d4d2aa2f9b0"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x104)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=0xDEAD,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMP(pc=0x0)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xdd77382f06bfeea4258e6f7bffc6d9d31b885815"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x106)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=0xDEAD,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.PC
            + Op.JUMP(pc=Op.SUB(Op.PC, 0x4))
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xe08a8de27b3798640d504f1431a360f276b9f2ae"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1002)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=0xDEAD,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xebe3a4514feca3eb2819bf83ebd926c5e4143739"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "611001600155600060006000600061dead6175305a03f4505b600115602b576301000000600020506018565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "610103600155600060006000600061dead6175305a03f450ba"
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "6160a76000556000600060006000600435611000015af400"
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("6160a760025500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "611000600155600060006000600061dead6175305a03f45060106000fd00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "610105600155600060006000600061dead6175305a03f450010101"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "610104600155600060006000600061dead6175305a03f450600056"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "610106600155600060006000600061dead6175305a03f4505b586004580356"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "611002600155600060006000600061dead6175305a03f450600160000360002000"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
