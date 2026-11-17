"""
Test touching non-empty precompile accounts in a frame that runs OOG.

Ported from:
state_tests/stRevertTest/RevertPrecompiledTouch_nonceFiller.json
state_tests/stRevertTest/RevertPrecompiledTouch_noncestorageFiller.json
state_tests/stRevertTest/RevertPrecompiledTouch_ParisFiller.json
state_tests/stRevertTest/RevertPrecompiledTouch_storage_ParisFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PRECOMPILES = [Address(n) for n in range(1, 9)]


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/RevertPrecompiledTouch_nonceFiller.json",
        "state_tests/stRevertTest/RevertPrecompiledTouch_noncestorageFiller.json",  # noqa: E501
        "state_tests/stRevertTest/RevertPrecompiledTouch_ParisFiller.json",
        "state_tests/stRevertTest/RevertPrecompiledTouch_storage_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "precompile_state",
    [
        pytest.param(Account(nonce=1, balance=0, storage={}), id="nonce"),
        pytest.param(
            Account(nonce=1, balance=0, storage={0: 1}), id="noncestorage"
        ),
        pytest.param(Account(nonce=0, balance=1, storage={}), id="paris"),
        pytest.param(
            Account(nonce=0, balance=10, storage={0: 1}), id="storage_paris"
        ),
    ],
)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="d0"),
        pytest.param(Op.DELEGATECALL, id="d1"),
        pytest.param(Op.CALLCODE, id="d2"),
        pytest.param(Op.STATICCALL, id="d3"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile_state: Account,
    opcode: Op,
) -> None:
    """
    Call every precompile, then run out of gas storing GAS readings.

    The precompiles hold `precompile_state`, which must survive the
    reverted frame unchanged.
    """
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)
    for precompile in PRECOMPILES:
        pre[precompile] = precompile_state

    # Source: lll
    # { (CALL 50000 1 0 0 0 0 0) ... (CALL 50000 8 0 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }  # noqa: E501
    caller_code = Bytecode()
    for precompile in PRECOMPILES:
        caller_code += Op.POP(opcode(gas=0xC350, address=precompile))
    caller_code += (
        Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS)
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code)

    # Source: lll
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.CALLCODE(address=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=caller.rjust(32, b"\0"),
        gas_limit=100000,
    )

    post = dict.fromkeys(PRECOMPILES, precompile_state)
    post[target] = Account(storage={})

    state_test(pre=pre, post=post, tx=tx)
