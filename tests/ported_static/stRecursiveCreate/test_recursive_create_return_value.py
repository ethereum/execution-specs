"""
Test_recursive_create_return_value.

Ported from:
state_tests/stRecursiveCreate/recursiveCreateReturnValueFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRecursiveCreate/recursiveCreateReturnValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_recursive_create_return_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_recursive_create_return_value."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {(CODECOPY 0 0 32) [[ 0 ]] (ADD (CREATE 0 0 32) 1) }
    contract_0 = pre.deploy_contract(
        code=Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(
            key=0x0,
            value=Op.ADD(Op.CREATE(value=0x0, offset=0x0, size=0x20), 0x1),
        )
        + Op.STOP,
        balance=0x1312D00,
    )

    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=1000000000,
        value=0x186A0,
    )

    post = {
        compute_create_address(address=contract_0, nonce=1): Account(nonce=2),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
