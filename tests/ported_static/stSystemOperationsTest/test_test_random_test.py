"""
Test_test_random_test.

Ported from:
state_tests/stSystemOperationsTest/testRandomTestFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/testRandomTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_test_random_test(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_test_random_test."""
    sender = pre.fund_eoa()

    # Source: raw
    # 0x424443444243434383f0155af055
    contract_0 = pre.deploy_contract(
        code=Op.TIMESTAMP
        + Op.PREVRANDAO
        + Op.NUMBER
        + Op.PREVRANDAO
        + Op.SSTORE(
            key=Op.CREATE(
                value=Op.GAS,
                offset=Op.ISZERO(
                    Op.CREATE(value=Op.DUP4, offset=Op.NUMBER, size=Op.NUMBER)
                ),
                size=Op.NUMBER,
            ),
            value=Op.TIMESTAMP,
        ),
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        gas_limit=2300000 if fork >= Amsterdam else 300000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(
            storage={
                compute_create_address(address=contract_0, nonce=2): 1000
            },
            nonce=3,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
