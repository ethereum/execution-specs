"""
Geth Failed this test on Frontier and Homestead.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest645Filler.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest645Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.parametrize(
    "tx_value, expected_post",
    [
        (4074160023, {}),
        (0, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_random_statetest645(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
    expected_post: dict,
) -> None:
    """Geth Failed this test on Frontier and Homestead."""
    coinbase = Address("0xaa0103980a7c3113d3a8f81478b0281492eb3d38")
    sender = EOA(
        key=0x0E5FB93861A38E5458E9D2FF0203D01D1D8167FA9C0DB762CC5CA50EB43B3376
    )
    contract = Address("0x0000000000000000000000000000000000000003")
    callee_1 = Address("0x9e9c03f8f885c32813db5207fd04870f08327f30")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=13175566155172316,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PC
            + Op.PUSH8[0x9B8E24022D8C28F3]
            + Op.SGT(0x84BC2F83, 0xB55A0)
            + Op.EQ(
                0xEA3E9D28799D45AA77BF1FC1A84EDF0193DEA2D610209EAAF9C8,
                0x15B61916F0F5,
            )
        ),
        balance=0xBCBAF5A33577F162,
        nonce=29,
        address=Address("0x322c72dedad1a81092ab9ba908fbec8779ce1c32"),  # noqa: E501
    )
    pre[callee_1] = Account(balance=0xB3508C0F8A22F8A1, nonce=28)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1D72DE, value=0xCBB01282)
            + Op.LOG1(
                offset=0xC396EB18074F148D96FD766DDA35B6CC250661B5F83F0ED625BA68A5FF49A,  # noqa: E501
                size=0x1EF17F23ED237D9F3262C4EB1B95112820595B127C516074DF06223DB,  # noqa: E501
                topic_1=0x22948F746C938A0CB,
            )
        ),
        balance=0x2BE1CFD5D6D6B0B7,
        nonce=175,
        address=coinbase,  # noqa: E501
    )
    pre[sender] = Account(balance=0x6F1F70FEA641F30A)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "326e3696ffc10e3e95c67d29784a35ba967d416feb1e1712098bcbb4d20454c1681694f5"  # noqa: E501
            "1d8591ff7b80f0e4da50c89a0a777fa7666abccfbd600e213bd71da4925c2a2115799e9c"  # noqa: E501
            "3bb1622f075452"
        ),
        gas_limit=26970,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest645Filler.json"],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "tx_value, expected_post",
    [
        (4074160023, {}),
        (0, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_random_statetest645_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
    expected_post: dict,
) -> None:
    """Geth Failed this test on Frontier and Homestead."""
    coinbase = Address("0xaa0103980a7c3113d3a8f81478b0281492eb3d38")
    sender = EOA(
        key=0x0E5FB93861A38E5458E9D2FF0203D01D1D8167FA9C0DB762CC5CA50EB43B3376
    )
    contract = Address("0x0000000000000000000000000000000000000003")
    callee_1 = Address("0x9e9c03f8f885c32813db5207fd04870f08327f30")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=13175566155172316,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PC
            + Op.PUSH8[0x9B8E24022D8C28F3]
            + Op.SGT(0x84BC2F83, 0xB55A0)
            + Op.EQ(
                0xEA3E9D28799D45AA77BF1FC1A84EDF0193DEA2D610209EAAF9C8,
                0x15B61916F0F5,
            )
        ),
        balance=0xBCBAF5A33577F162,
        nonce=29,
        address=Address("0x322c72dedad1a81092ab9ba908fbec8779ce1c32"),  # noqa: E501
    )
    pre[callee_1] = Account(balance=0xB3508C0F8A22F8A1, nonce=28)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1D72DE, value=0xCBB01282)
            + Op.LOG1(
                offset=0xC396EB18074F148D96FD766DDA35B6CC250661B5F83F0ED625BA68A5FF49A,  # noqa: E501
                size=0x1EF17F23ED237D9F3262C4EB1B95112820595B127C516074DF06223DB,  # noqa: E501
                topic_1=0x22948F746C938A0CB,
            )
        ),
        balance=0x2BE1CFD5D6D6B0B7,
        nonce=175,
        address=coinbase,  # noqa: E501
    )
    pre[sender] = Account(balance=0x6F1F70FEA641F30A)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "326e3696ffc10e3e95c67d29784a35ba967d416feb1e1712098bcbb4d20454c1681694f5"  # noqa: E501
            "1d8591ff7b80f0e4da50c89a0a777fa7666abccfbd600e213bd71da4925c2a2115799e9c"  # noqa: E501
            "3bb1622f075452"
        ),
        gas_limit=26970,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
