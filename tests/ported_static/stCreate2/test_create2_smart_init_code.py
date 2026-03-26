"""
create2SmartInitCode. create2 works different each time you call it

Ported from:
state_tests/stCreate2/create2SmartInitCodeFiller.json
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
    "0000000000000000000000000f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
    "0000000000000000000000001f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
]
TX_GAS = [400000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2SmartInitCodeFiller.json"],
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
def test_create2_smart_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """create2SmartInitCode."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
    contract_1 = Address("0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
    contract_2 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
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
        gas_limit=47244640256,
    )

    # Source: lll
    # { (MSTORE 0 0x600060015414601157600a6000f3601a565b60016001556001ff5b) [[1]](CREATE2 1 5 27 0) [[2]](CREATE2 1 5 27 0) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600060015414601157600a6000f3601a565b60016001556001ff5b)
        + Op.SSTORE(key=0x1, value=Op.CREATE2(value=0x1, offset=0x5, size=0x1b, salt=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.CREATE2(value=0x1, offset=0x5, size=0x1b, salt=0x0))  # noqa: E501
        + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x600060015414601157600a6000f3601c565b6001600155600a6000f35b) [[1]](CREATE2 1 3 29 0) [[2]](CREATE2 1 5 27 0) }
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600060015414601157600a6000f3601c565b6001600155600a6000f35b)
        + Op.SSTORE(key=0x1, value=Op.CREATE2(value=0x1, offset=0x3, size=0x1d, salt=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.CREATE2(value=0x1, offset=0x5, size=0x1b, salt=0x0))  # noqa: E501
        + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)
    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_2 = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0x6400000000,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x0000000000000000000000000000000000000001"): Account(balance=1),  # noqa: E501
        contract_0: Account(nonce=2),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(
                storage={
            1: 0xd27e800c69122409ac5609fe4df903745f3988a0,
            2: 0,
        },
            ),
        Address("0xd27e800c69122409ac5609fe4df903745f3988a0"): Account(
                storage={1: 1},
                code=bytes.fromhex("00000000000000000000"),
                nonce=1,
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_2,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
