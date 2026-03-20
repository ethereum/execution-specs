"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000001000",
    "693c61390000000000000000000000000000000000000000000000000000000000001001",
    "693c61390000000000000000000000000000000000000000000000000000000000001002",
    "693c61390000000000000000000000000000000000000000000000000000000000001003",
    "693c61390000000000000000000000000000000000000000000000000000000000001004",
    "693c61390000000000000000000000000000000000000000000000000000000000001005",
    "693c61390000000000000000000000000000000000000000000000000000000000001006",
    "693c61390000000000000000000000000000000000000000000000000000000000001007",
    "693c61390000000000000000000000000000000000000000000000000000000000001008",
    "693c61390000000000000000000000000000000000000000000000000000000000001009",
    "693c6139000000000000000000000000000000000000000000000000000000000000100a",
    "693c61390000000000000000000000000000000000000000000000000000000000000200",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(8, 0, 0, id="case0"),
        pytest.param(9, 0, 0, id="case1"),
        pytest.param(7, 0, 0, id="case2"),
        pytest.param(6, 0, 0, id="case3"),
        pytest.param(5, 0, 0, id="case4"),
        pytest.param(4, 0, 0, id="case5"),
        pytest.param(3, 0, 0, id="case6"),
        pytest.param(2, 0, 0, id="case7"),
        pytest.param(1, 0, 0, id="case8"),
        pytest.param(0, 0, 0, id="case9"),
        pytest.param(11, 0, 0, id="case10"),
        pytest.param(10, 0, 0, id="case11"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_byte(
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

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x100, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4A,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x100), 0x20)),
            )
            + Op.SSTORE(
                key=Op.MLOAD(offset=0x100),
                value=Op.BYTE(
                    Op.MLOAD(offset=0x100),
                    0x102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F,  # noqa: E501
                ),
            )
            + Op.MSTORE(
                offset=0x100, value=Op.ADD(Op.MLOAD(offset=0x100), 0x1)
            )
            + Op.JUMP(pc=0x6)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x0), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x1), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x2), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x3), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x4), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x5), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x6), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    callee_8 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x7), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    [[0]] (byte (- 31 31) 0x8040201008040201)
    # }
    callee_9 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SUB(0x1F, 0x1F), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    [[0]] (byte (sdiv 31 32) 0x8040201008040201)
    # }
    callee_10 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.BYTE(Op.SDIV(0x1F, 0x20), 0x8040201008040201),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_11 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.ADD(Op.DUP1, Op.BYTE(0x1F, 0x1234523456)),
            )
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #     (call 0xffffff $4 0 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xFFFFFF,
                address=Op.CALLDATALOAD(offset=0x4),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    storage={0: 128},
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    ),
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    storage={0: 64},
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    storage={0: 32},
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    ),
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    storage={0: 16},
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    storage={0: 8},
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    storage={0: 4},
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    ),
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={
                        1: 1,
                        2: 2,
                        3: 3,
                        4: 4,
                        5: 5,
                        6: 6,
                        7: 7,
                        8: 8,
                        9: 9,
                        10: 10,
                        11: 11,
                        12: 12,
                        13: 13,
                        14: 14,
                        15: 15,
                        16: 16,
                        17: 17,
                        18: 18,
                        19: 19,
                        20: 20,
                        21: 21,
                        22: 22,
                        23: 23,
                        24: 24,
                        25: 25,
                        26: 26,
                        27: 27,
                        28: 28,
                        29: 29,
                        30: 30,
                        31: 31,
                    },
                    code=bytes.fromhex(
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex("641234523456601f1a8001600155")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000610100525b6020610100511015604a577e0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f610100511a610100515560016101005101610100526006565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6780402010080402016000601f031a60005500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6780402010080402016001601f031a60005500"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6780402010080402016002601f031a60005500"
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6780402010080402016003601f031a60005500"
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6780402010080402016004601f031a60005500"
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6780402010080402016005601f031a60005500"
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6780402010080402016006601f031a60005500"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6780402010080402016007601f031a60005500"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "678040201008040201601f601f031a60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "6780402010080402016020601f051a60005500"
                    )
                ),
                callee_11: Account(
                    storage={1: 172},
                    code=bytes.fromhex("641234523456601f1a8001600155"),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060043562fffffff100"
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
