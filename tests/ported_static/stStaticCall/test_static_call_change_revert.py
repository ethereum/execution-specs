"""
Test_static_call_change_revert.

Ported from:
state_tests/stStaticCall/static_callChangeRevertFiller.json

@manually-enhanced: Do not overwrite.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callChangeRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "sstore_in_static,oog",
    [
        pytest.param(False, False),
        pytest.param(False, True),
        pytest.param(True, False),
    ],
)
def test_static_call_change_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    sstore_in_static: bool,
    oog: bool,
) -> None:
    """Test_static_call_change_revert."""
    sender = pre.fund_eoa()

    subcall_code = Op.MSTORE(offset=0x1, value=0x1)
    if sstore_in_static:
        subcall_code += Op.SSTORE(key=0x1, value=Op.SLOAD(key=0x1))
    subcall_code += Op.STOP
    subcall_contract = pre.deploy_contract(subcall_code)

    caller_storage = Storage()
    caller_code = (
        Op.SSTORE(
            key=caller_storage.store_next(not oog),
            value=Op.CALL(address=subcall_contract, value=0x1),
        )
        + Op.SSTORE(
            key=caller_storage.store_next(not oog and not sstore_in_static),
            value=Op.STATICCALL(address=subcall_contract),
        )
        + Op.SSTORE(
            key=caller_storage.store_next(not oog),
            value=Op.CALL(address=subcall_contract, value=0x1),
        )
    )
    if oog:
        caller_code += Op.MLOAD(2**256 - 1)
    caller_code += Op.STOP

    caller_contract = pre.deploy_contract(caller_code, balance=2)

    post = {
        caller_contract: Account(storage=caller_storage),
        subcall_contract: Account(balance=2 if not oog else 0),
    }

    tx = Transaction(sender=sender, to=caller_contract)

    state_test(pre=pre, post=post, tx=tx)
