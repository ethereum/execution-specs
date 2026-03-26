"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP2930/coinbaseT2Filler.yml
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
    AccessList,
    Hash,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
]
TX_GAS = [16777216]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])

TX_ACCESS_LISTS: dict[int, list] = {
    0: [
        AccessList(
            address=Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3"),
            storage_keys=[
            ],
        ),
    ],
    1: [
        AccessList(
            address=Address("0x000000000000000000000000000000000000ba5a"),
            storage_keys=[
            ],
        ),
    ],
}


def _tx_access_list(d: int) -> list | None:
    """Get access list for data index d. None means no access list (legacy tx)."""
    return TX_ACCESS_LISTS.get(d)


@pytest.mark.ported_from(
    ["state_tests/stEIP2930/coinbaseT2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="T2baseInList",
        ),
        pytest.param(
            1, 0, 0,
            id="T2baseNotInList",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_t2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    sender = EOA(
        key=0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=100,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin
    # { 
    #   mstore(0, gas())
    #   pop(call(gas(), <eoa:0x000000000000000000000000000000000000ba5e>, 1000000, 0, 0, 0, 0))
    #   mstore(0x20, gas())
    # 
    #   // The 24 is the cost of twi gas(), seven pushes(), a pop(), and an mstore()
    #   sstore(0, sub(sub(mload(0), mload(0x20)),33))
    # }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CALL(gas=Op.GAS, address=0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3, value=0xf4240, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)), 0x21))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=1,
        address=Address("0x30873f83c35401e315e6e5994c012f1ee8119585"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[coinbase] = Account(balance=0, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 6800})},
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 6800})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        max_fee_per_gas=10000,
        max_priority_fee_per_gas=100,
        nonce=1,
        access_list=_tx_access_list(d),
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
