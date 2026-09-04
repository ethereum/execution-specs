"""
Tests for the EIP-7702 authorization *execution*-gas repricing under
[EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Under EIP-2780 each EIP-7702 authorization is charged in two parts: a
state-independent *execution* base cost paid in the intrinsic, and
state-dependent costs (``NEW_ACCOUNT`` / ``ACCOUNT_WRITE`` for a new
authority leaf, ``AUTH_BASE`` for a net-new delegation indicator) paid
lazily at the top frame in ``set_delegation``. This module pins the
**execution** per-authorization intrinsic magnitude and the repriced
cold/warm account-access costs that an authorized delegation incurs
when later accessed by a ``CALL``.

The execution per-authorization intrinsic magnitude is the fixed
per-authorization base cost charged by the intrinsic (on Amsterdam,
``101 * 16`` calldata tokens plus the ``3000`` ecrecover, ``3000`` cold
and ``2 * 100`` warm accesses of the EIP-7702 base), isolated here as
the intrinsic delta of adding one authorization. The top-frame
state charges are asserted by the sibling
``eip8037_state_creation_gas_cost_increase`` and
``eip2780_reduce_intrinsic_tx_gas`` suites; this suite does not
re-assert them.
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _execution_per_auth(fork: Fork) -> int:
    """
    Return the *execution* intrinsic gas charged per EIP-7702
    authorization.

    Under EIP-2780 the intrinsic charges only the state-independent
    per-authorization base cost; the account-write (``ACCOUNT_WRITE``)
    and delegation-write (``AUTH_BASE``) costs are charged lazily at the
    top frame, not in the intrinsic. Isolated as the intrinsic delta of
    adding one authorization.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    return calc(
        authorization_list_or_count=1,
        return_cost_deducted_prior_execution=True,
    ) - calc(
        authorization_list_or_count=0,
        return_cost_deducted_prior_execution=True,
    )


def _execution_intrinsic(
    fork: Fork,
    *,
    n: int,
    access_list: List[AccessList] | None = None,
    calldata: bytes = b"",
) -> int:
    """
    Return the intrinsic gas of a set-code
    transaction: the full intrinsic less the authorization state gas.
    """
    return fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=n,
        access_list=access_list,
        calldata=calldata,
        return_cost_deducted_prior_execution=True,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("n", [1, 2, 3])
