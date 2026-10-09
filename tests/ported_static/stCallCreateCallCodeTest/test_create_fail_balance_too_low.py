"""
Create fails because we try to send more wei to it that we have.

Ported from:
state_tests/stCallCreateCallCodeTest/createFailBalanceTooLowFiller.json
@manually-enhanced: Do not overwrite. Gas bumped fork-conditionally
to cover EIP-8037 state-gas spill into regular gas; pre-EIP-8037
behavior unchanged.

"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createFailBalanceTooLowFiller.json"  # noqa: E501
    ],
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
def test_create_fail_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create fails because we try to send more wei to it that we have."""
    # EIP-8037 gas bumps: original values for pre-EIP-8037 forks.
    outer_tx_gas = 253021
    if fork.is_eip_enabled(8037):
        outer_tx_gas = 1265105

    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {(MSTORE 0 0x6001600255 ) (SELFDESTRUCT (CREATE 1000000000000000024 27 5)) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6001600255)
        + Op.SELFDESTRUCT(
            address=Op.CREATE(value=0xDE0B6B3A7640018, offset=0x1B, size=0x5)
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address(0x0000000000000000000000000000000000000000): Account(
                    storage={}
                ),
                compute_create_address(
                    address=contract_0, nonce=1
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    0x0000000000000000000000000000000000000000
                ): Account.NONEXISTENT,
                compute_create_address(address=contract_0, nonce=1): Account(
                    storage={2: 1}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [outer_tx_gas]
    tx_value = [23, 24]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
