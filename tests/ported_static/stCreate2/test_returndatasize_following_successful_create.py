"""
Returndatasize_following_successful_create for create2.

Ported from:
state_tests/stCreate2/returndatasize_following_successful_createFiller.json
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
    [
        "state_tests/stCreate2/returndatasize_following_successful_createFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_returndatasize_following_successful_create(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Returndatasize_following_successful_create for create2."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (seq (CREATE2 0 0 (lll (seq (mstore 0 0x112233) (RETURN 0 32)) 0) 0) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0xD]
        + Op.CODECOPY(dest_offset=0x0, offset=0x17, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        storage={0: 1},
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
    )

    post = {contract_0: Account(storage={0: 0})}

    state_test(pre=pre, post=post, tx=tx)
