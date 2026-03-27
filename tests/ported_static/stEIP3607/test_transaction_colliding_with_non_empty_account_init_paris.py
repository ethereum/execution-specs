"""
Account with non-empty code attempts to send tx to create a contract.

Ported from:
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_init_ParisFiller.yml
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
    TransactionException,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "00",
    "60206000f3",
    "600080808061271073cc7c3c64708397216f5f8aeb34a43f1749693fa95af100",
    "600080808073cc7c3c64708397216f5f8aeb34a43f1749693fa95af400",
]
TX_GAS = [400000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    [
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_init_ParisFiller.yml"  # noqa: E501
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
            id="d0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_colliding_with_non_empty_account_init_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Account with non-empty code attempts to send tx to create a contract."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    addr_0x6295ee1b4f6dd65047762f924ecd367c17eabf8f = Address(
        "0x76fae819612a29489a1a43208613d8f8557b8898"
    )
    sender = EOA(
        key=0x3696BFBDBC65B14F4DC76D7762E0567E1DD55F053314276E47969D22E70A554E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xDE0B6B3A7640000, code=Op.STOP)
    pre[addr_0x6295ee1b4f6dd65047762f924ecd367c17eabf8f] = Account(balance=10)
    # Source: raw
    # 0x00
    addr_0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0xcc7c3c64708397216f5f8aeb34a43f1749693fa9"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": TransactionException.SENDER_NOT_EOA
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
