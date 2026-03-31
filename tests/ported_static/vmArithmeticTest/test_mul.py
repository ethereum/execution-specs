"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/mulFiller.yml
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
    ["state_tests/VMTests/vmArithmeticTest/mulFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="mul_2_3",
        ),
        pytest.param(
            1,
            0,
            0,
            id="mul_neg1_neg1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="mul_0_23",
        ),
        pytest.param(
            3,
            0,
            0,
            id="mul_23_1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="mul_2pow255_neg1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="mul_2pow255_2pow255",
        ),
        pytest.param(
            6,
            0,
            0,
            id="mul_2pow255min1_2pow255min1",
        ),
        pytest.param(
            7,
            0,
            0,
            id="big_pow_3",
        ),
        pytest.param(
            8,
            0,
            0,
            id="stack_underflow",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mul(
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
    contract_9 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    # Source: lll
    # {
    #     [[0]] (* 2 3)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.MUL(0x2, 0x3)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; -1 * -1
    #     ; -1 = 2^256-1 in evm arithmetic
    #     [[0]] (*
    #              0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff  # noqa: E501
    #              0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff  # noqa: E501
    #           )
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.MUL(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #      [[0]] (* 0 23)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.MUL(0x0, 0x17)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #      [[0]] (* 23 1)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.MUL(0x17, 0x1)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; 2^255 * -1 (the expected answer is 2^255,
    #    ;             because -2^255 = 2^256-2^255 in evm arithmetic)
    #    [[0]] (*
    #        0x8000000000000000000000000000000000000000000000000000000000000000
    #        0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    #    )
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.MUL(
                0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; 2^255 * 2^255
    #    ;
    #    ; the expected answer is 0, because 2^510 % 2^256 = 0
    #    [[0]] (*
    #        0x8000000000000000000000000000000000000000000000000000000000000000
    #        0x8000000000000000000000000000000000000000000000000000000000000000
    #    )
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.MUL(
                0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (2^255-1) * (2^255-1)
    #    ;
    #    ; = 2^510 - 2*2^255 + 1 = 2^510 - 2^256 + 1 = 1
    #    [[0]] (*
    #        0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    #        0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    #    )
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.MUL(
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001006),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (* (*
    #          0x1234567890abcdef0fedcba0987654321
    #          0x1234567890abcdef0fedcba0987654321
    #       )
    #       0x1234567890abcdef0fedcba0987654321
    #    )
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.MUL(
                Op.MUL(
                    0x1234567890ABCDEF0FEDCBA0987654321,
                    0x1234567890ABCDEF0FEDCBA0987654321,
                ),
                0x1234567890ABCDEF0FEDCBA0987654321,
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001007),  # noqa: E501
    )
    # Source: raw
    # 0x600160005560010200
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1) + Op.PUSH1[0x1] + Op.MUL + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001008),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0xFFFFFF,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
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
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [8, 2, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(storage={0: 0}),
                contract_5: Account(storage={0: 0}),
                contract_8: Account(storage={0: 0}),
            },
        },
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 6})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 23})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_4: Account(
                    storage={
                        0: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_6: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_7: Account(
                    storage={
                        0: 0x47D0817E4167B1EB4F9FC722B133EF9D7D9A6FB4C2C1C442D000107A5E419561,  # noqa: E501
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x6),
        Bytes("693c6139") + Hash(0x7),
        Bytes("693c6139") + Hash(0x8),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_9,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
