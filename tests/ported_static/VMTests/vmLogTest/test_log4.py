"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmLogTest/log4Filler.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000007",
    "693c61390000000000000000000000000000000000000000000000000000000000000008",
    "693c61390000000000000000000000000000000000000000000000000000000000000009",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/VMTests/vmLogTest/log4Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(7, 0, 0, id="case0"),
        pytest.param(0, 0, 0, id="case1"),
        pytest.param(5, 0, 0, id="case2"),
        pytest.param(6, 0, 0, id="case3"),
        pytest.param(8, 0, 0, id="case4"),
        pytest.param(2, 0, 0, id="case5"),
        pytest.param(3, 0, 0, id="case6"),
        pytest.param(1, 0, 0, id="case7"),
        pytest.param(4, 0, 0, id="case8"),
        pytest.param(9, 0, 0, id="case9"),
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
        code=(
            Op.LOG4(
                offset=0x0,
                size=0x0,
                topic_1=0x0,
                topic_2=0x0,
                topic_3=0x0,
                topic_4=0x0,
            )
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: LLL
    # {        ; maxTopic
    #    (def 'neg1 (- 0 1))
    #
    #    (mstore8 0 0xFF)
    #    (log4 31 1 neg1 neg1 neg1 neg1)
    #    [[0]] 0x600D
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.LOG4(
                offset=0x1F,
                size=0x1,
                topic_1=Op.SUB(0x0, 0x1),
                topic_2=Op.SUB(0x0, 0x1),
                topic_3=Op.SUB(0x0, 0x1),
                topic_4=Op.SUB(0x0, 0x1),
            )
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: LLL
    # {        ; pc
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log4 31 1 (pc) (pc) (pc) (pc))
    #    [[0]] 0x600D
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x0: 0xBAD},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {
                "data": [0, 3, 4, 5, 6, 7, 8, 9],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 24589})},
        },
        {
            "indexes": {"data": [1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 2989})},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
