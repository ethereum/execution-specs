"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml
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
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="byte_31_big",
        ),
        pytest.param(
            1,
            0,
            0,
            id="byte_30_big",
        ),
        pytest.param(
            2,
            0,
            0,
            id="byte_29_big",
        ),
        pytest.param(
            3,
            0,
            0,
            id="byte_28_big",
        ),
        pytest.param(
            4,
            0,
            0,
            id="byte_27_big",
        ),
        pytest.param(
            5,
            0,
            0,
            id="byte_26_big",
        ),
        pytest.param(
            6,
            0,
            0,
            id="byte_25_big",
        ),
        pytest.param(
            7,
            0,
            0,
            id="byte_24_big",
        ),
        pytest.param(
            8,
            0,
            0,
            id="byte_00_big",
        ),
        pytest.param(
            9,
            0,
            0,
            id="byte_00_big_2nd",
        ),
        pytest.param(
            10,
            0,
            0,
            id="byte_asm",
        ),
        pytest.param(
            11,
            0,
            0,
            id="byte_all",
        ),
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
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x0000000000000000000000000000000000001001)
    contract_2 = Address(0x0000000000000000000000000000000000001002)
    contract_3 = Address(0x0000000000000000000000000000000000001003)
    contract_4 = Address(0x0000000000000000000000000000000000001004)
    contract_5 = Address(0x0000000000000000000000000000000000001005)
    contract_6 = Address(0x0000000000000000000000000000000000001006)
    contract_7 = Address(0x0000000000000000000000000000000000001007)
    contract_8 = Address(0x0000000000000000000000000000000000001008)
    contract_9 = Address(0x0000000000000000000000000000000000001009)
    contract_10 = Address(0x000000000000000000000000000000000000100A)
    contract_11 = Address(0x0000000000000000000000000000000000000200)
    contract_12 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: lll
    # {
    #    [[0]] (byte (- 31 0) 0x8040201008040201)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x0), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 1) 0x8040201008040201)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x1), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 2) 0x8040201008040201)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x2), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 3) 0x8040201008040201)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x3), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 4) 0x8040201008040201)
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x4), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 5) 0x8040201008040201)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x5), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 6) 0x8040201008040201)
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x6), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001006),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 7) 0x8040201008040201)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x7), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001007),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (- 31 31) 0x8040201008040201)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SUB(0x1F, 0x1F), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001008),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (byte (sdiv 31 32) 0x8040201008040201)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.BYTE(Op.SDIV(0x1F, 0x20), 0x8040201008040201)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001009),  # noqa: E501
    )
    # Source: raw
    # 0x641234523456601F1A8001600155
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1, value=Op.ADD(Op.DUP1, Op.BYTE(0x1F, 0x1234523456))
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100A),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'i   0x0100)    ; index
    #
    #    ;   (byte <n> num) = n
    #    (def 'num 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f)  # noqa: E501
    #
    #    [i] 0x00
    #
    #    (while (< @i 0x20) {
    #       [[@i]] (byte @i num)
    #       [i] (+ @i 1)
    #    })  ; while loop
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x100, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x4A, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x100), 0x20))
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x100),
            value=Op.BYTE(
                Op.MLOAD(offset=0x100),
                0x102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F,  # noqa: E501
            ),
        )
        + Op.MSTORE(offset=0x100, value=Op.ADD(Op.MLOAD(offset=0x100), 0x1))
        + Op.JUMP(pc=0x6)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000200),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call 0xffffff $4 0 0 0 0 0)
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0xFFFFFF,
            address=Op.CALLDATALOAD(offset=0x4),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 2})},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 4})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 8})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={0: 16})},
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={0: 32})},
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_6: Account(storage={0: 64})},
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_7: Account(storage={0: 128})},
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_8: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_9: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_10: Account(storage={1: 172})},
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_11: Account(
                    storage={
                        0: 0,
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
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_8, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(contract_10, left_padding=True),
        Bytes("693c6139") + Hash(contract_11, left_padding=True),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_12,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
