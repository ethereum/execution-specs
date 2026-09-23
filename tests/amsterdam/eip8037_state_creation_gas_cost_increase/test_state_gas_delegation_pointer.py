"""
Test state gas behavior when calling via 7702 delegation pointer vs direct.

Under EIP-8037, calling a contract that has a 7702 delegation pointer
should charge the same state gas as calling the target directly. The
delegation resolution is transparent to gas accounting.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Fork,
    Header,
    Op,
    RecipientType,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
def test_sstore_via_delegation_pointer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas charged when called via delegation pointer.

    A contract performs an SSTORE. An EOA delegates to that contract
    via EIP-7702. Calling the EOA (delegation pointer) executes the
    contract code in the EOA's context. The SSTORE state gas should
    be charged from the reservoir just as it would for a direct call.
    """
    storage = Storage()
    contract_code = Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=contract_code)

    # EOA with pre-existing delegation to the contract
    delegator = pre.fund_eoa(delegation=contract)

    # The authorization re-targets an already-delegated authority whose
    # nonce (1, from the delegation setup) no longer matches nonce=0, so
    # it is invalid and charges no top-frame state gas.
    authorization = AuthorizationTuple(
        address=contract,
        nonce=0,
        signer=delegator,
        creates_account=False,
        writes_delegation=False,
        first_write=False,
    )
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=[authorization],
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=False,
        authorizations=[authorization],
    )
    auth_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        authorizations=[authorization],
    )
    assert auth_state_gas == 0

    block_execution = (
        intrinsic_execution
        + top_frame_execution
        + contract_code.execution_cost(fork)
    )
    block_state = auth_state_gas + contract_code.state_cost(fork)
    assert block_state > block_execution

    sender = pre.fund_eoa()
    tx = Transaction(
        to=delegator,
        state_gas_reservoir=block_state,
        authorization_list=[authorization],
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=block_execution + block_state,
        ),
    )

    # SSTORE writes to the delegator's storage context
    post = {delegator: Account(storage=storage)}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(block_execution, block_state)
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_direct_call_same_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas charged when calling the contract directly.

    Baseline comparison: calling the contract directly (not via a
    delegation pointer) charges SSTORE state gas identically.
    """
    storage = Storage()
    contract_code = Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=contract_code)

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.CONTRACT,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
    )
    assert top_frame_state == 0

    block_execution = (
        intrinsic_execution
        + top_frame_execution
        + contract_code.execution_cost(fork)
    )
    block_state = top_frame_state + contract_code.state_cost(fork)
    assert block_state > block_execution

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        state_gas_reservoir=block_state,
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=block_execution + block_state,
        ),
    )

    post = {contract: Account(storage=storage)}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(block_execution, block_state)
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_delegation_pointer_new_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test delegation pointer CALL to empty account charges new-account gas.

    A contract CALLs with value to a non-existent address. When executed
    via a delegation pointer, the new-account state gas
    is charged identically to a direct call.
    """
    target = pre.nonexistent_account()

    parent_storage = Storage()

    call = Op.CALL(
        gas=0,
        address=target,
        value=1,
        value_transfer=True,
        account_new=True,
    )
    contract_code = Op.SSTORE(parent_storage.store_next(1), call)
    contract = pre.deploy_contract(code=contract_code, balance=1)

    # EOA delegates to the contract
    delegator = pre.fund_eoa(delegation=contract, amount=1)

    # The authorization re-targets an already-delegated authority whose
    # nonce (1, from the delegation setup) no longer matches nonce=0, so
    # it is invalid and charges no top-frame state gas.
    authorization = AuthorizationTuple(
        address=contract,
        nonce=0,
        signer=delegator,
        creates_account=False,
        writes_delegation=False,
        first_write=False,
    )
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=[authorization],
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=False,
        authorizations=[authorization],
    )
    auth_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        authorizations=[authorization],
    )
    assert auth_state_gas == 0

    # The callee leaves the value-transfer stipend unused, so it returns
    # to this frame instead of being spent.
    block_execution = (
        intrinsic_execution
        + top_frame_execution
        + contract_code.execution_cost(fork)
        - fork.gas_costs().CALL_STIPEND
    )
    block_state = auth_state_gas + contract_code.state_cost(fork)
    assert block_state > block_execution

    sender = pre.fund_eoa()
    tx = Transaction(
        to=delegator,
        state_gas_reservoir=block_state,
        authorization_list=[authorization],
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=block_execution + block_state,
        ),
    )

    # CALL success stored in delegator's storage context
    post = {
        delegator: Account(storage=parent_storage, balance=0),
        target: Account(balance=1),
    }

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(block_execution, block_state)
        ),
    )