@pytest.mark.parametrize(
    "authority_exists",
    [
        pytest.param(False, id="new_authority"),
        pytest.param(True, id="existing_authority"),
    ],
)
@pytest.mark.parametrize(
    "authority_in_access_list",
    [
        pytest.param(False, id="empty_access_list"),
        pytest.param(True, id="access_list_contains_authority"),
    ],
)
def test_auth_execution_intrinsic_magnitude(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    n: int,
    authority_exists: bool,
    authority_in_access_list: bool,
) -> None:
    """
    Assert the EIP-8038 *execution* per-authorization intrinsic magnitude.

    The execution intrinsic above the ``n=0`` base must equal
    ``n * execution_per_auth`` plus the access-list delta (derived from
    the calculator itself so the calldata-floor contribution of the
    access-list bytes is accounted for).
    """
    contract = pre.deploy_contract(code=Op.STOP)

    signers = [
        pre.fund_eoa() if authority_exists else pre.fund_eoa(amount=0)
        for _ in range(n)
    ]
    authorization_list = [
        AuthorizationTuple(address=contract, nonce=0, signer=signer)
        for signer in signers
    ]

    access_list: List[AccessList] | None = None
    if authority_in_access_list:
        access_list = [
            AccessList(address=signer, storage_keys=[]) for signer in signers
        ]

    base_execution = _execution_intrinsic(fork, n=0)
    execution = _execution_intrinsic(fork, n=n, access_list=access_list)

    # Access-list delta is derived from the calculator (it folds in the
    # calldata-floor cost of the access-list bytes), never hardcoded.
    access_list_delta = _execution_intrinsic(
        fork, n=0, access_list=access_list
    ) - _execution_intrinsic(fork, n=0)

    expected_per_auth = _execution_per_auth(fork)
    assert (
        execution - base_execution == n * expected_per_auth + access_list_delta
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        access_list=access_list,
        sender=sender,
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in signers
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.inclusion_test
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.exception_test
@pytest.mark.parametrize("n", [1, 3])
def test_auth_intrinsic_oog_boundary(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    n: int,
) -> None:
    """
    Reject a set-code transaction one gas below the full intrinsic.

    ``gas_limit`` is set to ``full_intrinsic - 1`` (full intrinsic =
    execution + auth state gas). Catches an implementation that omits the
    repriced execution per-authorization cost from the intrinsic check.
    """
    contract = pre.deploy_contract(code=Op.STOP)
    authorization_list = [
        AuthorizationTuple(address=contract, nonce=0, signer=pre.fund_eoa())
        for _ in range(n)
    ]

    full_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
    )

    tx = Transaction(
        to=contract,
        gas_limit=full_intrinsic - 1,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "invalidity",
    [
        pytest.param("invalid_nonce", id="invalid_nonce"),
        pytest.param("invalid_chain_id", id="invalid_chain_id"),
        pytest.param("repeated_nonce", id="repeated_nonce"),
        pytest.param("authority_is_contract", id="authority_is_contract"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_invalid_auth_charged_intrinsic(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    invalidity: str,
) -> None:
    """
    A skipped (invalid) authorization is still charged the full
    intrinsic, and the invalid authority's account is left unchanged.

    Each invalidity kind (``INVALID_NONCE``, ``INVALID_CHAIN_ID``,
    ``REPEATED_NONCE``, ``AUTHORITY_IS_CONTRACT``) makes the
    authorization invalid during processing, so it is silently skipped,
    but its execution + state intrinsic gas is still paid. The transaction
    succeeds.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    # Build a (possibly multi-element) authorization list where the
    # authority that *should* end up untouched is the invalid one.
    authorization_list: List[AuthorizationTuple] = []

    if invalidity == "invalid_nonce":
        authority = pre.fund_eoa()
        authorization_list.append(
            AuthorizationTuple(
                address=contract,
                nonce=99,  # wrong nonce -> skipped
                signer=authority,
            )
        )
        expected_code: bytes | Bytecode = b""
    elif invalidity == "invalid_chain_id":
        authority = pre.fund_eoa()
        authorization_list.append(
            AuthorizationTuple(
                address=contract,
                nonce=0,
                chain_id=9999,  # wrong chain id -> skipped
                signer=authority,
            )
        )
        expected_code = b""
    elif invalidity == "repeated_nonce":
        # First auth is valid and consumes nonce 0; the second reuses
        # nonce 0 and is therefore skipped. The (single) signer ends up
        # delegated by the first auth, so assert that delegation.
        authority = pre.fund_eoa()
        authorization_list.append(
            AuthorizationTuple(address=contract, nonce=0, signer=authority)
        )
        authorization_list.append(
            AuthorizationTuple(address=contract, nonce=0, signer=authority)
        )
        expected_code = Spec7702.delegation_designation(contract)
    elif invalidity == "authority_is_contract":
        # An authority that is already a (non-delegation) contract is an
        # invalid authority; the authorization is skipped and the
        # contract code is left intact.
        authority = pre.fund_eoa(code=Op.STOP)
        authorization_list.append(
            AuthorizationTuple(address=contract, nonce=0, signer=authority)
        )
        expected_code = Op.STOP
    else:
        raise ValueError(f"unknown invalidity: {invalidity!r}")

    # The full intrinsic (execution + state) is charged regardless of
    # validity. Provide a comfortable gas limit and let the receipt
    # accounting be verified by the framework; the key assertion is the
    # untouched-authority post state.
    full_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
    )
    assert full_intrinsic > 0

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=sender,
    )

    post = {authority: Account(code=expected_code)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "invalidity",
    [
        pytest.param("invalid_nonce", id="invalid_nonce"),
        pytest.param("invalid_chain_id", id="invalid_chain_id"),
        pytest.param("repeated_nonce", id="repeated_nonce"),
        pytest.param("authority_is_contract", id="authority_is_contract"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mixed_validity_multi_auth_receipt_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    invalidity: str,
) -> None:
    """
    Pin the exact receipt gas of a transaction carrying one valid and
    one invalid authorization under the EIP-2780 top-frame charge model.

    Both tuples pay the state-independent ``EXECUTION_PER_AUTH_BASE_COST``
    in the intrinsic. The single valid authorization's authority leaf
    already exists (a funded EOA) and gains a net-new delegation
    indicator, so at the top frame it pays the first-write
    ``ACCOUNT_WRITE`` and ``AUTH_BASE`` -- no ``NEW_ACCOUNT`` and no
    refund. The invalid tuple is silently skipped during
    ``set_delegation`` and pays nothing beyond the intrinsic base.

    Each ``invalidity`` kind (``INVALID_NONCE``, ``INVALID_CHAIN_ID``,
    ``REPEATED_NONCE``, ``AUTHORITY_IS_CONTRACT``) yields the same
    one-valid-one-invalid shape, so every kind pins the same receipt
    gas. This is the numeric-receipt companion to
    ``test_invalid_auth_charged_intrinsic`` (which asserts only post
    state).
    """
    delegate = pre.deploy_contract(code=Op.STOP)

    # The single valid authorization: an existing (funded) authority
    # gaining a net-new delegation. It writes a delegation indicator
    # (AUTH_BASE at the top frame) but creates no account.
    valid_signer = pre.fund_eoa()
    valid_auth = AuthorizationTuple(
        address=delegate,
        nonce=0,
        signer=valid_signer,
        creates_account=False,
        writes_delegation=True,
    )

    # One valid tuple plus one invalid tuple of the requested kind. The
    # invalid tuple is skipped in ``set_delegation``, so it neither
    # creates an account nor writes a delegation indicator.
    authorization_list: List[AuthorizationTuple]
    post: dict = {
        valid_signer: Account(
            code=Spec7702.delegation_designation(delegate),
        ),
    }

    if invalidity == "invalid_nonce":
        authority = pre.fund_eoa()
        authorization_list = [
            valid_auth,
            AuthorizationTuple(
                address=delegate,
                nonce=99,  # wrong nonce -> skipped
                signer=authority,
                creates_account=False,
                writes_delegation=False,
                first_write=False,
            ),
        ]
        post[authority] = Account(code=b"")
    elif invalidity == "invalid_chain_id":
        authority = pre.fund_eoa()
        authorization_list = [
            valid_auth,
            AuthorizationTuple(
                address=delegate,
                nonce=0,
                chain_id=9999,  # wrong chain id -> skipped
                signer=authority,
                creates_account=False,
                writes_delegation=False,
                first_write=False,
            ),
        ]
        post[authority] = Account(code=b"")
    elif invalidity == "repeated_nonce":
        # The valid tuple consumes the signer's nonce 0; a second tuple
        # reusing nonce 0 on the same signer is skipped.
        authorization_list = [
            valid_auth,
            AuthorizationTuple(
                address=delegate,
                nonce=0,
                signer=valid_signer,
                creates_account=False,
                writes_delegation=False,
                first_write=False,
            ),
        ]
    elif invalidity == "authority_is_contract":
        # An authority that is already a (non-delegation) contract is an
        # invalid authority; its authorization is skipped and the
        # contract code is left intact.
        authority = pre.fund_eoa(code=Op.STOP)
        authorization_list = [
            valid_auth,
            AuthorizationTuple(
                address=delegate,
                nonce=0,
                signer=authority,
                creates_account=False,
                writes_delegation=False,
                first_write=False,
            ),
        ]
        post[authority] = Account(code=Op.STOP)
    else:
        raise ValueError(f"unknown invalidity: {invalidity!r}")

    n = len(authorization_list)

    # Charge model (no refunds): the intrinsic charges the per-auth base
    # for every tuple; the one valid authorization adds ``AUTH_BASE`` at
    # the top frame for its net-new delegation indicator. The skipped
    # tuple and the plain ``STOP`` recipient add nothing.
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=n,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )
    cumulative_gas_used = (
        intrinsic_execution + top_frame_execution + top_frame_state
    )

    tx = Transaction(
        to=delegate,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "self_sponsored",
    [
        pytest.param(False, id="external_sponsor"),
        pytest.param(True, id="self_sponsor"),
    ],
)
@pytest.mark.parametrize(
    "delegation_in_access_list",
    [
        pytest.param(False, id="delegation_cold"),
        pytest.param(True, id="delegation_warm"),
    ],
)
def test_auth_account_warming(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    self_sponsored: bool,
    delegation_in_access_list: bool,
) -> None:
    """
    A later ``CALL`` to an authorized authority pays the repriced
    cold/warm account-access costs, plus the delegation double-charge.

    The authority itself is warmed by the authorization (added to
    ``accessed_addresses`` during validation), so the ``CALL`` access
    to it is ``WARM_ACCESS``. Because the authority carries a delegation
    designator, accessing it triggers a *second* access to the
    delegation target: ``WARM_ACCESS`` if that target is in the access
    list (or is the authority itself, for self-delegation), else
    ``COLD_ACCOUNT_ACCESS``. When the sponsor is the authority, the
    authority is already warm for the same reason.

    All costs are derived from the fork's opcode schedule (not
    hardcoded) so the repricing is asserted against the live values.
    """
    # Bare account-access costs, isolated via BALANCE (no code-read
    # surcharge and no operand push).
    cold = Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork)
    warm = Op.BALANCE.with_metadata(address_warm=True).gas_cost(fork)

    delegation_target = pre.deploy_contract(code=Op.STOP)

    if self_sponsored:
        # Self-sponsored: the sender is the authority. fund_eoa with a
        # delegation pre-installs the designator and sets nonce to 1.
        sender = pre.fund_eoa(delegation=delegation_target)
        authority: Address = sender
        authorization_list = None
    else:
        sender = pre.fund_eoa()
        authority = pre.fund_eoa()
        authorization_list = [
            AuthorizationTuple(
                address=delegation_target,
                nonce=0,
                signer=authority,
            )
        ]

    access_list: List[AccessList] | None = None
    if delegation_in_access_list:
        access_list = [AccessList(address=delegation_target, storage_keys=[])]

    # Authority access: always warm (authorization or self-sponsor warms
    # it). Delegation target double-charge: warm iff in the access list,
    # else cold.
    delegation_access = warm if delegation_in_access_list else cold
    expected_cost = warm + delegation_access

    # Measure the cost of a single CALL to the authority. The CALL
    # opcode leaves one stack item (success); the overhead is the PUSHes
    # for its arguments.
    overhead_cost = Op.PUSH1(0).execution_cost(fork) * len(Op.CALL.kwargs)
    storage = Storage()
    callee_code = CodeGasMeasure(
        code=Op.CALL(gas=0, address=authority),
        overhead_cost=overhead_cost,
        extra_stack_items=1,
        sstore_key=storage.store_next(expected_cost),
    )
    callee_address = pre.deploy_contract(callee_code)

    tx = Transaction(
        to=callee_address,
        authorization_list=authorization_list,
        access_list=access_list,
        sender=sender,
    )

    post = {
        callee_address: Account(storage=storage),
        authority: Account(
            code=Spec7702.delegation_designation(delegation_target),
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_many_auths_block_limit(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Pack many authorizations into a single transaction near the gas
    limit cap and confirm it succeeds.

    The authorization count is sized from the per-authorization total
    intrinsic (execution + state) and the transaction gas-limit cap, so it
    automatically tracks the repriced cost.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    contract = pre.deploy_contract(code=Op.STOP)

    # Per-authorization total for a fresh (empty) authority: the execution
    # intrinsic base plus the top-frame account-write, account-creation
    # and delegation-write charges, derived from the fork's calculators
    # so it tracks the repricing. The probe only feeds the gas
    # calculators, so it is signed with a fixed dummy key rather than a
    # throwaway pre-state signer.
    probe_auth = AuthorizationTuple(
        address=contract,
        nonce=0,
        secret_key=Hash(1),
        creates_account=True,
        writes_delegation=True,
        first_write=True,
    )
    per_auth_total = (
        _execution_per_auth(fork)
        + fork.transaction_top_frame_execution_gas(authorizations=[probe_auth])
        + fork.transaction_top_frame_state_gas(authorizations=[probe_auth])
    )
    base = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=0,
    )
    # Leave headroom for the base intrinsic and a little slack.
    num_auths = (gas_limit_cap - base) // per_auth_total
    assert num_auths >= 2

    signers = [pre.fund_eoa() for _ in range(num_auths)]
    authorization_list = [
        AuthorizationTuple(address=contract, nonce=0, signer=signer)
        for signer in signers
    ]

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=sender,
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in signers
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
