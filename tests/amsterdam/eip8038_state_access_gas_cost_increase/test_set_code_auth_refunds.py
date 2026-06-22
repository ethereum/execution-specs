"""
Tests for the EIP-7702 authorization *regular*-gas refund under
[EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

When an authority's account leaf already exists, ``set_delegation``
refunds on two independent channels:

* the **state** channel: ``StateGasCosts.NEW_ACCOUNT`` is refilled into
  ``state_gas_reservoir`` / ``state_refund`` (and ``AUTH_BASE`` too when
  the code slot already holds a delegation indicator). It is subtracted
  from ``tx_state_gas`` *before* the regular refund is applied and is
  **not** subject to the EIP-3529 one-fifth cap. This channel is the
  subject of the EIP-8037 ``eip8037_state_creation_gas_cost_increase``
  suite.
* the **regular** channel: the worst-case ``GasCosts.ACCOUNT_WRITE``
  charged in the regular intrinsic is returned via the regular refund
  counter, and **is** subject to the one-fifth cap.

This module pins the *regular* ``ACCOUNT_WRITE`` refund. The dual-channel
accounting mirrors ``process_transaction``:

    gas_before_regular_refund = (
        intrinsic_regular + exec_regular
        + intrinsic_state + exec_state
        - state_refund            # uncapped, subtracted first
    )
    regular_refund = min(
        n * ACCOUNT_WRITE,
        gas_before_regular_refund // fork.max_refund_quotient(),
    )
    cumulative_gas_used = gas_before_regular_refund - regular_refund

Two regimes are exercised:

* a non-clearing delegation on an existing leaf, padded with cold
  SSTOREs so ``gas_before_regular_refund`` is large and the full
  ``n * ACCOUNT_WRITE`` clears under the cap; and
* a *clearing* re-authorization of an existing-delegation authority,
  where the state channel refunds the **full** per-auth state intrinsic
  (``NEW_ACCOUNT + AUTH_BASE``). That collapses
  ``gas_before_regular_refund`` to the regular intrinsic alone, so the
  cap ``gas // 5`` becomes the binding term and the regular refund
  clamps below ``ACCOUNT_WRITE``.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _sstore_state_per_op(fork: Fork) -> int:
    """Return the state gas of one cold ``0 -> 1`` SSTORE."""
    return Op.SSTORE(new_value=1).state_cost(fork)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.parametrize("n", [1, 2])
def test_existing_authority_regular_refund_visible(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    n: int,
) -> None:
    """
    Pin the full regular ``ACCOUNT_WRITE`` refund for set-code
    authorizations whose authority leaves already exist.

    Each authority is an existing funded EOA delegating to a fresh
    contract, so ``set_delegation`` refunds ``NEW_ACCOUNT`` on the state
    channel (uncapped) and ``ACCOUNT_WRITE`` on the regular channel
    (capped). The execution is padded with ten cold ``0 -> 1`` SSTOREs
    so ``gas_before_regular_refund`` is large and the one-fifth cap
    exceeds ``n * ACCOUNT_WRITE``; the entire regular refund is visible
    in the receipt.

    The state refill is subtracted first and is not capped; it belongs
    to the EIP-8037 suite and is only used here to size the receipt.
    """
    gas_costs = fork.gas_costs()
    account_write = gas_costs.ACCOUNT_WRITE
    # Existing leaf overwritten with a fresh (non-clearing) delegation
    # indicator: only NEW_ACCOUNT is refilled on the state channel.
    state_refund = gas_costs.REFUND_AUTH_PER_EXISTING_ACCOUNT * n

    total_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=n,
    )
    intrinsic_state = fork.transaction_intrinsic_state_gas(
        authorization_count=n,
    )

    num_sstores = 10
    storage = Storage()
    code = Bytecode()
    for _ in range(num_sstores):
        code += Op.SSTORE(storage.store_next(1), 1)
    code += Op.STOP
    contract = pre.deploy_contract(code=code)

    exec_state = _sstore_state_per_op(fork) * num_sstores
    # The deployed bytecode's combined cost minus its state portion is
    # the regular execution gas (includes the PUSHes for SSTORE args).
    exec_regular = code.gas_cost(fork) - exec_state

    delegate = pre.deploy_contract(code=Op.STOP)
    signers = [pre.fund_eoa() for _ in range(n)]
    authorization_list = [
        AuthorizationTuple(address=delegate, nonce=0, signer=signer)
        for signer in signers
    ]

    gas_before_regular_refund = (
        total_intrinsic + exec_regular + exec_state - state_refund
    )
    regular_refund = min(
        n * account_write,
        gas_before_regular_refund // fork.max_refund_quotient(),
    )
    assert regular_refund == n * account_write
    cumulative_gas_used = gas_before_regular_refund - regular_refund

    tx = Transaction(
        to=contract,
        state_gas_reservoir=intrinsic_state + exec_state,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post: dict = {contract: Account(storage=storage)}
    for signer in signers:
        post[signer] = Account(
            code=Spec7702.delegation_designation(delegate),
        )
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.parametrize("n", [1, 3])
def test_clearing_delegation_regular_refund_capped(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    n: int,
) -> None:
    """
    Clearing a delegation refunds the full per-auth state intrinsic on
    the state channel, which drives the regular refund into the
    one-fifth cap.

    Each authority already holds a delegation and re-authorizes to the
    reset (zero) address, clearing its code. The leaf exists, so
    ``ACCOUNT_WRITE`` is refunded on the regular channel; the code slot
    held a delegation indicator and the new indicator is empty, so both
    ``NEW_ACCOUNT`` and ``AUTH_BASE`` are refilled on the state channel.
    Refunding the full per-auth state intrinsic collapses
    ``gas_before_regular_refund`` to the regular intrinsic alone, so the
    cap ``gas // 5`` is below ``n * ACCOUNT_WRITE`` and the regular
    refund clamps to ``gas // 5`` (cap-saturated). No execution padding
    is used, so the contrast with the full-refund test is purely the
    refunded state magnitude.
    """
    gas_costs = fork.gas_costs()
    account_write = gas_costs.ACCOUNT_WRITE

    total_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=n,
    )
    intrinsic_state = fork.transaction_intrinsic_state_gas(
        authorization_count=n,
    )
    # Clearing an existing delegation refills the full per-auth state
    # intrinsic (NEW_ACCOUNT + AUTH_BASE) for every authorization.
    state_refund = intrinsic_state

    contract = pre.deploy_contract(code=Op.STOP)
    delegated_to = pre.deploy_contract(code=Op.STOP)
    # Authorities that already delegate; fund_eoa(delegation=...) sets
    # the authority nonce to 1, which is the expected auth nonce.
    signers = [pre.fund_eoa(delegation=delegated_to) for _ in range(n)]
    authorization_list: List[AuthorizationTuple] = [
        AuthorizationTuple(
            address=Spec7702.RESET_DELEGATION_ADDRESS,
            nonce=1,
            signer=signer,
        )
        for signer in signers
    ]

    gas_before_regular_refund = total_intrinsic - state_refund
    regular_refund = min(
        n * account_write,
        gas_before_regular_refund // fork.max_refund_quotient(),
    )
    # The cap is the binding term: the refund clamps below ACCOUNT_WRITE.
    assert regular_refund < n * account_write
    assert regular_refund == gas_before_regular_refund // (
        fork.max_refund_quotient()
    )
    cumulative_gas_used = gas_before_regular_refund - regular_refund

    tx = Transaction(
        to=contract,
        state_gas_reservoir=intrinsic_state,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post: dict = {}
    for signer in signers:
        # Delegation cleared back to empty code, nonce incremented.
        post[signer] = Account(nonce=2, code=b"")
    state_test(env=env, pre=pre, post=post, tx=tx)
