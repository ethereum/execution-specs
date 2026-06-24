"""
EIP-2780 probe: warm/cold-aware top-frame delegation resolution.

EIP-2780 is internally inconsistent about the regular-gas charge for
resolving an EIP-7702 delegation at the top transaction frame:

- The normative "Transaction's top-level gas costs" bullet and the
  reference-cases table charge an unconditional ``COLD_ACCOUNT_ACCESS``
  (``TX_BASE_COST + 2 * COLD_ACCOUNT_ACCESS``).
- The "Interactions" note says the delegation target is charged
  ``COLD_ACCOUNT_ACCESS`` on first touch or warm thereafter, following
  the standard EIP-2929 ``accessed_addresses`` model (warm/cold-aware).

``test_warmth_invariants.py`` pins the first reading: the access list
does not waive the cold charge. This module pins the second: when the
delegation target is already warm (listed in the access list), the
top-frame resolution should cost ``WARM_ACCESS`` instead of
``COLD_ACCOUNT_ACCESS``.

The implementation charges the cold rate unconditionally
(``interpreter.py`` charges ``GasCosts.COLD_ACCOUNT_ACCESS`` before
adding the target to ``accessed_addresses``), so this test is
``xfail(strict=True)``: it flips to passing once the contradiction is
resolved in favour of the warm/cold-aware reading and the spec adopts
it, at which point ``strict`` forces the marker's removal.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.xfail(
    strict=True,
    reason="EIP-2780 charges COLD_ACCOUNT_ACCESS unconditionally at the "
    "top frame; the Interactions note requires WARM_ACCESS for an "
    "access-listed (warm) delegation target. Pending disambiguation.",
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_delegation_in_access_list_is_warm(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation whose target is
    in the access list, so the target is warm when the top frame
    resolves it. Under the EIP-2929 warm/cold-aware reading the
    resolution costs ``WARM_ACCESS`` rather than
    ``COLD_ACCOUNT_ACCESS``: the sole difference from
    ``test_top_frame_charges_delegation_in_access_list`` is that one
    constant, a 2,900 gas swing.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = pre.deploy_contract(code=Op.STOP)
    target_code = Spec7702.delegation_designation(delegated_to)
    target = pre.deploy_contract(code=target_code)
    access_list = [AccessList(address=delegated_to, storage_keys=[])]

    gas_costs = fork.gas_costs()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    cold_top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
    )
    # Warm/cold-aware reading: the access-listed delegation target
    # resolves warm, so the top frame should charge WARM_ACCESS in
    # place of the calculator's unconditional COLD_ACCOUNT_ACCESS.
    warm_top_frame_gas = (
        cold_top_frame_gas
        - gas_costs.COLD_ACCOUNT_ACCESS
        + gas_costs.WARM_ACCESS
    )

    gas_price = 1_000_000_000
    # Budget the worst case (cold) so the transaction always runs to
    # completion; the warm/cold discrepancy then surfaces purely as the
    # sender's gas balance instead of an out-of-gas halt.
    gas_limit = intrinsic_gas + cold_top_frame_gas + 1000

    expected_gas_used = intrinsic_gas + warm_top_frame_gas

    tx = Transaction(
        ty=1,
        sender=sender,
        to=target,
        value=value,
        access_list=access_list,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - expected_gas_used * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=value, code=target_code),
    }

    state_test(pre=pre, tx=tx, post=post)
