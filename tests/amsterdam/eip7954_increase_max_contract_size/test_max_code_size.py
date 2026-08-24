"""
Test [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).
"""

from typing import Any, Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
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


def max_deposit_env(fork: Fork) -> Environment:
    """
    Return a block environment able to fund a max-size code deposit at
    the fork's cost per state byte.
    """
    deposit_state_gas = Op.RETURN(
        0,
        fork.max_code_size(),
        code_deposit_size=fork.max_code_size(),
    ).state_cost(fork)
    return Environment(
        gas_limit=max(Environment().gas_limit, 2 * deposit_state_gas)
    )


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
    )

    post: dict[Any, Account | None] = {}
    if code_size <= fork.max_code_size():
        post[create_address] = Account(code=deploy_code)
    else:
        post[create_address] = Account.NONEXISTENT

    state_test(env=max_deposit_env(fork), pre=pre, tx=tx, post=post)


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
    )

    created = code_size <= fork.max_code_size()
    post: dict[Any, Account | None] = {
        factory: Account(storage={0: create_address if created else 0}),
    }
    if created:
        post[create_address] = Account(code=deploy_code)
    else:
        post[create_address] = Account.NONEXISTENT

    state_test(env=max_deposit_env(fork), pre=pre, tx=tx, post=post)


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
    # Under EIP-2780 the created account's NEW_ACCOUNT state gas is
    # charged at the top frame, no longer bundled in the intrinsic, so
    # add it back into the exact-fit gas limit.
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=(
            intrinsic_gas
            + top_frame_state_gas
            + initcode.evm_gas(fork)
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

    state_test(env=max_deposit_env(fork), pre=pre, tx=tx, post=post)


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
    )

    post = {create_address: Account(code=deploy_code)}

    state_test(env=max_deposit_env(fork), pre=pre, tx=tx, post=post)


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


