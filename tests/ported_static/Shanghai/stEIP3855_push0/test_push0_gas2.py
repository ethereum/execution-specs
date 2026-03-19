"""
Test ported from static filler.

Ported from:
tests/static/state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml
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
    "0000000000000000000000000000000000001000",
    "0000000000000000000000000000000000000200",
]

TX_GAS = [300000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_push0_gas2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
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
        gas_limit=89128960,
    )

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.PUSH1[0x0]
            + Op.GAS
            + Op.SWAP1
            + Op.SWAP2
            + Op.SUB
            + Op.SWAP1
            + Op.SSTORE
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_1 = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.PUSH0
            + Op.GAS
            + Op.SWAP1
            + Op.SWAP2
            + Op.SUB
            + Op.SWAP1
            + Op.SSTORE
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)
    # Source: Yul
    # {
    #    sstore(0, call(100000, shr(96, calldataload(0)), 0, 0, 0, 0, 0))
    #    sstore(1, 1)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=Op.SHR(0x60, Op.CALLDATALOAD(offset=Op.DUP1)),
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5a60005a9091039055")),
                callee_1: Account(
                    storage={0: 4}, code=bytes.fromhex("5a5f5a9091039055")
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600080808080803560601c620186a0f16000556001805500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 5}, code=bytes.fromhex("5a60005a9091039055")
                ),
                callee_1: Account(code=bytes.fromhex("5a5f5a9091039055")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600080808080803560601c620186a0f16000556001805500"
                    ),
                ),
            },
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
