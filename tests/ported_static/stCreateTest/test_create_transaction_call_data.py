"""
Tests if CALLDATALOAD, CALLDATACOPY, CODECOPY and CODESIZE work...

call data is always empty in initcode context and "code" is initcode.

Ported from:
state_tests/stCreateTest/CreateTransactionCallDataFiller.yml
"""

import pytest
from execution_testing import (
    Account,
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
    ["state_tests/stCreateTest/CreateTransactionCallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="calldataload",
        ),
        pytest.param(
            1,
            0,
            0,
            id="calldatacopy",
        ),
        pytest.param(
            2,
            0,
            0,
            id="codecopy",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_transaction_call_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Tests if CALLDATALOAD, CALLDATACOPY, CODECOPY and CODESIZE work..."""
    sender = pre.fund_eoa(amount=0x5AF3107A4000)

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    storage={}, code=b"", nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    storage={},
                    code=bytes.fromhex("3860008039386000f3"),
                    nonce=1,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.CALLDATALOAD(offset=0x21))
        + Op.STOP,
        Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x1)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.CALLDATACOPY(dest_offset=0x0, offset=0x1, size=0x20)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        Op.CODECOPY(dest_offset=Op.DUP1, offset=0x0, size=Op.CODESIZE)
        + Op.RETURN(offset=0x0, size=Op.CODESIZE),
    ]
    tx_gas = [100000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