@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(Op.CREATE2, id="CREATE2"),
    ],
)
def test_warm_after_failed_create_over_max_code_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify the would-be contract address is warm after a CREATE that fails
    because the returned deploy code exceeds max_code_size.

    Unlike pre-validation aborts (insufficient balance, nonce overflow), the
    address is added to the access list during initcode execution, so the
    post-RETURN size check rejecting deployment must leave the address warm.
    """
    initcode = Op.RETURN(offset=0, size=fork.max_code_size() + 1)
    initcode_bytes = bytes(initcode)
    if create_opcode == Op.CREATE2:
        salt = CREATE2_SALT
        create_call = create_opcode(
            value=0,
            offset=0,
            size=len(initcode_bytes),
            salt=salt,
        )
    else:
        salt = 0
        create_call = create_opcode(
            value=0, offset=0, size=len(initcode_bytes)
        )

    creator_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.ljust(32, b"\0"))
    ) + Op.SSTORE(0, create_call)

    creator_address = pre.deploy_contract(creator_code, storage={0: 1})

    contract_address = compute_create_address(
        address=creator_address,
        nonce=1,
        salt=salt,
        initcode=initcode_bytes,
        opcode=create_opcode,
    )

    warm_balance = Op.BALANCE(contract_address, address_warm=True)
    checker_address = pre.deploy_contract(
        CodeGasMeasure(
            code=warm_balance,
            extra_stack_items=1,
            sstore_key=1,
        )
    )

    entry_address = pre.deploy_contract(
        Op.CALL(gas=Op.GAS, address=creator_address)
        + Op.CALL(gas=Op.GAS, address=checker_address)
        + Op.STOP
    )

    tx = Transaction(
        to=entry_address,
        gas_limit=fork.transaction_gas_limit_cap(),
        sender=pre.fund_eoa(),
    )

    post = {
        creator_address: Account(storage={0: 0}),
        checker_address: Account(storage={1: warm_balance.gas_cost(fork)}),
        contract_address: Account.NONEXISTENT,
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "valid_jumpdest",
    [
        pytest.param(True, id="valid_high_jumpdest"),
        pytest.param(False, id="invalid_high_dest"),
    ],
)
def test_max_code_size_high_jumpdest(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    valid_jumpdest: bool,
) -> None:
    """
    Ensure jump destination validity is enforced past the old size limits.

    Deploy a `MAX_CODE_SIZE` contract that stores a sentinel and then jumps
    near the new limit, far beyond the old 24 KiB code and 48 KiB initcode
    limits, then call it through a caller that records the call's success:

    - ``valid_high_jumpdest``: the target byte is a real ``JUMPDEST``, so the
      jump succeeds, the frame returns, and the sentinel store is kept.
    - ``invalid_high_dest``: the target byte is a ``STOP`` (not a
      ``JUMPDEST``), so the jump is rejected, the frame reverts, and the
      sentinel store is discarded.

    A client whose jumpdest analysis or code execution does not cover the
    full new code range fails one of the two cases. No existing test
    executes a contract at a program counter beyond the old limit.
    """
    if valid_jumpdest:
        tail = Op.JUMPDEST
    else:
        # A bare STOP, not a JUMPDEST: jumping here is invalid. A client that
        # wrongly accepts it halts normally and keeps the prefix store (1).
        tail = Op.STOP

    dest = fork.max_code_size() - len(tail)
    push_size = (dest.bit_length() + 7) // 8
    push_op = getattr(Op, f"PUSH{push_size}")
    prefix = Op.SSTORE(0, 1) + push_op(dest) + Op.JUMP
    target_code = prefix + Op.INVALID * (dest - len(prefix)) + tail
    assert len(target_code) == fork.max_code_size()

    target = pre.deploy_contract(target_code)
    caller = pre.deploy_contract(
        Op.SSTORE(0, Op.CALL(gas=Op.GAS, address=target)) + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    # Valid: jump completes, call succeeds (1), and the store is kept.
    # Invalid: jump reverts, call fails (0), and nothing is stored.
    stored = 1 if valid_jumpdest else 0
    post = {
        caller: Account(storage={0: stored}),
        target: Account(storage={0: stored}),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "tail,accepted",
    [
        pytest.param(Op.PUSH1(0x5B), False, id="push1_data_rejected"),
        pytest.param(Op.DUPN[b"\x5b"], True, id="dupn_immediate_accepted"),
        pytest.param(Op.SWAPN[b"\x5b"], True, id="swapn_immediate_accepted"),
        pytest.param(
            Op.EXCHANGE[b"\x5b"], True, id="exchange_immediate_accepted"
        ),
    ],
)
def test_max_code_size_jumpdest_in_immediate(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tail: Bytecode,
    accepted: bool,
) -> None:
    """
    Ensure jumpdest analysis classifies a `0x5B` immediate byte correctly at
    the new max code size.

    A `0x5B` sits as the last byte of a `MAX_CODE_SIZE` contract, right after
    an immediate-carrying opcode, and the contract jumps to it:

    - ``push1_data_rejected``: the `0x5B` is `PUSH` data, always skipped by
      the analysis, so it is not a `JUMPDEST` and the jump is rejected.
    - ``dupn``/``swapn``/``exchange``: per EIP-8024 `0x5B` is an *invalid*
      immediate for these opcodes, so it is not skipped and stays a valid
      `JUMPDEST`, and the jump is accepted.

    Exercises the immediate-skipping branches of jumpdest analysis well past
    the old 24 KiB code and 48 KiB initcode limits.
    """
    jump_target = fork.max_code_size() - 1  # the 0x5B is the last byte
    push_size = (jump_target.bit_length() + 7) // 8
    push_op = getattr(Op, f"PUSH{push_size}")
    prefix = Op.SSTORE(0, 1) + push_op(jump_target) + Op.JUMP
    filler_len = fork.max_code_size() - len(prefix) - len(tail)
    target_code = prefix + Op.INVALID * filler_len + tail
    assert len(target_code) == fork.max_code_size()
    assert bytes(target_code)[jump_target] == 0x5B

    target = pre.deploy_contract(target_code)
    caller = pre.deploy_contract(
        Op.SSTORE(0, Op.CALL(gas=Op.GAS, address=target)) + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    # Accepted: jump completes, the call succeeds (1), the store is kept.
    # Rejected: jump reverts, the call fails (0), nothing is stored.
    stored = 1 if accepted else 0
    post = {
        caller: Account(storage={0: stored}),
        target: Account(storage={0: stored}),
    }

    state_test(pre=pre, tx=tx, post=post)
