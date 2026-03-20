"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stRevertTest/costRevertFiller.yml
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
    "1a8451e600000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010020000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010030000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010040000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010050000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010060000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010010000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010020000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010030000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010040000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010050000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010060000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010010000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010020000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010030000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010040000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010050000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010060000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010010000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010020000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010030000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010040000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010050000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000010060000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
]

TX_GAS = [80000000]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/costRevertFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(10, 0, 0, id="case0"),
        pytest.param(17, 0, 0, id="case1"),
        pytest.param(24, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(11, 0, 0, id="case4"),
        pytest.param(18, 0, 0, id="case5"),
        pytest.param(25, 0, 0, id="case6"),
        pytest.param(4, 0, 0, id="case7"),
        pytest.param(8, 0, 0, id="case8"),
        pytest.param(15, 0, 0, id="case9"),
        pytest.param(22, 0, 0, id="case10"),
        pytest.param(1, 0, 0, id="case11"),
        pytest.param(7, 0, 0, id="case12"),
        pytest.param(14, 0, 0, id="case13"),
        pytest.param(21, 0, 0, id="case14"),
        pytest.param(0, 0, 0, id="case15"),
        pytest.param(13, 0, 0, id="case16"),
        pytest.param(20, 0, 0, id="case17"),
        pytest.param(27, 0, 0, id="case18"),
        pytest.param(6, 0, 0, id="case19"),
        pytest.param(12, 0, 0, id="case20"),
        pytest.param(19, 0, 0, id="case21"),
        pytest.param(26, 0, 0, id="case22"),
        pytest.param(5, 0, 0, id="case23"),
        pytest.param(9, 0, 0, id="case24"),
        pytest.param(16, 0, 0, id="case25"),
        pytest.param(23, 0, 0, id="case26"),
        pytest.param(2, 0, 0, id="case27"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_cost_revert(
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

    pre.deploy_contract(
        code=Op.REVERT(offset=0x0, size=0x10) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(pc=0x13, condition=Op.ISZERO(0x1))
            + Op.POP(Op.SHA3(offset=0x0, size=0x1000000))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "610103600155600060006000600061dead6175305a03f450ba"
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
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
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.LT + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.JUMPDEST + Op.PC + Op.JUMP(pc=Op.SUB(Op.PC, 0x4)),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     (if (= $36 0) {     ; CALL
    #        [0x00] (gas)
    #
    #       ; Leave us some gas even if the call takes all of it
    #       (call (- (gas) 30000) $4 0 0 0 0 0)
    #
    #       [0x20] (gas)
    #
    #       ; Opcodes between the two gas measurements cost 42 gas
    #
    #       ; 0-1            GAS         2         0  79978808
    #       ; 1-1          PUSH1         3         2  79978806
    #       ; 2-1         MSTORE         6         5  79978803
    #       ; 3-1          PUSH1         3        11  79978797
    #       ; 4-1          PUSH1         3        14  79978794
    #       ; 5-1          PUSH1         3        17  79978791
    #       ; 6-1          PUSH1         3        20  79978788
    #       ; 7-1          PUSH1         3        23  79978785
    #       ; 8-1          PUSH1         3        26  79978782
    #       ; 9-1   CALLDATALOAD         3        29  79978779
    #       ; 10-1          PUSH2         3        38  79978770
    #       ; 11-1            GAS         2        41  79978767
    #       ; 12-1            SUB         3        43  79978765
    #       ;
    #       ;  The call goes here, and the cost varies based
    #       ;  on what the call does
    #       ;
    #       ; 17-1            POP         2     24761  79954047
    #
    # ... (59 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=Op.PUSH2[0x11],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x3B])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=Op.CALLDATALOAD(offset=0x4),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x2A,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x4D],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x75])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=Op.CALLDATALOAD(offset=0x4),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x27,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x87],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x2),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xAF])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.STATICCALL(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=Op.CALLDATALOAD(offset=0x4),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x27,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xC1],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x3),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xEB])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.SUB(Op.GAS, 0x7530),
                    address=Op.CALLDATALOAD(offset=0x4),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x2A,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x100, condition=Op.GT(Op.SLOAD(key=0x0), 0x4000000))
            + Op.SLOAD(key=0x0)
            + Op.JUMP(pc=0x105)
            + Op.JUMPDEST
            + Op.PUSH3[0xFFFFFF]
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 21, 14, 7], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 2609})},
        },
        {
            "indexes": {
                "data": [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0xFFFFFF})},
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
