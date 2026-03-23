"""
A state test with invalid transaction example filler.

Ported from:
tests/static/state_tests/stExample/invalidTrFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stExample/invalidTrFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_invalid_tr(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A state test with invalid transaction example filler."""
    coinbase = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { [[0]] (ADD 1 1) }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x4567f627abb612a28ed0a355e3fa9bf1e455677a"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160010160005500"))
            },
            "expect_exception": {
                ">=Cancun": "TransactionException.INTRINSIC_GAS_TOO_LOW"
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
