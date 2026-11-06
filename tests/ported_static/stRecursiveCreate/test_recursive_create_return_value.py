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
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRecursiveCreate/recursiveCreateReturnValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_recursive_create_return_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_recursive_create_return_value."""
    sender = pre.fund_eoa()

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

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        value=0x186A0,
    )

    child = compute_create_address(address=contract_0, nonce=1)
    grandchild = compute_create_address(address=child, nonce=1)
    post = {
        contract_0: Account(
            storage={0: int.from_bytes(child, "big") + 1}, nonce=2
        ),
        child: Account(
            storage={0: int.from_bytes(grandchild, "big") + 1}, nonce=2
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
