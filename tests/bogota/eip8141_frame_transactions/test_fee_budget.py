"""
Test the `max_fee` budget of a frame transaction.

A single `max_fee` caps the transaction's total payment for its execution,
state, and blob gas. It must cover the worst case at the block's base fees,
`max_gas` at the base fee plus the blob gas at the blob base fee. The payer
escrows that worst case plus the largest tip the rest of the budget allows,
and at settlement the gas used is burned at the base fee while the coinbase
receives the tip per gas on the gas used, capped by what the escrow still
holds.
"""

from typing import List

import pytest
from execution_testing import (
    SECP256K1_SIGNATURE_LENGTH,
    Account,
    Alloc,
    Bytes,
    Environment,
    Fork,
    FrameSignature,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import SpecHelpers as BlobSpecHelpers
from .helpers import (
    BASE_FEE,
    PRIORITY_FEE,
    default_frame,
    fee_budget,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

FUNDS = 10**18
"""Sender balance before the transaction, which pays and escrows."""

PROBE_GAS = 100_000
"""Execution budget of a probe frame that stores what it reads."""

PROBE_STATE_GAS = 1_000_000
"""State budget of a probe frame, covering the slot it creates."""


def blob_versioned_hashes(count: int) -> List[Hash]:
    """Return `count` versioned hashes for the transaction to carry."""
    return add_kzg_version(list(range(1, count + 1)), 1)


@pytest.mark.parametrize(
    "budget_delta",
    [
        pytest.param(0, id="exact"),
        pytest.param(
            -1,
            id="one_below",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.parametrize(
    "blob_count",
    [
        pytest.param(0, id="no_blobs"),
        pytest.param(1, id="one_blob"),
    ],
)
def test_max_fee_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_count: int,
    budget_delta: int,
) -> None:
    """
    Admit a transaction whose `max_fee` covers exactly its worst case,
    blob gas included, and reject one a wei short of it.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    target = pre.deploy_contract(code=Op.STOP)
    frames = [verify_frame(state_gas_limit=0), default_frame(target=target)]
    required_max_fee = fee_budget(
        fork, sender, frames, blob_count=blob_count
    ).required_max_fee

    tx = Transaction(
        sender=sender,
        max_fee=required_max_fee + budget_delta,
        blob_versioned_hashes=blob_versioned_hashes(blob_count),
        frames=frames,
        error=(
            TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS
            if budget_delta < 0
            else None
        ),
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=0 if budget_delta < 0 else 1)},
    )


@pytest.mark.parametrize(
    "budget",
    [
        pytest.param("full_tip", id="full_tip"),
        pytest.param("no_headroom", id="no_headroom"),
        pytest.param("partial_tip", id="partial_tip"),
        # A budget beyond the worst case plus the full tip is never
        # escrowed in full.
        pytest.param("surplus_budget", id="surplus_budget"),
    ],
)
def test_escrow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    budget: str,
) -> None:
    """
    Escrow the worst case plus the largest tip the budget allows: the
    full tip on `max_gas` when the budget has room for it, and the whole
    budget when it does not, but never more than that worst case plus
    the full tip.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            0, Op.SUB(FUNDS, Op.BALANCE(Op.TXPARAM(Spec.TXPARAM_SENDER)))
        )
        + Op.STOP
    )
    frames = [
        verify_frame(state_gas_limit=0),
        default_frame(
            target=probe,
            gas_limit=PROBE_GAS,
            state_gas_limit=PROBE_STATE_GAS,
        ),
    ]
    fees = fee_budget(fork, sender, frames)
    max_gas, required_max_fee = fees.max_gas, fees.required_max_fee
    full_tip = PRIORITY_FEE * max_gas
    max_fee = {
        "full_tip": required_max_fee + full_tip,
        "no_headroom": required_max_fee,
        "partial_tip": required_max_fee + full_tip // 2,
        "surplus_budget": required_max_fee + 2 * full_tip,
    }[budget]
    escrow = required_max_fee + min(full_tip, max_fee - required_max_fee)
    assert (escrow < max_fee) == (budget == "surplus_budget")

    tx = Transaction(
        sender=sender,
        max_fee=max_fee,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=frames,
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={probe: Account(storage={0: escrow})},
    )


@pytest.mark.parametrize(
    "budget",
    [
        pytest.param("full_tip", id="full_tip"),
        pytest.param("no_headroom", id="no_headroom"),
        pytest.param("partial_tip", id="partial_tip"),
    ],
)
def test_tip_settlement(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    budget: str,
) -> None:
    """
    Pay the coinbase the tip per gas on the gas used, capped by what the
    escrow holds after the base fee on the gas used is burned, and refund
    the payer the rest.

    With no headroom in the budget, only the unused gas the escrow still
    covers at the base fee backs the tip.
    """
    unused_gas = 100
    sender = pre.fund_eoa(amount=FUNDS)
    # Execution well above the calldata floor, so the unused gas is not
    # absorbed by the floor.
    target_code = Op.JUMPDEST * 5_000 + Op.STOP
    target = pre.deploy_contract(code=target_code)
    target_gas = fork.frame_entry_gas_calculator()(
        target_warm=False
    ) + target_code.execution_cost(fork)
    verify_gas = fork.frame_entry_gas_calculator()(target_warm=True)
    frames = [
        verify_frame(gas_limit=verify_gas, state_gas_limit=0),
        default_frame(
            target=target,
            gas_limit=target_gas + unused_gas,
            state_gas_limit=0,
        ),
    ]
    fees = fee_budget(fork, sender, frames)
    max_gas, required_max_fee = fees.max_gas, fees.required_max_fee
    full_tip = PRIORITY_FEE * max_gas
    max_fee = {
        "full_tip": required_max_fee + full_tip,
        "no_headroom": required_max_fee,
        "partial_tip": required_max_fee + full_tip // 2,
    }[budget]
    escrow = required_max_fee + min(full_tip, max_fee - required_max_fee)

    signature = FrameSignature(
        scheme=Spec.SCHEME_SECP256K1,
        signer=Bytes(sender),
        signature=Bytes(bytes(SECP256K1_SIGNATURE_LENGTH)),
    )
    execution_gas = (
        fork.frame_transaction_intrinsic_cost_calculator()(
            frames=frames,
            signatures=[signature],
            return_cost_deducted_prior_execution=True,
        )
        + verify_gas
        + target_gas
    )
    calldata_floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=frames, signatures=[signature]
    )
    assert execution_gas > calldata_floor
    gas_used = execution_gas
    assert gas_used == max_gas - unused_gas
    base_fee_paid = gas_used * BASE_FEE
    tip = min(PRIORITY_FEE * gas_used, escrow - base_fee_paid)
    # The premise of each case: only the full budget pays the whole tip.
    assert (tip == PRIORITY_FEE * gas_used) == (budget == "full_tip")

    tx = Transaction(
        sender=sender,
        max_fee=max_fee,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=frames,
    )

    env = Environment(base_fee_per_gas=BASE_FEE)
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=FUNDS - base_fee_paid - tip),
            env.fee_recipient: Account(balance=tip),
        },
    )


