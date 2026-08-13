"""
Gas-limit boundary tests for EIP-2780.

Pin transactions one gas below the intrinsic charge layer to verify the
transaction is rejected by the pre-execution intrinsic gas check at
that boundary. Top-frame boundary OOGs are covered by the dedicated
top-frame charge tests in ``test_top_frame_charges.py``.
"""

import pytest
from execution_testing import (
    Alloc,
    AuthorizationTuple,
    Fork,
    Hash,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as EIP4844_Spec
from .helpers import (
    EOA_INITIAL_BALANCE,
    RECIPIENT_TYPES_NON_CREATE,
    AuthorizationAction,
    build_authorization,
    setup_target,
)
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.parametrize("recipient_type", RECIPIENT_TYPES_NON_CREATE)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_intrinsic_gas_floor_boundary(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    recipient_type: RecipientType,
    value: int,
) -> None:
    """
    Reject when ``gas_limit = intrinsic_gas - 1``.

    The transaction never enters the EVM; it is rejected by the
    pre-execution intrinsic gas check.
    """
    sender = pre.fund_eoa(10**18)
    target = setup_target(pre, recipient_type, sender)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=recipient_type,
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=intrinsic_gas - 1,
        gas_price=1_000_000_000,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, tx=tx, post={})


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_intrinsic_gas_floor_boundary_contract_creation(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Reject a contract-creation transaction when
    ``gas_limit = intrinsic_gas - 1``.

    A creation tx's intrinsic includes the ``NEW_ACCOUNT`` state gas, so
    the pre-execution check rejects against the combined
    ``execution + state`` intrinsic. The init code never runs.
    """
    sender = pre.fund_eoa(10**18)
    init_code = Op.STOP

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        value=value,
        data=init_code,
        gas_limit=intrinsic_gas - 1,
        gas_price=1_000_000_000,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, tx=tx, post={})


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "authorization_count",
    [
        pytest.param(1, id="one_authorization"),
        pytest.param(2, id="two_authorizations"),
    ],
)
def test_intrinsic_gas_floor_boundary_with_authorizations(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    authorization_count: int,
) -> None:
    """
    Reject a type-4 transaction when ``gas_limit = intrinsic_gas - 1``,
    where the intrinsic includes ``EXECUTION_PER_AUTH_BASE_COST`` per
    authorization.

    EIP-2780 keeps only the state-independent per-authorization base
    cost in the intrinsic (the state-dependent remainder moved to the
    top frame). The calldata floor does not count authorization tuples,
    so the intrinsic -- which scales with the authorization count -- is
    the binding minimum. The transaction is rejected before
    ``set_delegation`` runs, so no authority is mutated.
    """
    sender = pre.fund_eoa(10**18)
    target = pre.fund_eoa(amount=EOA_INITIAL_BALANCE)
    delegate_to = pre.deploy_contract(code=Op.STOP)

    authorization_list = [
        AuthorizationTuple(
            address=delegate_to,
            nonce=0,
            signer=pre.fund_eoa(),
        )
        for _ in range(authorization_count)
    ]

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.EOA,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        value=0,
        authorization_list=authorization_list,
        gas_limit=intrinsic_gas - 1,
        max_fee_per_gas=1_000_000_000,
        max_priority_fee_per_gas=1_000_000_000,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, tx=tx, post=pre)


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type != 6)
def test_intrinsic_gas_floor_boundary_all_tx_types(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    tx_type: int,
) -> None:
    """
    Reject every transaction type when ``gas_limit = intrinsic_gas - 1``.

    Each type layers its own intrinsic components on the shared
    value-transfer shape -- ``EXECUTION_PER_AUTH_BASE_COST`` for type 4 --
    and the pre-execution check must reject one gas below the per-type
    total. Blob gas is priced in its own dimension, so a type-3
    transaction's execution-gas boundary is identical to type 2.
    """
    value = 1
    sender = pre.fund_eoa()
    target = pre.fund_eoa(amount=EOA_INITIAL_BALANCE)

    scenario = (
        build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
        if tx_type == 4
        else None
    )
    authorizations = [scenario.authorization] if scenario else []

    blob_versioned_hashes = (
        add_kzg_version([Hash(1)], EIP4844_Spec.BLOB_COMMITMENT_VERSION_KZG)
        if tx_type == 3
        else None
    )

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
        authorization_list_or_count=authorizations,
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=target,
        value=value,
        authorization_list=authorizations or None,
        blob_versioned_hashes=blob_versioned_hashes,
        gas_limit=intrinsic_gas - 1,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, tx=tx, post=pre)
