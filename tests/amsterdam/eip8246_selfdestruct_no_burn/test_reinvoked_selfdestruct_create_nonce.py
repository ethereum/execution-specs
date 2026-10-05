"""
A contract created in the transaction that SELFDESTRUCTs and is re-invoked must
keep accumulating its own nonce across the re-invocations.

Under EIP-6780/EIP-8246 a contract created in the current transaction stays
callable after SELFDESTRUCT until transaction finalization, and its nonce
(bumped by every CREATE it performs) is reset only at finalization. A CREATE in
a re-invocation whose frame then reverts must roll that one bump back, but must
not reset the creator to nonce 0 or drop its earlier nonce bumps, so a later
CREATE derives its address from the correct, accumulated nonce.

This covers a gap surfaced by cross-client differential testing: the surviving
children of the re-invoked contract must sit at CREATE(address, 1) and
CREATE(address, 2), and no child is ever created at CREATE(address, 0).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Conditional,
    Fork,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import ref_spec_8246

REFERENCE_SPEC_GIT_PATH = ref_spec_8246.git_path
REFERENCE_SPEC_VERSION = ref_spec_8246.version

pytestmark = pytest.mark.valid_from("EIP8246")


def test_reinvoked_selfdestruct_create_nonce(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A created-in-tx contract A self-destructs, is re-invoked and does a CREATE
    in a frame that reverts, then is invoked once more and does a surviving
    CREATE. A's nonce keeps accumulating across the SELFDESTRUCT and the
    reverted re-invocation, so the surviving children sit at CREATE(A, 1) and
    CREATE(A, 2), and no child is ever created at CREATE(A, 0).

    A.runtime per call: CREATE an (empty) child, bumping A's nonce; then, if a
    1-byte calldata flag is non-zero, REVERT the frame, else SELFDESTRUCT to A.
    The factory calls A three times with flags 0, 1, 0.
    """
    sender = pre.fund_eoa()

    a_runtime = Op.POP(Op.CREATE(value=0, offset=0, size=0)) + Conditional(
        condition=Op.CALLDATALOAD(0),
        if_true=Op.REVERT(0, 0),
        if_false=Op.SELFDESTRUCT(Op.ADDRESS),
    )
    a_initcode = Initcode(deploy_code=a_runtime)

    def call_a(flag: int) -> Op:
        # Flag byte at memory[0x1f], passed as 1 calldata byte; A's address is
        # kept at memory[0x40], clear of the flag word.
        return Op.MSTORE(0, flag) + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(0x40),
                value=0,
                args_offset=0x1F,
                args_size=1,
                ret_offset=0,
                ret_size=0,
            )
        )

    factory = pre.deploy_contract(
        code=Om.MSTORE(a_initcode, 0)
        + Op.MSTORE(
            0x40,
            Op.CREATE2(value=0, offset=0, size=len(a_initcode), salt=0),
        )
        + call_a(0)  # call 1: CREATE child, SELFDESTRUCT(self)
        + call_a(1)  # call 2: CREATE child, REVERT (frame undone)
        + call_a(0)  # call 3: CREATE child, SELFDESTRUCT(self)
        + Op.STOP
    )

    a_address = compute_create_address(
        address=factory, salt=0, initcode=a_initcode, opcode=Op.CREATE2
    )
    child_nonce0 = compute_create_address(address=a_address, nonce=0)
    child_nonce1 = compute_create_address(address=a_address, nonce=1)
    child_nonce2 = compute_create_address(address=a_address, nonce=2)

    tx = Transaction(sender=sender, to=factory, gas_limit=4_000_000)

    empty_child = Account(nonce=1, balance=0, code=b"", storage={})

    expected_bal = None
    if fork.is_eip_enabled(7928):
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                child_nonce1: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                child_nonce2: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # None asserts the nonce-0 child is absent from the BAL.
                child_nonce0: None,
            }
        )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post={
            # A created and self-destructed with zero balance: removed.
            a_address: Account.NONEXISTENT,
            # Surviving children at the correctly accumulated nonces.
            child_nonce1: empty_child,
            child_nonce2: empty_child,
            # No child is ever created at the creator's nonce 0.
            child_nonce0: Account.NONEXISTENT,
            # CREATE2 bumped the factory nonce from 1 to 2.
            factory: Account(nonce=2),
        },
    )
