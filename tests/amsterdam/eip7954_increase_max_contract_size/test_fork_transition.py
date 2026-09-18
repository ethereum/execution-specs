"""
Fork transition tests for
[EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).

Tests that the new max code size and initcode size limits activate
exactly at the EIP7954 fork boundary (timestamp 15,000).
"""

from typing import Any, Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Initcode,
    Op,
    Transaction,
    TransactionException,
    TransitionFork,
    compute_create_address,
)
from execution_testing import Macros as Om

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_at_transition_to("EIP7954")

PRE_FORK_TIMESTAMP = 14_999
POST_FORK_TIMESTAMP = 15_000

FACTORY_SENTINEL = 0xFF
"""Pre-set factory storage value, left untouched by an aborted frame."""


@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(
            lambda f: f.transitions_from().max_code_size(),
            id="at_parent_max",
        ),
        pytest.param(
            lambda f: f.transitions_from().max_code_size() + 1,
            id="over_parent_max",
        ),
        pytest.param(
            lambda f: f.transitions_to().max_code_size(),
            id="at_max",
        ),
        pytest.param(
            lambda f: f.transitions_to().max_code_size() + 1,
            id="over_max",
        ),
    ],
)
def test_max_code_size_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    code_size: Callable[[TransitionFork], int],
) -> None:
    """
    Ensure a creation transaction is held to the code size limit active in
    its own block.
    """
    size = code_size(fork)
    # Memory is zeroed, so the deployed code needs no initcode payload.
    initcode = Op.RETURN(offset=0, size=size)

    blocks = []
    post: dict[Any, Account | None] = {}
    for timestamp in (PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP):
        sender = pre.fund_eoa()
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[Transaction(sender=sender, to=None, data=initcode)],
            )
        )
        deployed = size <= fork.fork_at(timestamp=timestamp).max_code_size()
        post[compute_create_address(address=sender, nonce=0)] = (
            Account(code=b"\x00" * size) if deployed else Account.NONEXISTENT
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(
            lambda f: f.transitions_from().max_code_size(),
            id="at_parent_max",
        ),
        pytest.param(
            lambda f: f.transitions_from().max_code_size() + 1,
            id="over_parent_max",
        ),
        pytest.param(
            lambda f: f.transitions_to().max_code_size(),
            id="at_max",
        ),
        pytest.param(
            lambda f: f.transitions_to().max_code_size() + 1,
            id="over_max",
        ),
    ],
)
def test_max_code_size_via_create_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    code_size: Callable[[TransitionFork], int],
    create_opcode: Op,
) -> None:
    """
    Ensure a create opcode is held to the code size limit active in its own
    block.
    """
    size = code_size(fork)
    initcode_bytes = bytes(Op.RETURN(offset=0, size=size))

    create_call = (
        create_opcode(value=0, offset=0, size=len(initcode_bytes), salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=len(initcode_bytes))
    )
    factory_code = (
        Om.MSTORE(initcode_bytes, 0) + Op.SSTORE(0, create_call) + Op.STOP
    )

    blocks = []
    post: dict[Any, Account | None] = {}
    for timestamp in (PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP):
        sender = pre.fund_eoa()
        # A factory per block keeps both creations at the same nonce.
        factory = pre.deploy_contract(
            factory_code, storage={0: FACTORY_SENTINEL}
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[Transaction(sender=sender, to=factory)],
            )
        )
        created = size <= fork.fork_at(timestamp=timestamp).max_code_size()
        create_address = compute_create_address(
            address=factory,
            nonce=1,
            initcode=initcode_bytes,
            opcode=create_opcode,
        )
        # The oversized code is only detected once the initcode returns, so
        # the create opcode pushes zero over the sentinel and the factory
        # keeps running.
        post[factory] = Account(storage={0: create_address if created else 0})
        post[create_address] = (
            Account(code=b"\x00" * size) if created else Account.NONEXISTENT
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize(
    "initcode_size",
    [
        pytest.param(
            lambda f: f.transitions_from().max_initcode_size(),
            id="at_parent_max",
            marks=[
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork(),
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork(),
            ],
        ),
        pytest.param(
            lambda f: f.transitions_from().max_initcode_size() + 1,
            id="over_parent_max",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork(),
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork(),
            ],
        ),
        pytest.param(
            lambda f: f.transitions_to().max_initcode_size(),
            id="at_max",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            lambda f: f.transitions_to().max_initcode_size() + 1,
            id="over_max",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork(),
            ],
        ),
    ],
)
def test_max_initcode_size_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    initcode_size: Callable[[TransitionFork], int],
) -> None:
    """
    Ensure a creation transaction is validated against the initcode size
    limit active in its own block.
    """
    size = initcode_size(fork)
    initcode = Initcode(deploy_code=Op.STOP, initcode_length=size)

    blocks = []
    post: dict[Any, Account | None] = {}
    for timestamp in (PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP):
        sender = pre.fund_eoa()
        accepted = (
            size <= fork.fork_at(timestamp=timestamp).max_initcode_size()
        )
        error = (
            None if accepted else TransactionException.INITCODE_SIZE_EXCEEDED
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        sender=sender,
                        to=None,
                        data=initcode,
                        error=error,
                    )
                ],
                exception=error,
            )
        )
        post[compute_create_address(address=sender, nonce=0)] = (
            Account(code=Op.STOP) if accepted else Account.NONEXISTENT
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "initcode_size",
    [
        pytest.param(
            lambda f: f.transitions_from().max_initcode_size(),
            id="at_parent_max",
        ),
        pytest.param(
            lambda f: f.transitions_from().max_initcode_size() + 1,
            id="over_parent_max",
        ),
        pytest.param(
            lambda f: f.transitions_to().max_initcode_size(),
            id="at_max",
        ),
        pytest.param(
            lambda f: f.transitions_to().max_initcode_size() + 1,
            id="over_max",
        ),
    ],
)
def test_max_initcode_size_via_create_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    initcode_size: Callable[[TransitionFork], int],
    create_opcode: Op,
) -> None:
    """
    Ensure a create opcode is held to the initcode size limit active in its
    own block.
    """
    size = initcode_size(fork)
    # The initcode returns no code, so only its leading bytes are written
    # and the rest of the size comes from zeroed memory.
    initcode_prologue = bytes(Op.RETURN(offset=0, size=0))
    initcode_bytes = initcode_prologue.ljust(size, b"\x00")

    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )
    factory_code = (
        Om.MSTORE(initcode_prologue, 0) + Op.SSTORE(0, create_call) + Op.STOP
    )

    blocks = []
    post: dict[Any, Account | None] = {}
    for timestamp in (PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP):
        sender = pre.fund_eoa()
        factory = pre.deploy_contract(
            factory_code, storage={0: FACTORY_SENTINEL}
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[Transaction(sender=sender, to=factory)],
            )
        )
        created = size <= fork.fork_at(timestamp=timestamp).max_initcode_size()
        create_address = compute_create_address(
            address=factory,
            nonce=1,
            initcode=initcode_bytes,
            opcode=create_opcode,
        )
        # An oversized initcode aborts the create opcode before any child
        # frame runs, taking the factory frame down with it, so the sentinel
        # survives.
        post[factory] = Account(
            storage={0: create_address if created else FACTORY_SENTINEL}
        )
        post[create_address] = (
            Account(code=b"") if created else Account.NONEXISTENT
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.exception_test
def test_max_code_size_with_max_initcode_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """Ensure max code + max initcode activates at the fork boundary."""
    deploy_code = Op.JUMPDEST * fork.transitions_to().max_code_size()
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_length=fork.transitions_to().max_initcode_size(),
    )

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    create_address_post = compute_create_address(address=bob, nonce=0)

    initcode_too_large = TransactionException.INITCODE_SIZE_EXCEEDED

    blocks = [
        Block(
            timestamp=PRE_FORK_TIMESTAMP,
            txs=[
                Transaction(
                    sender=alice,
                    to=None,
                    data=initcode,
                    error=initcode_too_large,
                )
            ],
            exception=initcode_too_large,
        ),
        Block(
            timestamp=POST_FORK_TIMESTAMP,
            txs=[
                Transaction(
                    sender=bob,
                    to=None,
                    data=initcode,
                )
            ],
        ),
    ]

    post: dict[Any, Account | None] = {
        create_address_post: Account(code=deploy_code),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_max_code_size_with_max_initcode_via_create_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    create_opcode: Op,
) -> None:
    """
    Ensure both new limits activate together at the fork boundary through
    the create opcodes.
    """
    max_code_size = fork.transitions_to().max_code_size()
    max_initcode_size = fork.transitions_to().max_initcode_size()
    initcode_prologue = bytes(Op.RETURN(offset=0, size=max_code_size))
    initcode_bytes = initcode_prologue.ljust(max_initcode_size, b"\x00")

    create_call = (
        create_opcode(value=0, offset=0, size=max_initcode_size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=max_initcode_size)
    )
    factory_code = (
        Om.MSTORE(initcode_prologue, 0) + Op.SSTORE(0, create_call) + Op.STOP
    )

    blocks = []
    post: dict[Any, Account | None] = {}
    for timestamp in (PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP):
        sender = pre.fund_eoa()
        factory = pre.deploy_contract(
            factory_code, storage={0: FACTORY_SENTINEL}
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[Transaction(sender=sender, to=factory)],
            )
        )
        # The initcode limit binds first: pre-fork the create opcode aborts
        # the factory frame before the returned code size is ever checked.
        created = (
            max_initcode_size
            <= fork.fork_at(timestamp=timestamp).max_initcode_size()
        )
        create_address = compute_create_address(
            address=factory,
            nonce=1,
            initcode=initcode_bytes,
            opcode=create_opcode,
        )
        post[factory] = Account(
            storage={0: create_address if created else FACTORY_SENTINEL}
        )
        post[create_address] = (
            Account(code=b"\x00" * max_code_size)
            if created
            else Account.NONEXISTENT
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)
