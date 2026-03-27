"""
Test_create2_first_byte_loop.

Ported from:
state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml
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
    "1a8451e6000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000ef00000000000000000000000000000000000000000000000000000000000000f0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
]
TX_GAS = [16777216]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="firstHalf",
        ),
        pytest.param(
            1,
            0,
            0,
            id="invalidByte",
        ),
        pytest.param(
            2,
            0,
            0,
            id="secondHalf",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_first_byte_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create2_first_byte_loop."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3B9ACA00)
    # Source: yul
    # berlin
    # {
    #   let start := calldataload(4)
    #   let end := calldataload(36)
    #   // initcode: { mstore8(0, 0x00) return(0, 1) }
    #   mstore(0, 0x600060005360016000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   for { let code := start } lt(code, end) { code := add(code, 1) }
    #   {
    #     mstore8(1, code) // change returned byte in initcode
    #     if iszero(create2(0, 0, 10, 0)) { sstore(code, 1) }
    #   }
    #   sstore(256, 1)
    # }
    entry = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x600060005360016000F300000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x38, condition=Op.LT(Op.DUP2, Op.DUP2))
        + Op.SSTORE(key=0x100, value=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x1]
        + Op.SWAP2
        + Op.DUP3
        + Op.MSTORE8
        + Op.JUMPI(
            pc=0x4F,
            condition=Op.ISZERO(
                Op.CREATE2(value=Op.DUP1, offset=Op.DUP2, size=0xA, salt=0x0)
            ),
        )
        + Op.JUMPDEST
        + Op.ADD
        + Op.JUMP(pc=0x2A)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
        + Op.JUMP(pc=0x4A),
        nonce=0,
        address=Address("0x09fdd11d68be787a4c43f692a0778befc011cd35"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(storage={256: 1}, nonce=239),
                Address("0x0d03885ed4f051b06ae83d869cd60f8ebdde37d8"): Account(
                    nonce=1
                ),
                Address("0x94b507d001a223d7948119d899358a073fe5e331"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(storage={256: 1}, nonce=16),
                Address("0x896e9dc41224489ed98380921ef0aeac66115d7b"): Account(
                    nonce=1
                ),
                Address("0x070db4fa29b5d139bedb29347001bb9c3d75dc3a"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(storage={239: 1, 256: 1}, nonce=1),
                Address(
                    "0xa492678492a13f1031904de45f26a114234b668d"
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=entry,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