@pytest.mark.parametrize(
    "state_op",
    [Op.CREATE, Op.CREATE2, Op.SELFDESTRUCT],
)
@pytest.mark.valid_from("EIP8037")
def test_account_state_gas_via_delegation_pointer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_op: Op,
) -> None:
    """
    Test account-creating charges are billed the same via a delegation
    pointer as they are directly.

    Delegated code runs in the authority's context, so a CREATE takes the
    authority's nonce and a SELFDESTRUCT moves the authority's balance.
    Each still bills its state charge from the reservoir, and the header
    reports it in the state dimension.
    """
    if state_op == Op.CREATE:
        code = Op.POP(Op.CREATE(0, 0, 0))
    elif state_op == Op.CREATE2:
        code = Op.POP(Op.CREATE2(0, 0, 0, 0))
    else:
        code = Op.SELFDESTRUCT(pre.nonexistent_account(), account_new=True)
    contract = pre.deploy_contract(code=code)

    delegator = pre.fund_eoa(delegation=contract, amount=1)
    state_gas = code.state_cost(fork)
    assert state_gas > 0, "the op must carry a state charge"

    tx = Transaction(
        to=delegator,
        state_gas_reservoir=state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_gas),
    )


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_delegation_pointer_state_gas_on_frame_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Test a delegated frame's state charge is undone when it fails.

    The storage the charge pays for belongs to the authority, not the
    delegated code's own account, so the rollback has to reach the
    authority's slot. Either failure leaves the state dimension empty.
    """
    ending = Op.REVERT(0, 0) if failure_mode == "revert" else Op.INVALID
    code = Op.SSTORE(0, 1) + ending
    contract = pre.deploy_contract(code=code)

    delegator = pre.fund_eoa(delegation=contract)

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=False,
    )
    gas_limit = 200_000
    # The rolled-back set leaves the state dimension empty, so the
    # header is the execution total: a halt burns the whole budget, a
    # revert returns everything the frame did not spend.
    if failure_mode == "halt":
        expected_gas_used = gas_limit
    else:
        expected_gas_used = (
            intrinsic_execution
            + top_frame_execution
            + code.execution_cost(fork)
        )

    tx = Transaction(
        to=delegator,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    state_test(
        pre=pre,
        post={delegator: Account(storage={0: 0})},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_delegation_pointer_to_delegated_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a pointer aimed at an already-delegated account.

    Delegation resolves only once,
    so the frame executes the designator bytes (0xef0100 || writer) as code.
    Since 0xef is undefined, execution halts before reaching writer's SSTORE.
    The reservoir stays untouched and is refunded, so the bill equals the cap,
    not the full gas limit.
    """
    writer = pre.deploy_contract(code=Op.SSTORE(0, 1))
    inner = pre.fund_eoa(delegation=writer)
    outer = pre.fund_eoa(delegation=inner)

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    tx = Transaction(
        to=outer,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit_cap),
    )

    state_test(
        pre=pre,
        post={
            outer: Account(storage={}),
            inner: Account(storage={}),
            writer: Account(storage={}),
        },
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=gas_limit_cap),
    )
