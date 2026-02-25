"""
Test [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).

Tests for the increased maximum initcode size (64 KiB).
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
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_from("Amsterdam")

CREATE2_SALT = 0xC0FFEE

INITCODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.max_initcode_size(), id="at_max"),
    pytest.param(lambda f: f.max_initcode_size() + 1, id="over_max"),
]

TX_INITCODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.max_initcode_size(), id="at_max"),
    pytest.param(
        lambda f: f.max_initcode_size() + 1,
        id="over_max",
        marks=pytest.mark.exception_test,
    ),
]


@pytest.mark.parametrize("initcode_size", TX_INITCODE_SIZE_PARAMS)
def test_max_initcode_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size: Callable[[Fork], int],
) -> None:
    """Ensure the new max initcode size is enforced for transactions."""
    size = initcode_size(fork)
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=size,
    )

    alice = pre.fund_eoa()
    create_address = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post: dict[Any, Account | None] = {}
    if size <= fork.max_initcode_size():
        post[create_address] = Account(code=Op.STOP)
    else:
        tx.error = TransactionException.INITCODE_SIZE_EXCEEDED
        post[create_address] = Account.NONEXISTENT

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("initcode_size", INITCODE_SIZE_PARAMS)
@pytest.mark.with_all_create_opcodes()
def test_max_initcode_size_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size: Callable[[Fork], int],
    create_opcode: Op,
) -> None:
    """Ensure the new max initcode size is enforced via create opcodes."""
    size = initcode_size(fork)
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=size,
    )
    initcode_bytes = bytes(initcode)

    alice = pre.fund_eoa()

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

    factory = pre.deploy_contract(factory_code)

    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=CREATE2_SALT,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=alice,
        to=factory,
        data=initcode_bytes,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # Opcode-level: oversized initcode causes OutOfGasError
    # (tx succeeds, CREATE returns 0)
    created = size <= fork.max_initcode_size()
    post: dict[Any, Account | None] = {
        factory: Account(storage={0: create_address if created else 0}),
    }
    if created:
        post[create_address] = Account(code=Op.STOP)
    else:
        post[create_address] = Account.NONEXISTENT

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "gas_shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(
            1,
            id="short_one_gas",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_max_initcode_size_gas_metering(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
) -> None:
    """Verify initcode gas metering at the new max initcode size."""
    initcode = Initcode(
        deploy_code=Op.STOP, initcode_length=fork.max_initcode_size()
    )
    alice = pre.fund_eoa()

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode, contract_creation=True
    )

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=intrinsic_gas - gas_shortfall,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW
        if gas_shortfall
        else None,
    )

    post = {
        compute_create_address(address=alice, nonce=0): Account.NONEXISTENT
        if gas_shortfall
        else Account(code=Op.STOP),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "gas_shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(1, id="short_one_gas"),
    ],
)
@pytest.mark.with_all_create_opcodes()
def test_max_initcode_size_gas_metering_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
    create_opcode: Op,
) -> None:
    """Verify gas metering via create opcodes for the new initcode size."""
    initcode = Initcode(
        deploy_code=Op.STOP, initcode_length=fork.max_initcode_size()
    )
    alice = pre.fund_eoa()

    initcode_len = len(initcode)
    create_call = (
        create_opcode(
            value=0,
            offset=0,
            size=Op.CALLDATASIZE,
            salt=CREATE2_SALT,
            init_code_size=initcode_len,
        )
        if create_opcode == Op.CREATE2
        else create_opcode(
            value=0,
            offset=0,
            size=Op.CALLDATASIZE,
            init_code_size=initcode_len,
        )
    )

    # Factory stores CREATE return value in slot 0
    factory_code = (
        Op.CALLDATACOPY(
            0,
            0,
            Op.CALLDATASIZE,
            data_size=initcode_len,
            new_memory_size=initcode_len,
        )
        + Op.SSTORE(0, create_call)
        + Op.STOP
    )

    factory = pre.deploy_contract(factory_code)

    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=CREATE2_SALT,
        initcode=initcode,
        opcode=create_opcode,
    )

    # Compute exact gas the factory needs
    factory_gas = (
        factory_code.gas_cost(fork)
        + initcode.execution_gas(fork)
        + initcode.deployment_gas(fork)
    )

    # Caller CALLs factory with explicit gas to bypass EIP-7623 floor data
    # cost and the 63/64 rule (EIP-150).
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.CALL(
            gas=factory_gas - gas_shortfall,
            address=factory,
            value=0,
            args_offset=0,
            args_size=Op.CALLDATASIZE,
            ret_offset=0,
            ret_size=0,
        )
        + Op.STOP
    )

    tx = Transaction(
        sender=alice,
        to=caller,
        data=bytes(initcode),
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # With shortfall, factory OOGs and all state reverts
    created = not gas_shortfall
    post = {
        create_address: Account(code=Op.STOP)
        if created
        else Account.NONEXISTENT,
        factory: Account(storage={0: create_address if created else 0}),
    }

    state_test(pre=pre, tx=tx, post=post)
