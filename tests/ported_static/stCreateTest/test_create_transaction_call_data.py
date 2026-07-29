"""
Verify CALLDATALOAD, CALLDATACOPY, CODECOPY and CODESIZE in the initcode
context of a create transaction: call data is always empty and "code" is the
initcode itself.

Ported from:
state_tests/stCreateTest/CreateTransactionCallDataFiller.yml

@manually-enhanced: Do not overwrite. The post-state now genuinely verifies
each case (observable +1 reads prove empty call data is zero, a slot-2 canary
guards against silent creation failure, and the CODECOPY case asserts
`code=initcode`), and gas/fork boilerplate was removed in favor of maxing out
the transaction gas.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateTransactionCallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    ["calldataload", "calldatacopy", "codecopy"],
)
@pytest.mark.pre_alloc_mutable
def test_create_transaction_call_data(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: str,
) -> None:
    """Tests if CALLDATALOAD, CALLDATACOPY, CODECOPY and CODESIZE work..."""
    sender = pre.fund_eoa()

    created_contract = compute_create_address(address=sender, nonce=0)

    # Sentinel written to storage as the final init-code step. If creation
    # reverts or the init code does not run to completion, this slot stays
    # zero and the test fails instead of silently passing on an account that
    # happens to match the expected (small) values.
    canary = 0xC0DE

    # Each case sets the init code to run and the post-state it produces.
    # Call data is always empty in init code context, so the calldata reads
    # resolve to zero; the only thing that varies is the opcode under test.
    initcode: Bytecode
    post: dict
    if opcode == "calldataload":  # empty data reads 0; +1 makes it visible
        initcode = (
            Op.SSTORE(key=0x0, value=Op.ADD(Op.CALLDATALOAD(offset=0x0), 1))
            + Op.SSTORE(key=0x1, value=Op.ADD(Op.CALLDATALOAD(offset=0x21), 1))
            + Op.SSTORE(key=0x2, value=canary)
            + Op.STOP
        )
        post = {
            created_contract: Account(
                storage={0: 1, 1: 1, 2: canary}, code=b"", nonce=1
            )
        }
    elif opcode == "calldatacopy":  # empty data reads 0; +1 makes it visible
        initcode = (
            Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x1)
            + Op.SSTORE(key=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 1))
            + Op.CALLDATACOPY(dest_offset=0x0, offset=0x1, size=0x20)
            + Op.SSTORE(key=0x1, value=Op.ADD(Op.MLOAD(offset=0x0), 1))
            + Op.SSTORE(key=0x2, value=canary)
            + Op.STOP
        )
        post = {
            created_contract: Account(
                storage={0: 1, 1: 1, 2: canary}, code=b"", nonce=1
            )
        }
    else:  # "codecopy": CODECOPY/CODESIZE return the init code as the code
        initcode = Op.CODECOPY(
            dest_offset=Op.DUP1, offset=0x0, size=Op.CODESIZE
        ) + Op.RETURN(offset=0x0, size=Op.CODESIZE)
        # The init code returns its own bytes, so the deployed code is the
        # init code itself; assert against it directly rather than a
        # hand-copied hex string.
        post = {created_contract: Account(storage={}, code=initcode, nonce=1)}

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
    )

    state_test(pre=pre, post=post, tx=tx)
