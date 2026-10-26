"""
Returndatacopy_following_successful_create for CREATE2.

Ported from:
state_tests/stCreate2/returndatacopy_following_successful_createFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/returndatacopy_following_successful_createFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_returndatacopy_following_successful_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Returndatacopy_following_successful_create for CREATE2."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (create2 0 0 (lll (seq (STOP)) 0) 0) (RETURNDATACOPY 0 1 32) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x2]
        + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x1, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP
        + Op.INVALID
        + Op.STOP * 2,
        storage={0: 2},
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {contract_0: Account(storage={0: 2})}

    state_test(pre=pre, post=post, tx=tx)
