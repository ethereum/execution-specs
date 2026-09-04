"""
Test EIP-7702 SetCode authorization state gas under the EIP-2780
top-frame charge model.

Under EIP-2780 (Amsterdam) an authorization's intrinsic cost is only the
state-independent ``EXECUTION_PER_AUTH_BASE_COST``; there is no intrinsic
auth state gas and there are no auth refunds. The state-dependent costs
are charged lazily at the top frame in ``set_delegation``, keyed on each
authority's pre-transaction state:

* ``NEW_ACCOUNT`` (state) + ``ACCOUNT_WRITE`` (execution) when the
  authority's account leaf does not exist pre-tx (it gets created); and
* ``AUTH_BASE`` (state) when a net-new delegation indicator is written --
  the authority holds no delegation both before the transaction and at
  the point the authorization applies, and the authorization is not a
  clear.

For a value-free type-4 transaction whose recipient runs code ``code``:

* the receipt ``cumulative_gas_used`` is the plain sum
  ``intrinsic_execution + top_frame_execution + top_frame_state +
  evm_execution + evm_state`` (no refund term); and
* the header ``gas_used`` is ``max(block_execution, block_state)`` where
  ``block_execution = intrinsic_execution + top_frame_execution +
  evm_execution`` and ``block_state = top_frame_state +
  evm_state``.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037); the ``valid_from("EIP8037")``
markers resolve to Amsterdam, where EIP-2780 governs the charge model.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Header,
    Op,
    RecipientType,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.checklists import EIPChecklist

from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

from .spec import ref_spec_8037
from .test_state_gas_sstore import revoked_advance_call_tree

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def _auth_gas(
    fork: Fork,
    authorization_list: list[AuthorizationTuple],
    *,
    recipient_type: RecipientType = RecipientType.CONTRACT,
    sends_value: bool = False,
    delegation_warm: bool = False,
) -> tuple[int, int, int]:
    """Return (intrinsic_execution, top_frame_execution, top_frame_state)."""
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
        recipient_type=recipient_type,
        sends_value=sends_value,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_gas_calculator()(
        recipient_type=recipient_type,
        sends_value=sends_value,
        delegation_warm=delegation_warm,
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        recipient_type=recipient_type,
        sends_value=sends_value,
        authorizations=authorization_list,
    )
    return intrinsic_execution, top_frame_execution, top_frame_state


def _receipt_and_header(
    intrinsic_execution: int,
    top_frame_execution: int,
    top_frame_state: int,
    *,
    evm_execution: int = 0,
    evm_state: int = 0,
) -> tuple[int, int]:
    """
    Return the (receipt cumulative_gas_used, header gas_used) for a
    successful (non-reverting) transaction under the no-refund top-frame
    model.
    """
    block_execution = intrinsic_execution + top_frame_execution + evm_execution
    block_state = top_frame_state + evm_state
    cumulative_gas_used = block_execution + block_state
    header_gas_used = max(block_execution, block_state)
    return cumulative_gas_used, header_gas_used


@pytest.mark.parametrize(
    "num_auths",
    [
        pytest.param(1, id="single_auth"),
        pytest.param(3, id="three_auths"),
    ],
)
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("EIP8037")
def test_authorization_state_gas_scaling(
    state_test: StateTestFiller,
    pre: Alloc,
    num_auths: int,
    fork: Fork,
) -> None:
    """
    Test the top-frame authorization state gas scales with count.

    Each authority is an existing funded EOA gaining a fresh delegation,
    so ``set_delegation`` charges only the top-frame ``AUTH_BASE`` per
    authorization (no ``NEW_ACCOUNT`` / ``ACCOUNT_WRITE`` and no refund).
    The receipt gas is the execution intrinsic plus ``num_auths *
    AUTH_BASE`` and the header ``gas_used`` is the max of the execution and
    state blocks.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    signers = [pre.fund_eoa() for _ in range(num_auths)]
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
        for signer in signers
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in signers
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "reservoir_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@pytest.mark.valid_from("EIP8037")
def test_auth_state_gas_drawn_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reservoir_delta: int,
) -> None:
    """
    Verify the top-frame authorization charge is drawn from the state gas
    reservoir before `gas_left`.

    The reservoir holds the authorization's charge plus one storage set.
    A probe in a child frame is handed only its SSTORE's execution cost,
    so it can reach the reservoir but not the caller's `gas_left`: one
    gas short of that sizing it cannot pay, which happens only if the
    authorization took its own charge from the reservoir first.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    probe_ran = reservoir_delta == 0

    probe_storage = Storage()
    probe_code = Op.SSTORE(
        probe_storage.store_next(1 if probe_ran else 0, "probe_ran"), 1
    )
    probe = pre.deploy_contract(probe_code)
    probe_stipend = probe_code.execution_cost(fork)

    recipient = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=probe_stipend, address=probe))
    )

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=recipient,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
    ]

    _, _, top_frame_state = _auth_gas(fork, authorization_list)
    assert top_frame_state > 0, (
        "the authorization must carry a top-frame state charge"
    )
    reservoir = top_frame_state + sstore_state_gas + reservoir_delta

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(recipient)),
        probe: Account(storage=probe_storage),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_pre_delegated_authority_no_charge_after_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Verify re-delegating an already-delegated authority carries no
    top-frame state charge, whether or not the top frame then fails.

    The indicator is not net-new, so ``set_delegation`` charges no
    ``AUTH_BASE``. A failing top frame must not turn that into a charge:
    the state dimension stays empty and the header reports the execution
    total alone.
    """
    first = pre.deploy_contract(code=Op.STOP)

    ending = Op.REVERT(0, 0) if failure_mode == "revert" else Op.INVALID
    recipient = pre.deploy_contract(code=ending)

    signer = pre.fund_eoa(delegation=first)
    authorization_list = [
        AuthorizationTuple(
            address=recipient,
            # The delegation setup already moved the nonce to 1.
            nonce=1,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=True,
        )
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork,
        authorization_list,
        recipient_type=RecipientType.DELEGATION_7702,
    )
    assert top_frame_state == 0, (
        "re-delegating an existing indicator is not net-new state"
    )

    gas_limit = intrinsic_execution + top_frame_execution + 50_000

    if failure_mode == "halt":
        # An exceptional halt burns the whole budget.
        expected_gas_used = gas_limit
    else:
        # REVERT returns the gas it did not spend.
        expected_gas_used = (
            intrinsic_execution
            + top_frame_execution
            + ending.execution_cost(fork)
        )

    tx = Transaction(
        to=signer,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            status=0, cumulative_gas_used=expected_gas_used
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(recipient)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "num_auths",
    [
        pytest.param(1, id="single_auth"),
        pytest.param(2, id="two_auths"),
        pytest.param(3, id="three_auths"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_set_code_tx_below_total_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    num_auths: int,
) -> None:
    """
    Reject a set_code tx one gas below the (now execution-only) intrinsic.

    Under EIP-2780 the authorization intrinsic is entirely execution (the
    state-dependent costs moved to the top frame), so the intrinsic gas
    the transaction must cover is exactly
    ``fork.transaction_intrinsic_cost_calculator()(auth_list)``. Sweeping
    ``num_auths`` and pinning ``gas_limit`` at ``intrinsic - 1`` catches
    an implementation that omits the repriced per-authorization base cost
    from the pre-validate check.
    """
    contract = pre.deploy_contract(code=Op.STOP)
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=pre.fund_eoa(),
            creates_account=False,
            writes_delegation=True,
        )
        for _ in range(num_auths)
    ]

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
    )

    tx = Transaction(
        to=contract,
        gas_limit=intrinsic - 1,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_existing_account_no_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    An existing-authority delegation is charged the reduced top-frame
    cost directly, with no refund.

    The authority is an existing funded EOA gaining a fresh delegation.
    Its leaf exists, so ``set_delegation`` charges neither ``NEW_ACCOUNT``
    nor ``ACCOUNT_WRITE`` (and, unlike the superseded EIP-8037 behaviour,
    refunds neither); it charges only the top-frame ``AUTH_BASE``. The
    receipt gas is therefore exactly the execution intrinsic plus
    ``AUTH_BASE``.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {signer: Account(code=Spec7702.delegation_designation(contract))}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_mixed_new_and_existing_auths(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test mixed new and existing account authorizations at the top frame.

    One authority is an existing EOA (charged only ``AUTH_BASE``); the
    other does not exist pre-tx (charged ``NEW_ACCOUNT`` + ``ACCOUNT_WRITE``
    for the leaf plus ``AUTH_BASE`` for the net-new indicator). The total
    top-frame charge is the sum of the two, with no refund.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    existing_signer = pre.fund_eoa()
    new_signer = pre.fund_eoa(amount=0)

    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=existing_signer,
            creates_account=False,
            writes_delegation=True,
        ),
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=new_signer,
            creates_account=True,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        existing_signer: Account(
            code=Spec7702.delegation_designation(contract),
        ),
        new_signer: Account(
            nonce=1,
            balance=0,
            code=Spec7702.delegation_designation(contract),
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_authorization_with_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SetCode authorization combined with a recipient SSTORE.

    The authority (an existing EOA) gains a fresh delegation, charged the
    top-frame ``AUTH_BASE``; the called recipient then performs an SSTORE
    whose execution and state costs are charged during execution. The header
    ``gas_used`` is the max of the execution block and the (``AUTH_BASE`` +
    SSTORE) state block.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)
    evm_execution = code.execution_cost(fork)
    evm_state = code.state_cost(fork)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    _, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=evm_execution,
        evm_state=evm_state,
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_existing_account_no_refund_with_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    An existing-authority auth and a recipient SSTORE are both charged
    in full, with no refund reducing either.

    The existing authority pays only the top-frame ``AUTH_BASE`` (no
    ``NEW_ACCOUNT`` / ``ACCOUNT_WRITE`` and no refund), and the recipient's
    SSTORE pays its own execution + state costs. The receipt gas is the
    exact sum of the intrinsic, the ``AUTH_BASE`` and the SSTORE cost;
    there is no reservoir refund to draw on.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)
    evm_execution = code.execution_cost(fork)
    evm_state = code.state_cost(fork)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=evm_execution,
        evm_state=evm_state,
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        contract: Account(storage=storage),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "signer_pre_state,authorize_to_null",
    [
        pytest.param("nonexistent", False, id="nonexistent_authority"),
        pytest.param("nonexistent", True, id="nonexistent_clear"),
        pytest.param("existing_leaf", False, id="existing_leaf_empty_code"),
        pytest.param("existing_leaf", True, id="existing_leaf_clear"),
        pytest.param(
            "existing_delegation",
            False,
            id="existing_delegation_overwrite",
        ),
        pytest.param(
            "existing_delegation",
            True,
            id="existing_delegation_clear",
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_auth_block_gas_accounting(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    signer_pre_state: str,
    authorize_to_null: bool,
) -> None:
    """
    Verify block + receipt gas accounting against the per-authorization
    top-frame charge in ``set_delegation``.

    Six signer pre-states span every top-frame charge branch:

    * ``nonexistent`` + delegate -- leaf created and a net-new indicator
      written: ``NEW_ACCOUNT`` + ``ACCOUNT_WRITE`` + ``AUTH_BASE``;
    * ``nonexistent`` + clear -- leaf created, no indicator:
      ``NEW_ACCOUNT`` + ``ACCOUNT_WRITE`` only;
    * ``existing_leaf`` + delegate -- net-new indicator only:
      ``AUTH_BASE``;
    * ``existing_leaf`` + clear -- nothing beyond the intrinsic base;
    * ``existing_delegation`` overwrite / clear -- already delegated
      pre-tx, so no net-new indicator: nothing beyond the intrinsic base.

    No branch is refunded (the EIP-8037 over-charge-then-refund is gone).
    Verified via header ``gas_used``, receipt ``cumulative_gas_used`` and
    the authority post-state (which catches a silently-skipped auth).
    """
    contract_old = pre.deploy_contract(code=Op.STOP)
    contract_new = pre.deploy_contract(code=Op.STOP)

    if signer_pre_state == "nonexistent":
        signer = pre.fund_eoa(amount=0)
        pre_nonce = 0
        creates_account = True
    elif signer_pre_state == "existing_leaf":
        signer = pre.fund_eoa()
        pre_nonce = 0
        creates_account = False
    elif signer_pre_state == "existing_delegation":
        # `fund_eoa(delegation=...)` sets the authority's nonce to 1.
        signer = pre.fund_eoa(delegation=contract_old)
        pre_nonce = 1
        creates_account = False
    else:
        raise ValueError(f"unknown signer_pre_state: {signer_pre_state!r}")

    auth_target = (
        Spec7702.RESET_DELEGATION_ADDRESS
        if authorize_to_null
        else contract_new
    )
    # A net-new delegation indicator is written only when the auth is not
    # a clear and the authority was not already delegated before the tx.
    writes_delegation = (not authorize_to_null) and (
        signer_pre_state != "existing_delegation"
    )

    authorization_list = [
        AuthorizationTuple(
            address=auth_target,
            nonce=pre_nonce,
            signer=signer,
            creates_account=creates_account,
            writes_delegation=writes_delegation,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    post_code = (
        b""
        if authorize_to_null
        else Spec7702.delegation_designation(contract_new)
    )
    if signer_pre_state == "nonexistent":
        post_signer = Account(nonce=pre_nonce + 1, balance=0, code=post_code)
    else:
        post_signer = Account(nonce=pre_nonce + 1, code=post_code)

    tx = Transaction(
        to=contract_new,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    state_test(
        pre=pre,
        post={signer: post_signer},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_invalid_nonce_auth_still_charges_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test an invalid-nonce authorization still pays the intrinsic base.

    An authorization with a wrong nonce is skipped during
    ``set_delegation``, so it writes no delegation indicator and incurs
    no top-frame charge. Its state-independent
    ``EXECUTION_PER_AUTH_BASE_COST`` is still charged in the intrinsic, and
    the authority is left untouched.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=99,  # Wrong nonce -- auth will be skipped
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    assert top_frame_execution == 0
    assert top_frame_state == 0
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {signer: Account(nonce=0, code=b"")}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_invalid_chain_id_auth_still_charges_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test an invalid-chain-id authorization still pays the intrinsic base.

    An authorization with a mismatched chain ID is skipped during
    ``set_delegation`` and incurs no top-frame charge, but its
    ``EXECUTION_PER_AUTH_BASE_COST`` is still charged in the intrinsic and
    the authority is left untouched.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            chain_id=9999,  # Wrong chain ID -- auth will be skipped
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    assert top_frame_execution == 0
    assert top_frame_state == 0
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {signer: Account(nonce=0, code=b"")}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_self_sponsored_authorization(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a self-sponsored authorization where the sender is the authority.

    The transaction consumes the sender's nonce (0 -> 1) before
    ``set_delegation`` runs, so the authorization must carry ``nonce=1``
    to match. ``set_delegation`` then applies the delegation and bumps the
    nonce again (1 -> 2). The sender's leaf already exists (no
    ``NEW_ACCOUNT``) and was already written at inclusion -- priced into
    ``TX_BASE`` -- so the delegation write is not the transaction's
    first write to it (no ``ACCOUNT_WRITE``); only the top-frame
    ``AUTH_BASE`` is charged, with no refund.
    """
    delegate = pre.deploy_contract(code=Op.STOP)
    recipient = pre.deploy_contract(code=Op.STOP)

    # Sender is also the authority (self-sponsored). The tx bumps the
    # sender nonce to 1 before set_delegation, so the auth uses nonce=1.
    sender = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=1,
            signer=sender,
            creates_account=False,
            writes_delegation=True,
            # The sender's leaf is written at inclusion, so this is not
            # the transaction's first write to it.
            first_write=False,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        sender: Account(
            nonce=2,
            code=Spec7702.delegation_designation(delegate),
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_duplicate_signer_authorizations(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test two authorizations from the same signer with increasing nonces.

    The first authorization (nonce 0) sets a fresh delegation on the
    existing authority, paying the first-write ``ACCOUNT_WRITE`` and the
    top-frame ``AUTH_BASE``. The second (nonce 1) overwrites it to a
    different target; the authority is already written and already had a
    delegation set in this transaction, so it pays nothing beyond the
    intrinsic base. The authority ends delegated to the second target
    with nonce 2.
    """
    contract_a = pre.deploy_contract(code=Op.STOP)
    contract_b = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract_a,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
        AuthorizationTuple(
            address=contract_b,
            nonce=1,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract_a,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        signer: Account(
            nonce=2,
            code=Spec7702.delegation_designation(contract_b),
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_auth_with_calldata_and_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test authorization combined with calldata and an access list.

    The execution intrinsic folds in the calldata and access-list costs; on
    top of it the existing authority pays the top-frame ``AUTH_BASE`` and
    the recipient's SSTORE pays its execution + state costs. The
    receipt gas is the exact sum, with no refund term. Access lists do not
    warm the authority under EIP-2780, so the auth charge is unaffected.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(0x42), Op.CALLDATALOAD(0))
    contract = pre.deploy_contract(code=code)
    evm_execution = code.execution_cost(fork)
    evm_state = code.state_cost(fork)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    data = b"\x00" * 31 + b"\x42"
    access_list = [AccessList(address=contract, storage_keys=[])]

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
        calldata=data,
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    _, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=evm_execution,
        evm_state=evm_state,
    )

    tx = Transaction(
        to=contract,
        data=data,
        access_list=access_list,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        contract: Account(storage=storage),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "num_valid,num_invalid",
    [
        pytest.param(1, 1, id="one_valid_one_invalid"),
        pytest.param(2, 1, id="two_valid_one_invalid"),
        pytest.param(1, 2, id="one_valid_two_invalid"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_mixed_valid_and_invalid_auths(
    state_test: StateTestFiller,
    pre: Alloc,
    num_valid: int,
    num_invalid: int,
    fork: Fork,
) -> None:
    """
    Test mixed valid and invalid authorizations under the top-frame model.

    Every tuple (valid or invalid) pays the intrinsic
    ``EXECUTION_PER_AUTH_BASE_COST``. Only the valid authorizations reach
    ``set_delegation`` and each writes a net-new delegation on an existing
    authority, paying the first-write ``ACCOUNT_WRITE`` and the top-frame
    ``AUTH_BASE``; the invalid (wrong nonce) tuples are skipped and pay
    no top-frame charge. The receipt gas is ``intrinsic_execution +
    num_valid * (ACCOUNT_WRITE + AUTH_BASE)``.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    valid_signers = [pre.fund_eoa() for _ in range(num_valid)]
    invalid_signers = [pre.fund_eoa() for _ in range(num_invalid)]

    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
        for signer in valid_signers
    ] + [
        AuthorizationTuple(
            address=contract,
            nonce=99,  # Wrong nonce -- skipped
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        )
        for signer in invalid_signers
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in valid_signers
    }
    for signer in invalid_signers:
        post[signer] = Account(nonce=0, code=b"")

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_many_authorizations(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test ten authorizations, each charged the top-frame ``AUTH_BASE``.

    Ten existing authorities each gain a fresh delegation, so the total
    top-frame state charge is ``10 * AUTH_BASE`` with no refund. Verifies
    the top-frame charge scales correctly for large authorization lists.
    """
    num_auths = 10
    contract = pre.deploy_contract(code=Op.STOP)

    signers = [pre.fund_eoa() for _ in range(num_auths)]
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
        for signer in signers
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in signers
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_auth_with_multiple_sstores(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test an authorization combined with multiple recipient SSTOREs.

    The existing authority pays the top-frame ``AUTH_BASE`` and the
    recipient performs five distinct zero-to-nonzero SSTOREs, each paying
    its own execution + state cost during execution. Verifies combined
    accounting across the top-frame and execution state charges, all drawn
    from ``gas_left`` with no refund.
    """
    num_sstores = 5
    storage = Storage()
    code = Bytecode()
    for _ in range(num_sstores):
        code += Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)
    evm_execution = code.execution_cost(fork)
    evm_state = code.state_cost(fork)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    _, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=evm_execution,
        evm_state=evm_state,
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "gas_delta",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(
            -1,
            id="one_short",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_authorization_exact_state_gas_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Test the intrinsic-gas boundary and the top-frame OOG behaviour.

    Under EIP-2780 the intrinsic is execution-only, so the boundary keys off
    ``fork.transaction_intrinsic_cost_calculator()(auth_list)``. With
    ``gas_delta=-1`` the transaction is one gas below the intrinsic and is
    rejected as intrinsic-gas-too-low. With ``gas_delta=0`` the gas limit
    equals the intrinsic exactly, so the transaction is included but has
    zero gas left for the top frame: the authority's ``NEW_ACCOUNT`` state
    charge in ``set_delegation`` runs out of gas, the whole preparation
    rolls back, and the authority is never created.
    """
    target = pre.deploy_contract(code=Op.STOP)
    recipient = pre.deploy_contract(code=Op.STOP)

    # A fresh (nonexistent) authority so the first top-frame charge is
    # NEW_ACCOUNT, which OOGs when no gas is left after the intrinsic.
    signer = pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=target,
            nonce=0,
            signer=signer,
            creates_account=True,
            writes_delegation=True,
        ),
    ]

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
    )

    is_rejected = gas_delta < 0
    tx = Transaction(
        to=recipient,
        gas_limit=intrinsic_cost + gas_delta,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        error=(
            TransactionException.INTRINSIC_GAS_TOO_LOW if is_rejected else None
        ),
    )

    # gas_delta == 0: tx included, top-frame OOG rolls back the auth, so
    # the authority leaf is never created.
    # gas_delta == -1: tx rejected before execution; authority untouched.
    post = {signer: Account.NONEXISTENT}
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                exception=(
                    TransactionException.INTRINSIC_GAS_TOO_LOW
                    if is_rejected
                    else None
                ),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("EIP8037")
def test_authorization_to_precompile_address(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test an authorization targeting a precompile address applies.

    Authorizing delegation to a precompile address (ecrecover at 0x01) is
    processed like any other target: the authority's code is set to the
    precompile's delegation designator. Only the post-state is asserted
    here; the recipient path becomes a delegation and its exact charge is
    not the focus of this test.
    """
    precompile_address = Address(0x01)
    recipient = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=precompile_address,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        signer: Account(
            code=Spec7702.delegation_designation(precompile_address),
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_multi_tx_block_auth_and_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a multi-transaction block combining a top-frame auth and an
    SSTORE.

    Two transactions share one block:

    1. a SetCode tx delegating an existing authority (top-frame
       ``AUTH_BASE``, no refund); and
    2. a normal tx performing a zero-to-nonzero SSTORE (execution
       + state gas).

    The per-transaction receipt ``cumulative_gas_used`` accumulates across
    the block, so tx1's receipt is its own cost and tx2's is the running
    total. Verifies block-level accounting handles the two side by side.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    # TX 1: delegate an existing authority.
    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]
    intrinsic_execution_1, top_frame_execution_1, top_frame_state_1 = (
        _auth_gas(fork, authorization_list)
    )
    tx1_gas, _ = _receipt_and_header(
        intrinsic_execution_1, top_frame_execution_1, top_frame_state_1
    )
    tx_1 = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=tx1_gas),
    )

    # TX 2: a plain zero-to-nonzero SSTORE.
    storage = Storage()
    sstore_code = Op.SSTORE(storage.store_next(1), 1)
    sstore_contract = pre.deploy_contract(code=sstore_code)
    intrinsic_execution_2 = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.CONTRACT,
        return_cost_deducted_prior_execution=True,
    )
    tx2_gas = (
        intrinsic_execution_2
        + sstore_code.execution_cost(fork)
        + sstore_code.state_cost(fork)
    )
    tx_2 = Transaction(
        to=sstore_contract,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=tx1_gas + tx2_gas,
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract)),
        sstore_contract: Account(storage=storage),
    }
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx_1, tx_2])],
        post=post,
    )


@pytest.mark.valid_from("EIP8037")
def test_fresh_authority_and_sstores_full_state(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a fresh authority plus multiple SSTOREs pay the full state cost.

    A fresh (nonexistent) authority is delegated to the recipient, paying
    ``NEW_ACCOUNT`` + ``ACCOUNT_WRITE`` + ``AUTH_BASE`` at the top frame,
    and the recipient performs three zero-to-nonzero SSTOREs. Every state
    charge (top-frame and execution) is drawn from ``gas_left`` in full:
    there is no reservoir refund and no 1/5 cap in play. The receipt gas
    is the exact sum of all components.
    """
    num_sstores = 3
    storage = Storage()
    code = Bytecode()
    for _ in range(num_sstores):
        code += Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)
    evm_execution = code.execution_cost(fork)
    evm_state = code.state_cost(fork)

    signer = pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=True,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=evm_execution,
        evm_state=evm_state,
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        contract: Account(storage=storage),
        signer: Account(
            nonce=1,
            balance=0,
            code=Spec7702.delegation_designation(contract),
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "num_auths",
    [
        pytest.param(1, id="one_auth"),
        pytest.param(3, id="three_auths"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_existing_account_auth_header_gas_used(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    num_auths: int,
) -> None:
    """
    Verify the header ``gas_used`` for existing-authority delegations.

    Every authority is an existing account gaining a fresh delegation, so
    each pays only the top-frame ``AUTH_BASE`` (no ``NEW_ACCOUNT`` /
    ``ACCOUNT_WRITE`` and no refund). With STOP execution the header
    ``gas_used`` is ``max(intrinsic_execution, num_auths * AUTH_BASE)``.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    signers = [pre.fund_eoa() for _ in range(num_auths)]
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
        for signer in signers
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    _, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in signers
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "num_existing,num_new",
    [
        pytest.param(1, 1, id="one_existing_one_new"),
        pytest.param(2, 2, id="two_existing_two_new"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_mixed_auths_header_gas_used(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    num_existing: int,
    num_new: int,
) -> None:
    """
    Verify the header ``gas_used`` across a mix of existing and new
    authorities.

    Existing authorities pay only ``AUTH_BASE``; new (nonexistent)
    authorities additionally pay ``NEW_ACCOUNT`` (state) + ``ACCOUNT_WRITE``
    (execution) for the created leaf. The header ``gas_used`` is
    ``max(block_execution, block_state)`` over the summed top-frame charges,
    with no refund term.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    existing_signers = [pre.fund_eoa() for _ in range(num_existing)]
    new_signers = [pre.fund_eoa(amount=0) for _ in range(num_new)]

    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
        for signer in existing_signers
    ] + [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=True,
            writes_delegation=True,
        )
        for signer in new_signers
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    _, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(contract))
        for signer in existing_signers
    }
    for signer in new_signers:
        post[signer] = Account(
            nonce=1,
            balance=0,
            code=Spec7702.delegation_designation(contract),
        )

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_auth_state_gas_persists_on_top_level_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the auth state gas stays consumed on a top-level REVERT,
    because the delegation persists, while the reverted execution's own
    state gas is refilled.

    ``set_delegation`` runs in the top-frame preparation, before the
    execution snapshot, so the delegation survives a top-level REVERT
    and the state gas that paid for it (the ``AUTH_BASE`` here) is
    folded out of the frame's refillable pools. The recipient writes an
    SSTORE then REVERTs: the slot rolls back with the frame, so the
    SSTORE's ``STORAGE_SET`` state gas *is* refilled. The receipt is
    therefore the intrinsic and top-frame charges (execution and state)
    plus the execution gas, with only the authorization's state
    portion in the block's state component.
    """
    code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    contract = pre.deploy_contract(code=code)
    evm_execution = code.execution_cost(fork)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    # The SSTORE's state gas is refilled by the REVERT (the slot rolls
    # back); the authorization's state gas persists with its delegation.
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=evm_execution,
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        contract: Account(storage={}),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
        pytest.param("oog", id="oog"),
    ],
)
@pytest.mark.parametrize(
    "authority_exists",
    [
        pytest.param(False, id="new_account"),
        pytest.param(True, id="existing_account"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_auth_state_gas_in_header_after_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
    authority_exists: bool,
) -> None:
    """
    Verify the header ``gas_used`` when the top-level call fails after the
    authorization is applied.

    The delegation is applied in the top-frame preparation (before the
    execution snapshot), so it persists through every failure mode --
    and so does the state gas that paid for it (``NEW_ACCOUNT`` +
    ``AUTH_BASE`` for a fresh authority, ``AUTH_BASE`` for an existing
    one), which is folded out of the frame's refillable pools. The
    header is ``max(block_execution, block_state)``:

    * REVERT -- the unused execution budget returns, so the execution
      component is ``intrinsic_execution + top_frame_execution +
      evm_execution`` and the state component is the persisting
      authorization state gas.
    * HALT / OOG -- the frame consumes its whole gas limit; the
      authorization state gas within it is accounted on the state
      component, and the remainder on the execution component.
    """
    gas_limit = 500_000

    delegate = pre.deploy_contract(code=Op.STOP)

    if failure_mode == "revert":
        revert_code = Op.REVERT(0, 0)
        target = pre.deploy_contract(code=revert_code)
    elif failure_mode == "halt":
        target = pre.deploy_contract(code=Op.INVALID)
    else:
        # Consume all remaining gas at once (a spin loop would execute
        # millions of ops in the EVM and slow down filling).
        target = pre.deploy_contract(code=Om.OOG)

    if authority_exists:
        signer = pre.fund_eoa()
        creates_account = False
    else:
        signer = pre.fund_eoa(amount=0)
        creates_account = True

    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=signer,
            creates_account=creates_account,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )

    if failure_mode == "revert":
        # The authorization's state gas persists with its delegation.
        _, expected_gas_used = _receipt_and_header(
            intrinsic_execution,
            top_frame_execution,
            top_frame_state,
            evm_execution=revert_code.execution_cost(fork),
        )
    else:
        # HALT / OOG consume the whole gas limit, of which the
        # persisting authorization state gas is accounted on the state
        # component and the remainder on the execution component.
        expected_gas_used = max(gas_limit - top_frame_state, top_frame_state)

    tx = Transaction(
        ty=4,
        to=target,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        authorization_list=authorization_list,
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(delegate)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "authority_exists",
    [
        pytest.param(False, id="new_account"),
        pytest.param(True, id="existing_account"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_auth_sender_billing_after_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    authority_exists: bool,
) -> None:
    """
    Verify sender billing distinguishes new vs existing authority on a
    top-level REVERT.

    The delegation persists through the REVERT, so the state gas that
    paid for it stays billed alongside the execution gas: the sender pays
    ``intrinsic_execution + top_frame_execution + revert_execution`` plus the
    authorization's state charges. Both authorities pay the first-write
    ``ACCOUNT_WRITE`` and the ``AUTH_BASE``; a new authority
    additionally pays ``NEW_ACCOUNT`` for the created leaf, so its
    sender pays exactly ``NEW_ACCOUNT`` more than the
    existing-authority case.
    """
    delegate = pre.deploy_contract(code=Op.STOP)
    revert_code = Op.REVERT(0, 0)
    target = pre.deploy_contract(code=revert_code)

    if authority_exists:
        signer = pre.fund_eoa()
        creates_account = False
    else:
        signer = pre.fund_eoa(amount=0)
        creates_account = True

    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=signer,
            creates_account=creates_account,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    # The authorization's state gas persists with its delegation across
    # the REVERT and stays billed to the sender.
    expected_cumulative, header_gas_used = _receipt_and_header(
        intrinsic_execution,
        top_frame_execution,
        top_frame_state,
        evm_execution=revert_code.execution_cost(fork),
    )

    tx = Transaction(
        ty=4,
        to=target,
        sender=pre.fund_eoa(),
        authorization_list=authorization_list,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(delegate)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "inner_shape",
    [
        pytest.param("burned_child_spill", id="burned_child_spill"),
        pytest.param("revoked_advance", id="revoked_advance"),
    ],
)
@pytest.mark.valid_from("EIP8037")
@pytest.mark.parametrize(
    "authority_exists", [False, True], ids=["new", "existing"]
)
def test_top_level_halt_keeps_intrinsic_auth_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    inner_shape: str,
    authority_exists: bool,
) -> None:
    """
    Verify a top-level exceptional halt keeps the full authorization
    state gas in the state dimension while the burned child spill stays
    in the execution dimension: the header reports
    ``max(gas_limit - auth_state, auth_state)`` regardless of the
    spill shape burned inside the halted frame.

    The tx gas limit sits below the EIP-7825 cap, so the reservoir is
    empty and every state charge inside the halted frame spills from
    `gas_left`.
    """
    gas_limit = 1_000_000

    if inner_shape == "burned_child_spill":
        inner = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.INVALID)
    else:
        inner = revoked_advance_call_tree(pre)

    recipient = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=inner)) + Op.INVALID,
    )

    delegate = pre.deploy_contract(code=Op.STOP)
    signer = pre.fund_eoa() if authority_exists else pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=signer,
            creates_account=not authority_exists,
            writes_delegation=True,
        ),
    ]
    _, _, auth_state_gas = _auth_gas(fork, authorization_list)

    # The halt consumes the whole limit: the execution and state
    # dimensions sum to `gas_limit` however the split falls.
    tx = Transaction(
        ty=4,
        to=recipient,
        gas_limit=gas_limit,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            status=0,
            cumulative_gas_used=gas_limit,
        ),
    )

    post = {
        signer: Account(
            nonce=1, code=Spec7702.delegation_designation(delegate)
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(gas_limit - auth_state_gas, auth_state_gas)
        ),
    )


@pytest.mark.parametrize(
    "gas_delta",
    [
        pytest.param(0, id="exact_fit"),
        pytest.param(-1, id="one_short"),
    ],
)
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_auth_and_execution_state_oog_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Verify the top-frame + execution state gas OOG boundary.

    A set_code tx delegates an existing authority (top-frame
    ``AUTH_BASE``) to a recipient that performs a zero-to-nonzero SSTORE.
    All state charges draw from ``gas_left`` (there is no reservoir to
    fund them). At exactly the total cost the SSTORE lands and the storage
    is written; one gas short, the execution runs out of gas at the top
    frame, the storage change rolls back, and the transaction consumes its
    whole gas limit. The delegation, applied in the earlier preparation
    snapshot, persists in both cases.
    """
    storage = Storage()
    target_code = Op.SSTORE(storage.store_next(1), 1)
    target = pre.deploy_contract(code=target_code)
    evm_execution = target_code.execution_cost(fork)
    evm_state = target_code.state_cost(fork)

    authority = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=target,
            nonce=0,
            signer=authority,
            creates_account=False,
            writes_delegation=True,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    full_cost = (
        intrinsic_execution
        + top_frame_execution
        + top_frame_state
        + evm_execution
        + evm_state
    )
    gas_limit = full_cost + gas_delta
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    assert gas_limit <= gas_limit_cap

    fits = gas_delta >= 0
    if fits:
        _, header_gas_used = _receipt_and_header(
            intrinsic_execution,
            top_frame_execution,
            top_frame_state,
            evm_execution=evm_execution,
            evm_state=evm_state,
        )
    else:
        # One gas short: execution OOGs at the top frame, consuming the
        # whole gas limit; the SSTORE rolls back (its state gas is
        # refilled) while the delegation persists, so its AUTH_BASE is
        # accounted on the block's state component.
        header_gas_used = max(gas_limit - top_frame_state, top_frame_state)

    tx = Transaction(
        to=target,
        gas_limit=gas_limit,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        target: Account(storage=storage if fits else {}),
        authority: Account(code=Spec7702.delegation_designation(target)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.parametrize(
    "invalidity",
    [
        pytest.param("nonce_mismatch", id="nonce_mismatch"),
        pytest.param("nonce_at_u64_max", id="nonce_at_u64_max"),
        pytest.param("chain_id_mismatch", id="chain_id_mismatch"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_invalid_auth_no_top_frame_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    invalidity: str,
) -> None:
    """
    Verify a rejected authorization incurs no top-frame charge.

    A rejected authorization is skipped during ``set_delegation``, so it
    writes no delegation indicator and creates no account: it incurs
    neither ``NEW_ACCOUNT`` / ``ACCOUNT_WRITE`` nor ``AUTH_BASE`` at the
    top frame (and, unlike the superseded EIP-8037 model, nothing is
    refilled because nothing was charged). Only the intrinsic
    ``EXECUTION_PER_AUTH_BASE_COST`` is paid and the authority is never
    created. Swept over the reasons an authorization is rejected.
    """
    target = pre.deploy_contract(code=Op.STOP)
    signer = pre.fund_eoa(amount=0)

    if invalidity == "nonce_mismatch":
        auth = AuthorizationTuple(
            address=target,
            nonce=99,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        )
    elif invalidity == "nonce_at_u64_max":
        auth = AuthorizationTuple(
            address=target,
            nonce=2**64 - 1,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        )
    elif invalidity == "chain_id_mismatch":
        auth = AuthorizationTuple(
            address=target,
            nonce=0,
            chain_id=9999,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        )
    else:
        raise ValueError(f"unknown invalidity: {invalidity!r}")

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, [auth]
    )
    assert top_frame_execution == 0
    assert top_frame_state == 0
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=target,
        authorization_list=[auth],
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    state_test(
        pre=pre,
        post={signer: Account.NONEXISTENT},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_same_tx_create_then_clear(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a create-then-clear on one authority in a single transaction.

    A fresh authority is delegated by the first authorization then cleared
    by the second. The first charges ``NEW_ACCOUNT`` + ``ACCOUNT_WRITE``
    (leaf creation and first write) and ``AUTH_BASE`` (net-new
    indicator); the second clears the delegation the first set. The
    ``AUTH_BASE`` is charged at most once per authority and never
    credited back, so it stays paid even though the authority ends the
    transaction with empty code and nonce 2.
    """
    contract_a = pre.deploy_contract(code=Op.STOP)
    target = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=contract_a,
            nonce=0,
            signer=signer,
            creates_account=True,
            writes_delegation=True,
        ),
        AuthorizationTuple(
            address=Spec7702.RESET_DELEGATION_ADDRESS,
            nonce=1,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=target,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    state_test(
        pre=pre,
        post={signer: Account(nonce=2, balance=0, code=b"")},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_same_tx_clear_then_reset_pre_delegated(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a clear-then-reset of a pre-delegated authority in one tx.

    An authority delegated before the transaction is cleared by the first
    authorization then re-delegated to a new target by the second. Because
    the authority was already delegated before the transaction, neither
    authorization writes a net-new delegation indicator: no ``AUTH_BASE``
    is charged and, as the leaf already exists, no ``NEW_ACCOUNT``
    either. The clear is the transaction's first write to the leaf, so
    one ``ACCOUNT_WRITE`` is paid on top of the intrinsic
    per-authorization bases. The authority ends delegated to the new
    target with nonce 3.
    """
    contract_a = pre.deploy_contract(code=Op.STOP)
    contract_b = pre.deploy_contract(code=Op.STOP)
    target = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa(delegation=contract_a)
    authorization_list = [
        AuthorizationTuple(
            address=Spec7702.RESET_DELEGATION_ADDRESS,
            nonce=1,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
        ),
        AuthorizationTuple(
            address=contract_b,
            nonce=2,
            signer=signer,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        ),
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    assert top_frame_state == 0
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=target,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    state_test(
        pre=pre,
        post={
            signer: Account(
                nonce=3,
                code=Spec7702.delegation_designation(contract_b),
            ),
        },
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_same_authority_increasing_nonce_net_once(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the per-authority once invariant across valid auths.

    The same fresh authority is delegated by three authorizations with
    increasing nonces in one transaction. The account leaf is created and
    first written once (``NEW_ACCOUNT`` + ``ACCOUNT_WRITE`` on the first
    authorization) and a net-new delegation indicator is written once
    (``AUTH_BASE`` on the first). The later authorizations re-point an
    already-written, already-delegated authority, so they add nothing
    beyond the intrinsic base. The authority ends delegated to the last
    target with nonce 3.
    """
    num_auths = 3
    targets = [pre.deploy_contract(code=Op.STOP) for _ in range(num_auths)]
    call_target = pre.deploy_contract(code=Op.STOP)

    signer = pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=targets[i],
            nonce=i,
            signer=signer,
            creates_account=(i == 0),
            writes_delegation=(i == 0),
            first_write=(i == 0),
        )
        for i in range(num_auths)
    ]

    intrinsic_execution, top_frame_execution, top_frame_state = _auth_gas(
        fork, authorization_list
    )
    cumulative_gas_used, header_gas_used = _receipt_and_header(
        intrinsic_execution, top_frame_execution, top_frame_state
    )

    tx = Transaction(
        to=call_target,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    state_test(
        pre=pre,
        post={
            signer: Account(
                nonce=num_auths,
                balance=0,
                code=Spec7702.delegation_designation(targets[-1]),
            ),
        },
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=header_gas_used),
    )
