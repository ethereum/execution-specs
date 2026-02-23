"""
Mainnet tests for
[EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).
"""

from typing import Any, Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
    keccak256,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = [pytest.mark.valid_at("Amsterdam"), pytest.mark.mainnet]


def test_deploy_max_code_size_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify end-to-end deployment of a max-size contract on mainnet."""
    deploy_code = Op.JUMPDEST * fork.max_code_size()
    initcode = Initcode(deploy_code=deploy_code)

    sender = pre.fund_eoa()
    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {create_address: Account(code=deploy_code)}

    state_test(pre=pre, tx=tx, post=post)


def test_deploy_over_max_code_size_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify deployment above the new limit is rejected on mainnet."""
    deploy_code = Op.JUMPDEST * (fork.max_code_size() + 1)
    initcode = Initcode(deploy_code=deploy_code)

    sender = pre.fund_eoa()
    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post: dict[Any, Account | None] = {
        create_address: Account.NONEXISTENT,
    }

    state_test(pre=pre, tx=tx, post=post)


def test_max_initcode_tx_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify a CREATE transaction with max-size initcode succeeds."""
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=fork.max_initcode_size(),
    )

    sender = pre.fund_eoa()
    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {create_address: Account(code=Op.STOP)}

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.exception_test
def test_over_max_initcode_tx_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify a CREATE transaction over the new initcode limit is rejected."""
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=fork.max_initcode_size() + 1,
    )

    sender = pre.fund_eoa()
    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
        error=TransactionException.INITCODE_SIZE_EXCEEDED,
    )

    post: dict[Any, Account | None] = {
        create_address: Account.NONEXISTENT,
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "operation, expected",
    [
        pytest.param(
            lambda addr: Op.SSTORE(0, Op.EXTCODESIZE(addr)),
            lambda code: len(code),
            id="EXTCODESIZE",
        ),
        pytest.param(
            lambda addr: Op.SSTORE(0, Op.EXTCODEHASH(addr)),
            lambda code: keccak256(code),
            id="EXTCODEHASH",
        ),
        pytest.param(
            lambda addr: (
                Op.EXTCODECOPY(addr, 0, 0, Op.EXTCODESIZE(addr))
                + Op.SSTORE(0, Op.SHA3(0, Op.EXTCODESIZE(addr)))
            ),
            lambda code: keccak256(code),
            id="EXTCODECOPY",
        ),
    ],
)
def test_opcodes_on_max_size_contract_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    operation: Callable[..., Any],
    expected: Callable[..., Any],
) -> None:
    """Verify EVM opcodes works for a max-size deployed contract."""
    target_code = Op.JUMPDEST * fork.max_code_size()
    target = pre.deploy_contract(code=target_code)

    sender = pre.fund_eoa()
    oracle = pre.deploy_contract(code=operation(target))

    tx = Transaction(
        sender=sender,
        to=oracle,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {oracle: Account(storage={0: expected(target_code)})}

    state_test(pre=pre, tx=tx, post=post)
