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
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    addr = Address(0x76FAE819612A29489A1A43208613D8F8557B8898)
    sender = EOA(
        key=0x3696BFBDBC65B14F4DC76D7762E0567E1DD55F053314276E47969D22E70A554E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xDE0B6B3A7640000, code=Op.STOP)
    pre[addr] = Account(balance=10)
    # Source: raw
    # 0x00
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        balance=10,
        nonce=0,
        address=Address(0xCC7C3C64708397216F5F8AEB34A43F1749693FA9),  # noqa: E501
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

    tx_data = [
        Op.STOP,
        Op.RETURN(offset=0x0, size=0x20),
        Op.CALL(
            gas=Op.GAS,
            address=addr_2,
            value=0x2710,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.DELEGATECALL(
            gas=Op.GAS,
            address=addr_2,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
    ]
    tx_gas = [400000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=TransactionException.SENDER_NOT_EOA,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
