"""
Returndatacopy after failing create case due to 0xfd code.

Ported from:
state_tests/stCreate2/returndatacopy_afterFailing_createFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/returndatacopy_afterFailing_createFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_returndatacopy_after_failing_create(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Returndatacopy after failing create case due to 0xfd code."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (MSTORE 0 0x600260005260206000fd) (create2 0 22 10 0) (SSTORE 0 (RETURNDATASIZE)) (RETURNDATACOPY 0 0 32) (SSTORE 1 (MLOAD 0)) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600260005260206000FD)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x16, size=0xA, salt=0x0))
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 1},
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
    )

    post = {contract_0: Account(storage={0: 32, 1: 2})}

    state_test(pre=pre, post=post, tx=tx)
