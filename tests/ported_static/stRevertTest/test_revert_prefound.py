"""
Test a prefunded account touched by a frame that succeeds or goes OOG.

Ported from:
state_tests/stRevertTest/RevertPrefoundFiller.json
state_tests/stRevertTest/RevertPrefoundOOGFiller.json
state_tests/stRevertTest/RevertPrefoundCallFiller.json
state_tests/stRevertTest/RevertPrefoundCallOOGFiller.json
state_tests/stRevertTest/RevertPrefoundEmpty_ParisFiller.json
state_tests/stRevertTest/RevertPrefoundEmptyOOG_ParisFiller.json
state_tests/stRevertTest/RevertPrefoundEmptyCall_ParisFiller.json
state_tests/stRevertTest/RevertPrefoundEmptyCallOOG_ParisFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

OOG_MEMORY_SIZE = 0xFFFFFF


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/RevertPrefoundFiller.json",
        "state_tests/stRevertTest/RevertPrefoundOOGFiller.json",
        "state_tests/stRevertTest/RevertPrefoundCallFiller.json",
        "state_tests/stRevertTest/RevertPrefoundCallOOGFiller.json",
        "state_tests/stRevertTest/RevertPrefoundEmpty_ParisFiller.json",
        "state_tests/stRevertTest/RevertPrefoundEmptyOOG_ParisFiller.json",
        "state_tests/stRevertTest/RevertPrefoundEmptyCall_ParisFiller.json",
        "state_tests/stRevertTest/RevertPrefoundEmptyCallOOG_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "touch, oog, prefund",
    [
        pytest.param("create", False, 1, id="revert_prefound"),
        pytest.param("create", True, 1, id="revert_prefound_oog"),
        pytest.param("call", False, 1, id="revert_prefound_call"),
        pytest.param("call", True, 1, id="revert_prefound_call_oog"),
        pytest.param("create", False, 10, id="revert_prefound_empty"),
        pytest.param("create", True, 10, id="revert_prefound_empty_oog"),
        pytest.param("call", False, 10, id="revert_prefound_empty_call"),
        pytest.param("call", True, 10, id="revert_prefound_empty_call_oog"),
    ],
)
def test_revert_prefound(
    state_test: StateTestFiller,
    pre: Alloc,
    touch: str,
    oog: bool,
    prefund: int,
) -> None:
    """
    Touch a prefunded account by CREATE or CALL, then optionally go OOG.

    The CREATE case prefunds the target's CREATE address. On OOG the
    target frame reverts and the prefunded account keeps its pre-state.
    """
    sender = pre.fund_eoa()

    prefound: Address
    if touch == "call":
        prefound = pre.fund_eoa(amount=prefund)
        result = Op.CALL(address=prefound, args_size=0x20, ret_size=0x20)
    elif touch == "create":
        result = Op.CREATE(value=0, offset=0, size=0x20)
    else:
        raise ValueError(f"unknown touch: {touch}")
    code = Op.SSTORE(0, result) + Op.SSTORE(1, 12)
    if oog:
        code += Op.SHA3(offset=0, size=OOG_MEMORY_SIZE)
    target = pre.deploy_contract(code=code, balance=1)
    if touch == "create":
        prefound = compute_create_address(address=target, nonce=1)
        pre.fund_address(prefound, prefund)

    tx = Transaction(sender=sender, to=target)

    if oog:
        target_storage: dict = {}
        prefound_nonce = 0
    elif touch == "create":
        target_storage = {0: prefound, 1: 12}
        prefound_nonce = 1
    else:
        target_storage = {0: 1, 1: 12}
        prefound_nonce = 0

    post = {
        target: Account(storage=target_storage),
        prefound: Account(
            storage={}, code=b"", balance=prefund, nonce=prefound_nonce
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
