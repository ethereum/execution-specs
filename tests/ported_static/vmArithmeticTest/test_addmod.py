"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/addmodFiller.yml
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
    ["state_tests/VMTests/vmArithmeticTest/addmodFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="addmod_1_2_2",
        ),
        pytest.param(
            1,
            0,
            0,
            id="addmod_neg1_neg2_2",
        ),
        pytest.param(
            2,
            0,
            0,
            id="addmod_neg6_1_3",
        ),
        pytest.param(
            3,
            0,
            0,
            id="addmod_eq_smod",
        ),
        pytest.param(
            4,
            0,
            0,
            id="addmod_eq_mod",
        ),
        pytest.param(
            5,
            0,
            0,
            id="addmod_4_1_neg3",
        ),
        pytest.param(
            6,
            0,
            0,
            id="addmod_4_1_neg3_eq",
        ),
        pytest.param(
            7,
            0,
            0,
            id="addmod_neg1_0_5",
        ),
        pytest.param(
            8,
            0,
            0,
            id="addmod_neg1_1_5",
        ),
        pytest.param(
            9,
            0,
            0,
            id="addmod_neg1_2_5",
        ),
        pytest.param(
            10,
            0,
            0,
            id="addmod_neg1_neg2_5",
        ),
        pytest.param(
            11,
            0,
            0,
            id="addmod_2_160_1_5",
        ),
        pytest.param(
            12,
            0,
            0,
            id="addmod_4_1_0",
        ),
        pytest.param(
            13,
            0,
            0,
            id="addmod_0_1_0",
        ),
        pytest.param(
            14,
            0,
            0,
            id="addmod_1_0_0",
        ),
        pytest.param(
            15,
            0,
            0,
            id="addmod_0_0_0_min_1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_addmod(
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
    contract_11 = Address(0x000000000000000000000000000000000000100B)
    contract_12 = Address(0x000000000000000000000000000000000000100C)
    contract_13 = Address(0x000000000000000000000000000000000000100D)
    contract_14 = Address(0x000000000000000000000000000000000000100E)
    contract_15 = Address(0x000000000000000000000000000000000000100F)
    contract_16 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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
    #    [[0]] (addmod 1 2 2)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(0x1, 0x2, 0x2)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod (- 0 1) (- 0 2) 2)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.ADDMOD(Op.SUB(0x0, 0x1), Op.SUB(0x0, 0x2), 0x2)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod (- 0 6) 1 3)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(Op.SUB(0x0, 0x6), 0x1, 0x3))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (eq (smod (- 0 5) 3) (addmod (- 0 6) 1 3) )
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.EQ(
                Op.SMOD(Op.SUB(0x0, 0x5), 0x3),
                Op.ADDMOD(Op.SUB(0x0, 0x6), 0x1, 0x3),
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (eq (mod  (- 0 5) 3) (addmod (- 0 6) 1 3) )
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.EQ(
                Op.MOD(Op.SUB(0x0, 0x5), 0x3),
                Op.ADDMOD(Op.SUB(0x0, 0x6), 0x1, 0x3),
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod 4 1 (- 0 3) )
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(0x4, 0x1, Op.SUB(0x0, 0x3)))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (eq (addmod 4 1 (- 0 3) ) 2 )
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.EQ(Op.ADDMOD(0x4, 0x1, Op.SUB(0x0, 0x3)), 0x2)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001006),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod (- 0 1) 0 5)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(Op.SUB(0x0, 0x1), 0x0, 0x5))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001007),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod (- 0 1) 1 5)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(Op.SUB(0x0, 0x1), 0x1, 0x5))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001008),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod (- 0 1) 2 5)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(Op.SUB(0x0, 0x1), 0x2, 0x5))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001009),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod (- 0 1) (- 0 2) 5)
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.ADDMOD(Op.SUB(0x0, 0x1), Op.SUB(0x0, 0x2), 0x5)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100A),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; ((2^160)-1 + 1) % 5
    #    [[0]] (addmod 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1 5)  # noqa: E501
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.ADDMOD(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                0x1,
                0x5,
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100B),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod 4 1 0)
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(0x4, 0x1, 0x0)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100C),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod 0 1 0)
    # }
    contract_13 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(0x0, 0x1, 0x0)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100D),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (addmod 1 0 0)
    # }
    contract_14 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADDMOD(0x1, 0x0, 0x0)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100E),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (- (addmod 0 0 0) 1)
    # }
    contract_15 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.SUB(Op.ADDMOD(0x0, 0x0, 0x0), 0x1))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100F),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract_16 = pre.deploy_contract(  # noqa: F841
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

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 2})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={0: 5})},
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_6: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_7: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_8: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_9: Account(storage={0: 2})},
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_10: Account(storage={0: 4})},
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_11: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_13: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_14: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_15: Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
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
        Bytes("693c6139") + Hash(0x9),
        Bytes("693c6139") + Hash(0xA),
        Bytes("693c6139") + Hash(0xB),
        Bytes("693c6139") + Hash(0xC),
        Bytes("693c6139") + Hash(0xD),
        Bytes("693c6139") + Hash(0xE),
        Bytes("693c6139") + Hash(0xF),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_16,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
