"""
Test_create_name_registrator_out_of_memory_bonds0.

Ported from:
state_tests/stSystemOperationsTest/createNameRegistratorOutOfMemoryBonds0Filler.json
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
        "state_tests/stSystemOperationsTest/createNameRegistratorOutOfMemoryBonds0Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_name_registrator_out_of_memory_bonds0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_name_registrator_out_of_memory_bonds0."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 23 0xfffffffffff 29) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x601080600C6000396000F3006000355415600957005B60203560003555,
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE(value=0x17, offset=0xFFFFFFFFFFF, size=0x1D),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={}, nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
