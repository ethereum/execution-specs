"""
Calls a contract that runs CREATE2 which deploy a code. then OOG...

Ported from:
state_tests/stCreate2/Create2OOGafterInitCodeReturndataSizeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
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
    ["state_tests/stCreate2/Create2OOGafterInitCodeReturndataSizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_create2_oo_gafter_init_code_returndata_size(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Calls a contract that runs CREATE2 which deploy a code."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (MSTORE 0 0x6960016001556001600255600052600a6016f3) (CREATE2 0 13 19 0) (EXP 2 (RETURNDATASIZE)) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=0x6960016001556001600255600052600A6016F3
        )
        + Op.POP(Op.CREATE2(value=0x0, offset=0xD, size=0x13, salt=0x0))
        + Op.EXP(0x2, Op.RETURNDATASIZE)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=2055054 if fork >= Amsterdam else 55054,
        value=1,
    )

    post = {
        contract_0: Account(balance=1),
        compute_create_address(
            address=contract_0, nonce=1
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
