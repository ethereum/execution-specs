"""
Test [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).

Tests for the increased maximum initcode size (64 KiB).
"""

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
    compute_create2_address,
    compute_create_address,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_from("Amsterdam")

CREATE2_SALT = 0xC0FFEE

INITCODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.parent().max_initcode_size(), id="prev_max"),
    pytest.param(lambda f: f.max_initcode_size(), id="at_max"),
    pytest.param(lambda f: f.max_initcode_size() + 1, id="over_max"),
]

TX_INITCODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.parent().max_initcode_size(), id="prev_max"),
    pytest.param(lambda f: f.max_initcode_size(), id="at_max"),
    pytest.param(
        lambda f: f.max_initcode_size() + 1,
        id="over_max",
        marks=pytest.mark.exception_test,
    ),
]


@pytest.mark.parametrize("initcode_size", TX_INITCODE_SIZE_PARAMS)
def test_initcode_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size,
) -> None:
    """Ensure the new max initcode size is enforced for transactions."""
    size = initcode_size(fork)
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=size,
    )

    sender = pre.fund_eoa()
    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    if size <= fork.max_initcode_size():
        post = {create_address: Account(code=Op.STOP)}
    else:
        tx.error = TransactionException.INITCODE_SIZE_EXCEEDED
        post = {create_address: Account.NONEXISTENT}

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("initcode_size", INITCODE_SIZE_PARAMS)
@pytest.mark.with_all_create_opcodes()
def test_create_opcode_initcode_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size,
    create_opcode,
) -> None:
    """Ensure the new max initcode size is enforced via create opcodes."""
    size = initcode_size(fork)
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=size,
    )
    initcode_bytes = bytes(initcode)

    sender = pre.fund_eoa()

    extra_create_kwargs = (
        {"salt": CREATE2_SALT} if create_opcode == Op.CREATE2 else {}
    )

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            0,
            create_opcode(
                value=0, offset=0, size=Op.CALLDATASIZE, **extra_create_kwargs
            ),
        )
        + Op.STOP
    )

    factory = pre.deploy_contract(factory_code)

    create_address = (
        compute_create2_address(
            address=factory, salt=CREATE2_SALT, initcode=initcode
        )
        if create_opcode == Op.CREATE2
        else compute_create_address(address=factory, nonce=1)
    )

    tx = Transaction(
        sender=sender,
        to=factory,
        data=initcode_bytes,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # Opcode-level: oversized initcode causes OutOfGasError
    # (tx succeeds, CREATE returns 0)
    created = size <= fork.max_initcode_size()
    post = {
        create_address: Account(code=Op.STOP)
        if created
        else Account.NONEXISTENT,
        factory: Account(storage={0: create_address if created else 0}),
    }

    state_test(pre=pre, tx=tx, post=post)
