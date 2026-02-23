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
    ceiling_division,
    compute_create2_address,
    compute_create_address,
    keccak256,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_from("Amsterdam")

CREATE2_SALT = 0xC0FFEE

DEPLOY_CODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.max_code_size(), id="at_max"),
    pytest.param(lambda f: f.max_code_size() + 1, id="over_max"),
]


@pytest.mark.parametrize("deploy_code_size", DEPLOY_CODE_SIZE_PARAMS)
def test_deploy_size(
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
def test_create_opcode_deploy_size(
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

    create_address = (
        compute_create2_address(
            address=factory, salt=CREATE2_SALT, initcode=initcode
        )
        if create_opcode == Op.CREATE2
        else compute_create_address(address=factory, nonce=1)
    )

    tx = Transaction(
        sender=alice,
        to=factory,
        data=initcode_bytes,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post: dict[Any, Account | None] = {}
    if code_size <= fork.max_code_size():
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
def test_deploy_gas_usage(
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

    # Use return_cost_deducted_prior_execution to get the actual gas consumed
    # before EVM execution (excludes EIP-7623 floor data cost which would
    # inflate the gas limit without being consumed).
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )

    # Calculate initcode execution gas precisely.
    # The Initcode class overestimates memory costs (uses byte count instead
    # of word count), so we compute it here.
    gas_costs = fork.gas_costs()
    code_words = ceiling_division(len(bytes(deploy_code)), 32)
    initcode_execution_gas = (
        3 * 5  # PUSH2 + PUSH1 + DUP2 + PUSH1 + DUP3
        + gas_costs.G_VERY_LOW  # CODECOPY base
        + gas_costs.G_COPY * code_words  # CODECOPY copy cost
        + fork.memory_expansion_gas_calculator()(
            new_bytes=len(bytes(deploy_code))
        )
    )

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=(
            intrinsic_gas
            + initcode_execution_gas
            + initcode.deployment_gas
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


@pytest.mark.parametrize(
    "operation, expected, delegate",
    [
        pytest.param(
            lambda addr: Op.SSTORE(0, Op.EXTCODESIZE(addr)),
            lambda code: len(code),
            False,
            id="EXTCODESIZE",
        ),
        pytest.param(
            lambda addr: Op.SSTORE(0, Op.EXTCODEHASH(addr)),
            lambda code: keccak256(code),
            False,
            id="EXTCODEHASH",
        ),
        pytest.param(
            lambda addr: (
                Op.EXTCODECOPY(addr, 0, 0, Op.EXTCODESIZE(addr))
                + Op.SSTORE(0, Op.SHA3(0, Op.EXTCODESIZE(addr)))
            ),
            lambda code: keccak256(code),
            False,
            id="EXTCODECOPY",
        ),
        pytest.param(
            lambda _: Op.SSTORE(0, Op.CODESIZE),
            lambda code: len(code),
            True,
            id="CODESIZE",
        ),
        pytest.param(
            lambda _: (
                Op.CODECOPY(0, 0, Op.CODESIZE)
                + Op.SSTORE(0, Op.SHA3(0, Op.CODESIZE))
            ),
            lambda code: keccak256(code),
            True,
            id="CODECOPY",
        ),
    ],
)
def test_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    operation: Callable[..., Any],
    expected: Callable[..., Any],
    delegate: bool,
) -> None:
    """
    Ensure EVM opcodes work with the new max contract size.

    Self opcodes (CODESIZE, CODECOPY) are tested via DELEGATECALL
    into a max-size contract containing the checker logic, so the
    opcodes operate on the large contract's own code while writing
    results to the caller's storage.
    """
    alice = pre.fund_eoa()

    if delegate:
        logic = operation(None) + Op.STOP
        target_code = logic + Op.JUMPDEST * (fork.max_code_size() - len(logic))
        target = pre.deploy_contract(code=target_code)
        oracle = pre.deploy_contract(
            code=Op.DELEGATECALL(gas=Op.GAS, address=target)
        )
    else:
        target_code = Op.JUMPDEST * fork.max_code_size()
        target = pre.deploy_contract(code=target_code)
        oracle = pre.deploy_contract(code=operation(target))

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {oracle: Account(storage={0: expected(target_code)})}

    state_test(pre=pre, tx=tx, post=post)
