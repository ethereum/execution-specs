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
    EOA,
    SECP256K1_SIGNATURE_LENGTH,
    Account,
    Address,
    Alloc,
    Bytecode,
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
from .helpers import FrameCase, FrameTransaction, default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

BASE_FEE = 7
"""Base fee of the block every transaction lands in."""

PRIORITY_FEE = 5
"""Tip per gas each transaction asks for."""

FUNDS = 10**18
"""Sender balance before the transaction, which pays and escrows."""

PROBE_GAS = 100_000
"""Execution budget of a probe frame that stores what it reads."""

PROBE_STATE_GAS = 1_000_000
"""State budget of a probe frame, covering the slot it creates."""


def worst_case(
    fork: Fork,
    sender: EOA,
    frames: List[FrameCase],
    blob_count: int = 0,
    excess_blob_gas: int = 0,
) -> tuple[int, int]:
    """
    Return the transaction's `max_gas` and the fee its `max_fee` must
    cover, `max_gas` at the base fee plus the blob gas at the blob base
    fee of `excess_blob_gas`.

    The sender's default signature entry has an empty `msg`, so only its
    length enters the intrinsic cost and the entry can be priced before
    it is signed.
    """
    signature = FrameSignature(
        scheme=Spec.SCHEME_SECP256K1,
        signer=Bytes(sender),
        signature=Bytes(bytes(SECP256K1_SIGNATURE_LENGTH)),
    )
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, signatures=[signature]
    )
    blob_gas = blob_count * fork.blob_gas_per_blob()
    blob_base_fee = fork.blob_gas_price_calculator()(
        excess_blob_gas=excess_blob_gas
    )
    return max_gas, max_gas * BASE_FEE + blob_gas * blob_base_fee


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
    _, required_max_fee = worst_case(fork, sender, frames, blob_count)

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
    max_gas, required_max_fee = worst_case(fork, sender, frames)
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
    max_gas, required_max_fee = worst_case(fork, sender, frames)
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
    max_gas, _ = worst_case(fork, sender, frames)
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
    _, required_max_fee = worst_case(
        fork, sender, frames, blob_count, excess_blob_gas
    )
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


OVERFLOWING_PRIORITY_FEE = 2**255
"""
A tip per gas whose product with any even gas amount is a multiple of
2**256, so arithmetic that wraps at 256 bits computes a zero tip.
"""

TIP_BUDGET = 10**15
"""
What `max_fee` holds beyond the worst case at the base fee: the whole
tip the transaction can pay when its tip per gas is unbounded.
"""


def test_priority_fee_product_exceeds_256_bits(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Cap a tip per gas of 2**255 by the budget, both at the escrow and at
    settlement, computing the products over unbounded integers.

    EIP-8141 "Fee budget": "`max_priority_fee = min(
    tx.fees.max_priority_fee_per_gas * max_gas, tx.fees.max_fee -
    required_max_fee)`" and "`GASPRICE` returns `base_fee_per_gas +
    max_priority_fee // max_gas`"; "Transaction settlement":
    "`priority_fee_paid = min(tx.fees.max_priority_fee_per_gas *
    gas_used, max_cost - base_fee_paid)`". The field only has to be
    below 2**256, and the EIP's integers do not wrap.

    Both products exceed 2**256, so each `min` takes the budget side:
    the escrow is the whole `max_fee`, `GASPRICE` is the base fee plus
    `TIP_BUDGET // max_gas`, the coinbase receives everything the
    escrow holds after the base fee on the gas used is burned, and the
    payer gets nothing back. `max_gas` and the gas used are both even,
    so a product wrapped at 256 bits is zero: a client wrapping the
    escrow's product reports `GASPRICE` as the bare base fee, and one
    wrapping the settlement's product pays the coinbase nothing.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    # The probe overwrites a non-zero slot, so it creates no state.
    probe_store = Op.SSTORE(
        0,
        Op.GASPRICE,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=2,
    )
    verify_gas = fork.frame_entry_gas_calculator()(target_warm=True)
    probe_entry_gas = fork.frame_entry_gas_calculator()(target_warm=False)
    # The intrinsic cost does not depend on the frame budgets or the
    # probe's address, so it fixes the parity of the gas used up front.
    intrinsic = standard_gas_limit(
        fork,
        sender,
        [
            verify_frame(gas_limit=0, state_gas_limit=0),
            default_frame(gas_limit=0, state_gas_limit=0),
        ],
    )
    unpadded_gas_used = (
        intrinsic
        + verify_gas
        + probe_entry_gas
        + (probe_store + Op.STOP).execution_cost(fork)
    )
    # One extra gas makes an odd gas used even.
    probe_code = Op.JUMPDEST * (unpadded_gas_used % 2) + probe_store + Op.STOP
    probe = pre.deploy_contract(code=probe_code, storage={0: 1})
    probe_gas = probe_entry_gas + probe_code.execution_cost(fork)
    frames = [
        verify_frame(gas_limit=verify_gas, state_gas_limit=0),
        # An even amount of unused gas keeps `max_gas` even.
        default_frame(
            target=probe,
            code=probe_code,
            gas_limit=probe_gas + 10,
            state_gas_limit=0,
        ),
    ]
    max_gas, required_max_fee = worst_case(fork, sender, frames)
    max_cost = required_max_fee + TIP_BUDGET
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=frames,
        max_fee=max_cost,
        max_priority_fee_per_gas=OVERFLOWING_PRIORITY_FEE,
    )
    gas_used = tx.payer_gas_used()
    # The premises: the floor does not bind, both gas amounts are even,
    # and both products exceed 2**256.
    assert not tx.floor_binds()
    assert max_gas % 2 == 0 and gas_used % 2 == 0
    assert OVERFLOWING_PRIORITY_FEE * gas_used >= 2**256
    tip = max_cost - gas_used * BASE_FEE

    env = Environment(base_fee_per_gas=BASE_FEE)
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=FUNDS - max_cost),
            env.fee_recipient: Account(balance=tip),
            probe: Account(storage={0: BASE_FEE + TIP_BUDGET // max_gas}),
        },
    )


