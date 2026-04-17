"""
Geth Failed this test on Frontier and Homestead.

Ported from:
state_tests/stRandom2/randomStatetest645Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest645Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
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
    """Geth Failed this test on Frontier and Homestead."""
    coinbase = Address(0xAA0103980A7C3113D3A8F81478B0281492EB3D38)
    addr_2 = Address(0x9E9C03F8F885C32813DB5207FD04870F08327F30)
    sender = EOA(
        key=0xE5FB93861A38E5458E9D2FF0203D01D1D8167FA9C0DB762CC5CA50EB43B3376
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=13175566155172316,
    )

    pre[sender] = Account(balance=0x6F1F70FEA641F30A)
    pre[addr_2] = Account(balance=0xB3508C0F8A22F8A1, nonce=28)
    # Source: raw
    # 0x58679b8e24022d8c28f3620b55a06384bc2f83136515b61916f0f579ea3e9d28799d45aa77bf1fc1a84edf0193dea2d610209eaaf9c814  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.PC
        + Op.PUSH8[0x9B8E24022D8C28F3]
        + Op.SGT(0x84BC2F83, 0xB55A0)
        + Op.EQ(
            0xEA3E9D28799D45AA77BF1FC1A84EDF0193DEA2D610209EAAF9C8,
            0x15B61916F0F5,
        ),
        balance=0xBCBAF5A33577F162,
        nonce=29,
        address=Address(0x322C72DEDAD1A81092AB9BA908FBEC8779CE1C32),  # noqa: E501
    )
    # Source: raw
    # 0x63cbb01282621d72de5268022948f746c938a0cb7c01ef17f23ed237d9f3262c4eb1b95112820595b127c516074df06223db7e0c396eb18074f148d96fd766dda35b6cc250661b5f83f0ed625ba68a5ff49aa1  # noqa: E501
    coinbase = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1D72DE, value=0xCBB01282)
        + Op.LOG1(
            offset=0xC396EB18074F148D96FD766DDA35B6CC250661B5F83F0ED625BA68A5FF49A,  # noqa: E501
            size=0x1EF17F23ED237D9F3262C4EB1B95112820595B127C516074DF06223DB,
            topic_1=0x22948F746C938A0CB,
        ),
        balance=0x2BE1CFD5D6D6B0B7,
        nonce=175,
        address=Address(0xAA0103980A7C3113D3A8F81478B0281492EB3D38),  # noqa: E501
    )

    tx_data = [
        Bytes(
            "326e3696ffc10e3e95c67d29784a35ba967d416feb1e1712098bcbb4d20454c1681694f51d8591ff7b80f0e4da50c89a0a777fa7666abccfbd600e213bd71da4925c2a2115799e9c3bb1622f075452"  # noqa: E501
        ),
    ]
    tx_gas = [26970]
    tx_value = [4074160023, 0]

    tx = Transaction(
        sender=sender,
        to=Address(0x0000000000000000000000000000000000000003),
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        addr: Account(storage={}, nonce=29),
        sender: Account(storage={}, code=b"", nonce=1),
        coinbase: Account(storage={}, nonce=175),
        addr_2: Account(storage={}, code=b"", nonce=28),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
