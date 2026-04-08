"""
Test [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).
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
    compute_create_address,
    keccak256,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_from("EIP7954")

CREATE2_SALT = 0xC0FFEE

DEPLOY_CODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.max_code_size(), id="at_max"),
    pytest.param(lambda f: f.max_code_size() + 1, id="over_max"),
]


@pytest.mark.parametrize("deploy_code_size", DEPLOY_CODE_SIZE_PARAMS)
def test_max_code_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    deploy_code_size: Callable[[Fork], int],
) -> None:
    """Ensure the new max code size boundary is enforced."""
    code_size = deploy_code_size(fork)
    deploy_code = Op.JUMPDEST * code_size

    alice = pre.fund_eoa()
    initcode = Initcode(deploy_code=deploy_code)
    create_address = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post: dict[Any, Account | None] = {}
    if code_size <= fork.max_code_size():
        post[create_address] = Account(code=deploy_code)
    else:
        post[create_address] = Account.NONEXISTENT

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("deploy_code_size", DEPLOY_CODE_SIZE_PARAMS)
@pytest.mark.with_all_create_opcodes()
def test_max_code_size_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    deploy_code_size: Callable[[Fork], int],
    create_opcode: Op,
) -> None:
    """Ensure the new max code size boundary is enforced via create opcodes."""
    code_size = deploy_code_size(fork)
    deploy_code = Op.JUMPDEST * code_size
    initcode = Initcode(deploy_code=deploy_code)
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

    created = code_size <= fork.max_code_size()
    post: dict[Any, Account | None] = {
        factory: Account(storage={0: create_address if created else 0}),
    }
    if created:
        post[create_address] = Account(code=deploy_code)
    else:
        post[create_address] = Account.NONEXISTENT

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "gas_shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(1, id="short_one_gas"),
    ],
)
def test_max_code_size_deposit_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
) -> None:
    """Ensure code deposit gas is charged correctly at the new max."""
    deploy_code = Op.JUMPDEST * fork.max_code_size()
    initcode = Initcode(deploy_code=deploy_code)

    alice = pre.fund_eoa()
    create_address = compute_create_address(address=alice, nonce=0)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=(
            intrinsic_gas
            + initcode.execution_gas(fork)
            + initcode.deployment_gas(fork)
            - gas_shortfall
        ),
    )
    # With shortfall, code deposit OOGs: tx succeeds but
    # contract is not deployed
    post = {
        create_address: Account(code=deploy_code)
        if not gas_shortfall
        else Account.NONEXISTENT,
    }

    state_test(pre=pre, tx=tx, post=post)


def test_max_code_size_with_max_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Ensure max-size code deploys when initcode is also at max size."""
    deploy_code = Op.JUMPDEST * fork.max_code_size()
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_length=fork.max_initcode_size(),
    )

    alice = pre.fund_eoa()
    create_address = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {create_address: Account(code=deploy_code)}

    state_test(pre=pre, tx=tx, post=post)


def test_max_code_size_external_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    max_code_size_contract: tuple,
) -> None:
    """Ensure external code opcodes work with the new max contract size."""
    target, target_code = max_code_size_contract

    alice = pre.fund_eoa()

    tx = Transaction(
        sender=alice,
        to=target,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {
        target: Account(
            storage={
                0: len(target_code),
                1: keccak256(bytes(target_code)),
                2: keccak256(bytes(target_code)),
            }
        )
    }

    state_test(pre=pre, tx=tx, post=post)


def test_max_code_size_self_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Ensure self code opcodes work with the new max contract size.

    Tested via DELEGATECALL so opcodes operate on the large
    contract's own code while writing results to the caller's
    storage.
    """
    logic = (
        Op.SSTORE(0, Op.CODESIZE)
        + Op.CODECOPY(0, 0, Op.CODESIZE)
        + Op.SSTORE(1, Op.SHA3(0, Op.CODESIZE))
        + Op.STOP
    )
    target_code = logic + Op.JUMPDEST * (fork.max_code_size() - len(logic))
    target = pre.deterministic_deploy_contract(deploy_code=target_code)

    alice = pre.fund_eoa()
    oracle = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=Op.GAS, address=target)
    )

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {
        oracle: Account(
            storage={
                0: len(target_code),
                1: keccak256(bytes(target_code)),
            }
        )
    }

    state_test(pre=pre, tx=tx, post=post)
