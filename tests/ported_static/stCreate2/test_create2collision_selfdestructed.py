"""
Collision with address that has been selfdestructed in the same...

Ported from:
state_tests/stCreate2/create2collisionSelfdestructedFiller.json
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
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2collisionSelfdestructedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_selfdestructed(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Collision with address that has been selfdestructed in the same..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xE2B35478FDD26477CC576DD906E6277761246A3C)
    contract_1 = Address(0xAF3ECBA2FE09A4F6C19F16A9D119E44E08C2DA01)
    contract_2 = Address(0xEC2C6832D00680ECE8FF9254F81FDAB0A5A2AC50)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # { (SELFDESTRUCT 0x10) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x10) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xE2B35478FDD26477CC576DD906E6277761246A3C),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT 0x10) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x10) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xAF3ECBA2FE09A4F6C19F16A9D119E44E08C2DA01),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT 0x10) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x10) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xEC2C6832D00680ECE8FF9254F81FDAB0A5A2AC50),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(balance=0, nonce=0),
                Address("0x0000000000000000000000000000000000000010"): Account(
                    balance=1
                ),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0}, balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_1: Account(balance=0, nonce=0),
                Address("0x0000000000000000000000000000000000000010"): Account(
                    balance=1
                ),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0}, balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(balance=0, nonce=0),
                Address("0x0000000000000000000000000000000000000010"): Account(
                    balance=1
                ),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0}, balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(
            "6000600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c61c350f1506000600060006000f500"  # noqa: E501
        ),
        Bytes(
            "6000600060006000600073af3ecba2fe09a4f6c19f16a9d119e44e08c2da0161c350f15064600160015560005260006005601b6000f500"  # noqa: E501
        ),
        Bytes(
            "6000600060006000600073ec2c6832d00680ece8ff9254f81fdab0a5a2ac5061c350f1506d6460016001556000526005601bf36000526000600e60126000f500"  # noqa: E501
        ),
    ]
    tx_gas = [400000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