FLOOR_BRANCH_DATA = bytes(1_000)
"""
Zero bytes of frame data: cheap at the standard token rate, but priced
at the floor rate per byte whatever their value, so the calldata floor
far exceeds the intrinsic cost plus the small execution budgets.
"""

FLOOR_BRANCH_STATE_GAS = 100_000
"""State budget of the probe frame, added to both sides of `max_gas`."""


def floor_branch_frames(
    fork: Fork, target: Address, target_code: Bytecode
) -> List[FrameCase]:
    """
    Return frames whose `max_gas` is the calldata floor plus the state
    budgets, not the standard gas limit.
    """
    target_gas = fork.frame_entry_gas_calculator()(
        target_warm=False
    ) + target_code.execution_cost(fork)
    return [
        verify_frame(
            gas_limit=fork.frame_entry_gas_calculator()(target_warm=True),
            state_gas_limit=0,
        ),
        default_frame(
            target=target,
            gas_limit=target_gas,
            state_gas_limit=FLOOR_BRANCH_STATE_GAS,
            data=FLOOR_BRANCH_DATA,
        ),
    ]


def standard_gas_limit(
    fork: Fork, sender: EOA, frames: List[FrameCase]
) -> int:
    """
    Return the intrinsic cost plus every frame budget: the first operand
    of `max_gas`.
    """
    signature = FrameSignature(
        scheme=Spec.SCHEME_SECP256K1,
        signer=Bytes(sender),
        signature=Bytes(bytes(SECP256K1_SIGNATURE_LENGTH)),
    )
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames,
        signatures=[signature],
        return_cost_deducted_prior_execution=True,
    )
    return intrinsic + sum(
        int(frame.gas_limit) + int(frame.state_gas_limit) for frame in frames
    )


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
def test_max_fee_boundary_floor_branch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    budget_delta: int,
) -> None:
    """
    Require `max_fee` to cover the calldata floor plus the state budgets
    when that exceeds the standard gas limit.

    EIP-8141 "Gas Accounting": "`max_gas = max(standard_gas_limit,
    calldata_floor_gas + sum(frame.limits.state for frame in
    tx.frames))`"; "Fee budget": "The transaction is invalid if
    `tx.fees.max_fee < required_max_fee`".

    The frame data is zero bytes, priced 4 gas each in the intrinsic
    cost but 64 gas each in the floor, so the floor operand wins by tens
    of thousands of gas. A `max_fee` of exactly that `max_gas` at the
    base fee is admitted; one wei less is rejected, which a client
    pricing only the standard gas limit admits.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    target = pre.deploy_contract(code=Op.STOP)
    frames = floor_branch_frames(fork, target, Op.STOP)
    max_gas, required_max_fee = worst_case(fork, sender, frames)
    # The premise: the floor operand of `max_gas` is the larger one.
    assert max_gas > standard_gas_limit(fork, sender, frames)

    tx = Transaction(
        sender=sender,
        max_fee=required_max_fee + budget_delta,
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


def test_gasprice_floor_branch_divisor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Divide the tip budget by the floor-branch `max_gas` in `GASPRICE`.

    EIP-8141 "Fee budget": "`GASPRICE` returns `base_fee_per_gas +
    max_priority_fee // max_gas`", where `max_gas` is the floor operand
    here (see `test_max_fee_boundary_floor_branch`).

    The budget beyond the worst case is one wei short of two wei per
    unit of `max_gas`, so `GASPRICE` is the base fee plus one. Divided
    by the smaller standard gas limit, the same budget would report the
    base fee plus two.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    probe = pre.deploy_contract(code=Op.SSTORE(0, Op.GASPRICE) + Op.STOP)
    frames = floor_branch_frames(
        fork, probe, Op.SSTORE(0, Op.GASPRICE) + Op.STOP
    )
    max_gas, required_max_fee = worst_case(fork, sender, frames)
    tip_budget = 2 * max_gas - 1
    # The premise: the standard gas limit would report a larger tip.
    assert tip_budget // standard_gas_limit(fork, sender, frames) >= 2

    tx = Transaction(
        sender=sender,
        max_fee=required_max_fee + tip_budget,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=frames,
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={probe: Account(storage={0: BASE_FEE + 1})},
    )
