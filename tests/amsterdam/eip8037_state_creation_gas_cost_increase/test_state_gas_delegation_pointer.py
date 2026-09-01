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
    top_frame_execution = fork.transaction_top_frame_gas_calculator()(
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
    top_frame_execution = fork.transaction_top_frame_gas_calculator()(
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
    top_frame_execution = fork.transaction_top_frame_gas_calculator()(
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
