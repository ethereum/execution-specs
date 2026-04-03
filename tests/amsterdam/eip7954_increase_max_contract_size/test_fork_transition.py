"""
Fork transition tests for
[EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).

Tests that the new max code size and initcode size limits activate
exactly at the Amsterdam fork boundary (timestamp 15,000).
"""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Initcode,
    Op,
    Transaction,
    TransactionException,
    TransitionFork,
    compute_create_address,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_at_transition_to("Amsterdam")

CREATE2_SALT = 0xC0FFEE


def test_max_code_size_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """Ensure the new max code size limit activates at the fork boundary."""
    code_size = fork.transitions_to().max_code_size()
    deploy_code = Op.JUMPDEST * code_size
    initcode = Initcode(deploy_code=deploy_code)

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    create_address_pre = compute_create_address(address=alice, nonce=0)
    create_address_post = compute_create_address(address=bob, nonce=0)

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    sender=alice,
                    to=None,
                    data=initcode,
                    gas_limit=fork.transitions_from().transaction_gas_limit_cap(),
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    sender=bob,
                    to=None,
                    data=initcode,
                    # TODO: auto gas limit for EIP-8037 state gas
                    gas_limit=100_000_000,
                )
            ],
        ),
    ]

    post: dict[Any, Account | None] = {
        create_address_pre: Account.NONEXISTENT,
        create_address_post: Account(code=deploy_code),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_max_code_size_via_create_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    create_opcode: Op,
) -> None:
    """Ensure the new max code size limit activates at the fork via opcodes."""
    code_size = fork.transitions_to().max_code_size()
    deploy_code = Op.JUMPDEST * code_size
    initcode = Initcode(deploy_code=deploy_code)
    initcode_bytes = bytes(initcode)

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    create_call = (
        create_opcode(
            value=0, offset=0, size=Op.CALLDATASIZE, salt=CREATE2_SALT
        )
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=Op.CALLDATASIZE)
    )

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, create_call)
        + Op.STOP
    )

    factory_pre = pre.deploy_contract(factory_code)
    factory_post = pre.deploy_contract(factory_code)

    create_address_pre = compute_create_address(
        address=factory_pre,
        nonce=1,
        salt=CREATE2_SALT,
        initcode=initcode,
        opcode=create_opcode,
    )
    create_address_post = compute_create_address(
        address=factory_post,
        nonce=1,
        salt=CREATE2_SALT,
        initcode=initcode,
        opcode=create_opcode,
    )

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    sender=alice,
                    to=factory_pre,
                    data=initcode_bytes,
                    gas_limit=fork.transitions_from().transaction_gas_limit_cap(),
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    sender=bob,
                    to=factory_post,
                    data=initcode_bytes,
                    # TODO: auto gas limit for EIP-8037 state gas
                    gas_limit=100_000_000,
                )
            ],
        ),
    ]

    post: dict[Any, Account | None] = {
        create_address_pre: Account.NONEXISTENT,
        create_address_post: Account(code=deploy_code),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.exception_test
def test_max_initcode_size_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """Ensure the new max initcode size limit activates exactly at the fork."""
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=fork.transitions_to().max_initcode_size(),
    )

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    create_address_post = compute_create_address(address=bob, nonce=0)

    initcode_too_large = TransactionException.INITCODE_SIZE_EXCEEDED

    blocks = [
        # Pre-fork: initcode at the new max exceeds the parent fork's limit,
        # so the tx is rejected and the block is invalid.
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    sender=alice,
                    to=None,
                    data=initcode,
                    gas_limit=fork.transitions_from().transaction_gas_limit_cap(),
                    error=initcode_too_large,
                )
            ],
            exception=initcode_too_large,
        ),
        # Post-fork: the new limit is in effect, tx succeeds.
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    sender=bob,
                    to=None,
                    data=initcode,
                    gas_limit=fork.transitions_to().transaction_gas_limit_cap(),
                )
            ],
        ),
    ]

    post: dict[Any, Account | None] = {
        create_address_post: Account(code=Op.STOP),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_max_initcode_size_via_create_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    create_opcode: Op,
) -> None:
    """Ensure the new max initcode size limit activates at fork via opcodes."""
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=fork.transitions_to().max_initcode_size(),
    )
    initcode_bytes = bytes(initcode)

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    create_call = (
        create_opcode(
            value=0, offset=0, size=Op.CALLDATASIZE, salt=CREATE2_SALT
        )
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=Op.CALLDATASIZE)
    )

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, create_call)
        + Op.STOP
    )

    factory_pre = pre.deploy_contract(factory_code)
    factory_post = pre.deploy_contract(factory_code)

    create_address_pre = compute_create_address(
        address=factory_pre,
        nonce=1,
        salt=CREATE2_SALT,
        initcode=initcode,
        opcode=create_opcode,
    )
    create_address_post = compute_create_address(
        address=factory_post,
        nonce=1,
        salt=CREATE2_SALT,
        initcode=initcode,
        opcode=create_opcode,
    )

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    sender=alice,
                    to=factory_pre,
                    data=initcode_bytes,
                    gas_limit=fork.transitions_from().transaction_gas_limit_cap(),
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    sender=bob,
                    to=factory_post,
                    data=initcode_bytes,
                    gas_limit=fork.transitions_to().transaction_gas_limit_cap(),
                )
            ],
        ),
    ]

    # Pre-fork: CREATE returns 0 (initcode exceeds parent fork limit)
    # Post-fork: CREATE succeeds
    post: dict[Any, Account | None] = {
        factory_pre: Account(storage={0: 0}),
        create_address_pre: Account.NONEXISTENT,
        factory_post: Account(storage={0: create_address_post}),
        create_address_post: Account(code=Op.STOP),
    }

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
            timestamp=14_999,
            txs=[
                Transaction(
                    sender=alice,
                    to=None,
                    data=initcode,
                    gas_limit=fork.transitions_from().transaction_gas_limit_cap(),
                    error=initcode_too_large,
                )
            ],
            exception=initcode_too_large,
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    sender=bob,
                    to=None,
                    data=initcode,
                    # TODO: auto gas limit for EIP-8037 state gas
                    gas_limit=100_000_000,
                )
            ],
        ),
    ]

    post: dict[Any, Account | None] = {
        create_address_post: Account(code=deploy_code),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_parent_max_code_size_across_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """Ensure previous max code size works after transition."""
    parent = fork.transitions_from()
    assert parent is not None, "Parent fork must be defined for this test"

    code_size = parent.max_code_size()
    deploy_code = Op.JUMPDEST * code_size
    initcode = Initcode(deploy_code=deploy_code)

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    create_address_pre = compute_create_address(address=alice, nonce=0)
    create_address_post = compute_create_address(address=bob, nonce=0)

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    sender=alice,
                    to=None,
                    data=initcode,
                    gas_limit=fork.transitions_from().transaction_gas_limit_cap(),
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    sender=bob,
                    to=None,
                    data=initcode,
                    # TODO: auto gas limit for EIP-8037 state gas
                    gas_limit=100_000_000,
                )
            ],
        ),
    ]

    post: dict[Any, Account | None] = {
        create_address_pre: Account(code=deploy_code),
        create_address_post: Account(code=deploy_code),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
