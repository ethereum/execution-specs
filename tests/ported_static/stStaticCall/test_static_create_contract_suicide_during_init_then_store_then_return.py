"""
test_static_create_contract_suicide_during_init_then_store_then_return

Ported from:
state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json
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
    "600060006000600073c94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273d94f5374fce5edbc8e2a8697c15331677e6ebf0bff600060006000600073d94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa50600b600055600e6012f3",
    "600060006000600073094f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273d94f5374fce5edbc8e2a8697c15331677e6ebf0bff600060006000600073194f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa50600b600055600e6012f3",
]
TX_GAS = [600000]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_create_contract_suicide_during_init_then_store_then_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_create_contract_suicide_during_init_then_store_then_return"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_2 = Address("0x094f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_3 = Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # {[[1]]12}
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.STOP,
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # {[[1]]12}
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.STOP,
        nonce=0,
        address=Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) }
    contract_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x094f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE 1 1) }
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account.NONEXISTENT,  # noqa: E501
        contract_0: Account(storage={1: 0}, balance=0),
        contract_1: Account(storage={1: 0}, balance=10),
        contract_2: Account(storage={1: 0}, balance=0),
        contract_3: Account(storage={1: 0}, balance=0),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