@pytest.mark.parametrize(
    "budget",
    [
        pytest.param("full_tip", id="full_tip"),
        pytest.param("no_headroom", id="no_headroom"),
        pytest.param("one_wei_per_gas", id="one_wei_per_gas"),
        pytest.param("surplus_budget", id="surplus_budget"),
    ],
)
@pytest.mark.parametrize(
    "blob_count",
    [
        pytest.param(0, id="no_blobs"),
        pytest.param(1, id="one_blob"),
    ],
)
def test_gasprice(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    budget: str,
    blob_count: int,
) -> None:
    """
    Report through `GASPRICE` the base fee plus the tip per gas, capped
    by what the budget beyond the worst case pays for every unit of
    `max_gas`, leaving the blob fee out.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    probe = pre.deploy_contract(code=Op.SSTORE(0, Op.GASPRICE) + Op.STOP)
    frames = [
        verify_frame(state_gas_limit=0),
        default_frame(
            target=probe,
            gas_limit=PROBE_GAS,
            state_gas_limit=PROBE_STATE_GAS,
        ),
    ]
    max_gas = fee_budget(fork, sender, frames).max_gas
    # A blob fee of at least a wei per unit of `max_gas`, so folding it
    # into `GASPRICE` would show.
    excess_blob_gas = (
        BlobSpecHelpers.get_min_excess_blob_gas_for_blob_gas_price(
            fork=fork,
            blob_gas_price=max_gas // fork.blob_gas_per_blob() + 1,
        )
        if blob_count
        else 0
    )
    required_max_fee = fee_budget(
        fork,
        sender,
        frames,
        blob_count=blob_count,
        excess_blob_gas=excess_blob_gas,
    ).required_max_fee
    assert required_max_fee - max_gas * BASE_FEE >= blob_count * max_gas
    max_fee, gas_price = {
        "full_tip": (
            required_max_fee + PRIORITY_FEE * max_gas,
            BASE_FEE + PRIORITY_FEE,
        ),
        "no_headroom": (required_max_fee, BASE_FEE),
        # One wei per gas of headroom, short of a gas's worth of the next.
        "one_wei_per_gas": (
            required_max_fee + 2 * max_gas - 1,
            BASE_FEE + 1,
        ),
        # A wei per gas beyond the full tip, which is never reported.
        "surplus_budget": (
            required_max_fee + (PRIORITY_FEE + 1) * max_gas,
            BASE_FEE + PRIORITY_FEE,
        ),
    }[budget]

    tx = Transaction(
        sender=sender,
        max_fee=max_fee,
        max_priority_fee_per_gas=PRIORITY_FEE,
        blob_versioned_hashes=blob_versioned_hashes(blob_count),
        frames=frames,
    )

    state_test(
        env=Environment(
            base_fee_per_gas=BASE_FEE, excess_blob_gas=excess_blob_gas
        ),
        pre=pre,
        tx=tx,
        post={probe: Account(storage={0: gas_price})},
    )
