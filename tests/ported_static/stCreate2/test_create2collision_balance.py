"""
Create2 generates an account that already exists and has balance != 0.

Ported from:
state_tests/stCreate2/create2collisionBalanceFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2collisionBalanceFiller.json"],
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
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create2 generates an account that already exists and has balance != 0."""  # noqa: E501
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
    # Source: hex
    # 0x
    contract_0 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0xE2B35478FDD26477CC576DD906E6277761246A3C),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_1 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0xAF3ECBA2FE09A4F6C19F16A9D119E44E08C2DA01),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_2 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0xEC2C6832D00680ECE8FF9254F81FDAB0A5A2AC50),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(balance=1, nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_1: Account(
                    storage={1: 1}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=sender, nonce=0): Account(
                    balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(
                    storage={},
                    code=bytes.fromhex("6001600155"),
                    balance=1,
                    nonce=1,
                ),
                compute_create_address(address=sender, nonce=0): Account(
                    balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(balance=2, nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    balance=0, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.CREATE2(value=0x0, offset=0x0, size=0x0, salt=0x0) + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6001600155)
        + Op.CREATE2(value=0x0, offset=0x1B, size=0x5, salt=0x0)
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.CREATE2(value=0x0, offset=0x12, size=0xE, salt=0x0)
        + Op.STOP,
        Op.CREATE2(value=0x1, offset=0x0, size=0x0, salt=0x0) + Op.STOP,
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
