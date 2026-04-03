"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmLogTest/log4Filler.yml
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
    ["state_tests/VMTests/vmLogTest/log4Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="emptyMem",
        ),
        pytest.param(
            1,
            0,
            0,
            id="memStartTooHigh",
        ),
        pytest.param(
            2,
            0,
            0,
            id="memSizeTooHigh",
        ),
        pytest.param(
            3,
            0,
            0,
            id="memSizeZero",
        ),
        pytest.param(
            4,
            0,
            0,
            id="nonEmptyMem",
        ),
        pytest.param(
            5,
            0,
            0,
            id="log_0_1",
        ),
        pytest.param(
            6,
            0,
            0,
            id="log_31_1",
        ),
        pytest.param(
            7,
            0,
            0,
            id="caller",
        ),
        pytest.param(
            8,
            0,
            0,
            id="maxTopic",
        ),
        pytest.param(
            9,
            0,
            0,
            id="pc",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_log4(
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
    contract_10 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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
    # {   ; emptyMem
    #     (log4 0 0 0 0 0 0)
    #
    #     [[0]] 0x600D
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG4(
            offset=0x0,
            size=0x0,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {      ; memStartTooHigh
    #    (def 'neg1 (- 0 1))
    #
    #    [0]   0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd  # noqa: E501
    #    (log4 neg1 1 0 0 0 0)
    #    [[0]] 0x600D
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=Op.SUB(0x0, 0x1),
            size=0x1,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {        ; memSizeTooHigh
    #    (def 'neg1 (- 0 1))
    #
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 1 neg1 0 0 0 0)
    #    [[0]] 0x600D
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x1,
            size=Op.SUB(0x0, 0x1),
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {        ; memSizeZero
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 1 0 0 0 0 0)
    #    [[0]] 0x600D
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x1,
            size=0x0,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {        ; nonEmptyMem
    #    [0] 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    #    (log4 0 32 0 0 0 0)
    #    [[0]] 0x600D
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x0,
            size=0x20,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {        ; log_0_1
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 0 1 0 0 0 0)
    #    [[0]] 0x600D
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x0,
            size=0x1,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: lll
    # {        ; log_31_1
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 31 1 0 0 0 0)
    #    [[0]] 0x600D
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x1F,
            size=0x1,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001006),  # noqa: E501
    )
    # Source: lll
    # {        ; caller (as topic)
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 0 32 0 0 0 (caller))
    #    [[0]] 0x600D
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x0,
            size=0x20,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=Op.CALLER,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001007),  # noqa: E501
    )
    # Source: lll
    # {        ; maxTopic
    #    (def 'neg1 (- 0 1))
    #
    #    (mstore8 0 0xFF)
    #    (log4 31 1 neg1 neg1 neg1 neg1)
    #    [[0]] 0x600D
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG4(
            offset=0x1F,
            size=0x1,
            topic_1=Op.SUB(0x0, 0x1),
            topic_2=Op.SUB(0x0, 0x1),
            topic_3=Op.SUB(0x0, 0x1),
            topic_4=Op.SUB(0x0, 0x1),
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001008),  # noqa: E501
    )
    # Source: lll
    # {        ; pc
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 31 1 (pc) (pc) (pc) (pc))
    #    [[0]] 0x600D
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
        )
        + Op.LOG4(
            offset=0x1F,
            size=0x1,
            topic_1=Op.PC,
            topic_2=Op.PC,
            topic_3=Op.PC,
            topic_4=Op.PC,
        )
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001009),  # noqa: E501
    )
    # Source: lll
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={0: 2989},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [0, 3, 4, 5, 6, 7, 8, 9],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_10: Account(storage={0: 24589})},
        },
        {
            "indexes": {"data": [1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_10: Account(storage={0: 2989})},
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
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_10,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
