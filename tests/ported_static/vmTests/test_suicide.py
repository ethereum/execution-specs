"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmTests/suicideFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000001000",
    "693c61390000000000000000000000000000000000000000000000000000000000001001",
    "693c61390000000000000000000000000000000000000000000000000000000000001002",
]
TX_GAS = [16777216]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/suicideFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="caller",
        ),
        pytest.param(
            1, 0, 0,
            id="random",
        ),
        pytest.param(
            2, 0, 0,
            id="myself",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0000000000000000000000000000000000001000")
    contract_1 = Address("0x0000000000000000000000000000000000001001")
    contract_2 = Address("0x0000000000000000000000000000000000001002")
    contract_3 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
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
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #    (selfdestruct (caller))
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.CALLER) + Op.STOP,
        balance=0xff000000000000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (selfdestruct 0xdead)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xdead) + Op.STOP,
        balance=0x100000000000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (selfdestruct (address))
    # }
    contract_2 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
        balance=0x100000000000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (call (gas) $4 0 0 0 0 0)
    # }
    contract_3 = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x4), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0x100000000000,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5af3107a4000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(balance=0x5af31075d9de),
        contract_3: Account(balance=0xff100000000000),
    },
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x000000000000000000000000000000000000dead"): Account(balance=0x100000000000),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(balance=0x100000000000)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
