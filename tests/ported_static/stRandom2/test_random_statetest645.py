"""
Geth Failed this test on Frontier and Homestead

Ported from:
state_tests/stRandom2/randomStatetest645Filler.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "326e3696ffc10e3e95c67d29784a35ba967d416feb1e1712098bcbb4d20454c1681694f51d8591ff7b80f0e4da50c89a0a777fa7666abccfbd600e213bd71da4925c2a2115799e9c3bb1622f075452",
]
TX_GAS = [26970]
TX_VALUE = [4074160023, 0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest645Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_random_statetest645(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Geth Failed this test on Frontier and Homestead"""
    coinbase = Address("0xaa0103980a7c3113d3a8f81478b0281492eb3d38")
    addr_0xffffffffffffffffffffffffffffffffffffffff = Address("0x9e9c03f8f885c32813db5207fd04870f08327f30")  # noqa: E501
    sender = EOA(
        key=0xe5fb93861a38e5458e9d2ff0203d01d1d8167fa9c0db762cc5ca50eb43b3376
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=13175566155172316,
    )

    # Source: raw
    # 0x58679b8e24022d8c28f3620b55a06384bc2f83136515b61916f0f579ea3e9d28799d45aa77bf1fc1a84edf0193dea2d610209eaaf9c814
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.PC + Op.PUSH8[0x9b8e24022d8c28f3] + Op.SGT(0x84bc2f83, 0xb55a0)
        + Op.EQ(0xea3e9d28799d45aa77bf1fc1a84edf0193dea2d610209eaaf9c8, 0x15b61916f0f5),
        balance=0xbcbaf5a33577f162,
        nonce=29,
        address=Address("0x322c72dedad1a81092ab9ba908fbec8779ce1c32"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6f1f70fea641f30a)
    # Source: raw
    # 0x63cbb01282621d72de5268022948f746c938a0cb7c01ef17f23ed237d9f3262c4eb1b95112820595b127c516074df06223db7e0c396eb18074f148d96fd766dda35b6cc250661b5f83f0ed625ba68a5ff49aa1
    coinbase = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1d72de, value=0xcbb01282)
        + Op.LOG1(offset=0xc396eb18074f148d96fd766dda35b6cc250661b5f83f0ed625ba68a5ff49a, size=0x1ef17f23ed237d9f3262c4eb1b95112820595b127c516074df06223db, topic_1=0x22948f746c938a0cb),
        balance=0x2be1cfd5d6d6b0b7,
        nonce=175,
        address=Address("0xaa0103980a7c3113d3a8f81478b0281492eb3d38"),  # noqa: E501
    )
    pre[addr_0xffffffffffffffffffffffffffffffffffffffff] = Account(balance=0xb3508c0f8a22f8a1, nonce=28)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x1000000000000000000000000000000000000000: Account(storage={}, nonce=29),
        sender: Account(storage={}, code=b"", nonce=1),
        coinbase: Account(storage={}, nonce=175),
        addr_0xffffffffffffffffffffffffffffffffffffffff: Account(storage={}, code=b"", nonce=28),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=Address("0x0000000000000000000000000000000000000003"),
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
