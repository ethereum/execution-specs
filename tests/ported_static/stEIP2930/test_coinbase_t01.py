"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/coinbaseT01Filler.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
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
    ["state_tests/stEIP2930/coinbaseT01Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="T0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="T1baseInList",
        ),
        pytest.param(
            2,
            0,
            0,
            id="T1baseNotInList",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_t01(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x7704D8A022A1BA8F3539FC82C7D7FB065ABC0DF3)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=100,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: yul
    # berlin
    # {
    #   mstore(0, gas())
    #   pop(call(gas(), <eoa:0x000000000000000000000000000000000000ba5e>, 1000000, 0, 0, 0, 0))  # noqa: E501
    #   mstore(0x20, gas())
    #
    #   // The 24 is the cost of twi gas(), seven pushes(), a pop(), and an mstore()  # noqa: E501
    #   sstore(0, sub(sub(mload(0), mload(0x20)),33))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=coinbase,
                value=0xF4240,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)), 0x21
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=1,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 6800})},
        },
        {
            "indexes": {"data": [0, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 6800})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x0),
    ]
    tx_gas = [16777216]
    tx_access_lists: dict[int, list] = {
        1: [
            AccessList(
                address=coinbase,
                storage_keys=[],
            ),
        ],
        2: [
            AccessList(
                address=Address(0x000000000000000000000000000000000000BA5A),
                storage_keys=[],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        gas_price=1000,
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
