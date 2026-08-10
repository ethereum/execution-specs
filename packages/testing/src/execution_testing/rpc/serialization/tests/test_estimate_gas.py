"""Test the derivation behind `eth_estimateGas` expectations."""

from typing import Any, Dict

import pytest

from execution_testing import Conditional
from execution_testing.base_types import Account, Address, Bytes, Hash
from execution_testing.forks import Prague
from execution_testing.rpc.serialization.execution import (
    CALL_GAS_LIMIT,
    CallSite,
    UnrunnableCallError,
    _run_message,
    compute_declared_estimate,
    estimate_gas,
)
from execution_testing.test_types import Alloc, Environment
from execution_testing.test_types.account_types import EOA
from execution_testing.vm.opcodes import Opcodes as Op

SENDER = EOA(key=Hash(0x4321))

BYSTANDER = Address(0x0B57)
COINBASE = Address(0xC01B)
WRITES_A_SLOT = Address(0xC0DE)
REVERTS = Address(0xDEAD)
CALLS_AND_CHECKS = Address(0xCA11)
CALLS_AND_IGNORES = Address(0x1607)

BASE_TRANSFER_COST = 21_000
"""The cost of putting a transaction on the chain and doing nothing."""


def make_site(number: int = 0) -> CallSite:
    """Return a site holding a funded sender and a handful of probes."""
    inner_call = Op.CALL(Op.GAS, WRITES_A_SLOT, 0, 0, 0, 0, 0)
    state = Alloc(
        {
            Address(SENDER): Account(balance=10**18, nonce=3),
            BYSTANDER: Account(balance=11),
            COINBASE: Account(balance=1),
            WRITES_A_SLOT: Account(
                balance=0, code=bytes(Op.SSTORE(0x2A, 0x99) + Op.STOP)
            ),
            REVERTS: Account(balance=0, code=bytes(Op.REVERT(0, 0))),
            CALLS_AND_CHECKS: Account(
                balance=0,
                # Reverts unless the callee succeeded, so a limit that
                # starves the callee fails the whole message.
                code=bytes(
                    Conditional(
                        condition=inner_call,
                        if_true=Op.STOP,
                        if_false=Op.REVERT(0, 0),
                    )
                ),
            ),
            CALLS_AND_IGNORES: Account(
                balance=0, code=bytes(Op.POP(inner_call) + Op.STOP)
            ),
        }
    )
    return CallSite(
        number=number,
        state=state,
        environment=Environment(
            fee_recipient=COINBASE,
            number=number,
            timestamp=1_000 + number,
            gas_limit=30_000_000,
            base_fee_per_gas=7,
            excess_blob_gas=0,
            prev_randao=0,
        ),
        fork=Prague,
        chain_id=1,
    )


def derive(to: Address | None, **overrides: Any) -> Any:
    """Estimate a message from the funded sender."""
    arguments: Dict[str, Any] = {
        "sender": Address(SENDER),
        "to": to,
        "data": Bytes(b""),
        "value": 0,
        "gas": CALL_GAS_LIMIT,
    }
    arguments.update(overrides)
    site = arguments.pop("site", make_site())
    return estimate_gas(site, **arguments)


def completes(to: Address, gas: int, data: bytes = b"") -> bool:
    """Return whether the message completes when offered `gas`."""
    try:
        result = _run_message(
            make_site(),
            sender=Address(SENDER),
            to=to,
            data=Bytes(data),
            value=0,
            gas=gas,
        )
    except UnrunnableCallError:
        return False
    return not result.reverted


def test_a_transfer_is_the_base_cost_and_is_pinned_exactly() -> None:
    """
    A message running no code has an answer nothing can search for.

    Every limit the fork admits completes it and every limit below is
    refused outright, so there is only one number a client could report
    and it is the transaction's own base cost.
    """
    outcome = derive(BYSTANDER, value=1)
    assert outcome.minimum == BASE_TRANSFER_COST
    assert outcome.determinate
    assert outcome.assertion == "exact"
    assert outcome.result == hex(BASE_TRANSFER_COST)
    assert outcome.bounds is None


def test_the_boundary_the_exact_tier_rests_on_is_real() -> None:
    """
    One gas less than the answer does not merely run dry: it is refused.

    This is the property the whole `exact` tier is derived from, so it is
    asserted directly rather than through the tier it produces.
    """
    assert completes(BYSTANDER, BASE_TRANSFER_COST)
    assert not completes(BYSTANDER, BASE_TRANSFER_COST - 1)


def test_calldata_raises_the_answer_and_lowers_the_tier() -> None:
    """
    A message carrying data is bounded rather than pinned.

    The specification determines the figure — the data floor, which is
    above what the message would otherwise cost — but go-ethereum
    searches for a message with data instead of short-circuiting it, and
    its search does not land on the least limit that works. The floor is
    still the bottom of the range, so a client charging an older
    per-byte price and answering below it is caught.
    """
    data = bytes([0x00, 0xAB] * 48)
    outcome = derive(BYSTANDER, value=1, data=Bytes(data))
    assert outcome.assertion == "bounds"
    assert outcome.result is None
    assert outcome.bounds == (outcome.minimum, CALL_GAS_LIMIT)
    assert outcome.minimum is not None
    assert outcome.minimum > BASE_TRANSFER_COST
    assert completes(BYSTANDER, outcome.minimum, data)
    assert not completes(BYSTANDER, outcome.minimum - 1, data)


def test_a_contract_call_is_bounded_by_what_it_needs() -> None:
    """
    A message that executes is a range, and the range is tight below.

    The bottom is the least limit at which the message completes, which
    is the strongest lower bound that exists: anything less is a limit
    the message runs out of.
    """
    outcome = derive(WRITES_A_SLOT)
    assert outcome.assertion == "bounds"
    assert outcome.minimum is not None
    assert outcome.minimum > BASE_TRANSFER_COST
    assert completes(WRITES_A_SLOT, outcome.minimum)
    assert not completes(WRITES_A_SLOT, outcome.minimum - 1)


def test_the_answer_can_exceed_what_the_message_spends() -> None:
    """
    A frame passing gas to another needs more than either of them uses.

    Only 63/64ths of what a frame holds may be passed on, so the limit
    the message needs is strictly above the gas it ends up spending —
    which is exactly why an estimate is not an accounting exercise, and
    why a client reporting the gas used would be under-estimating.
    """
    outcome = derive(CALLS_AND_CHECKS)
    spent = _run_message(
        make_site(),
        sender=Address(SENDER),
        to=CALLS_AND_CHECKS,
        data=Bytes(b""),
        value=0,
        gas=CALL_GAS_LIMIT,
    ).gas_used
    assert outcome.minimum is not None
    assert outcome.minimum > spent


def test_the_ceiling_is_the_gas_the_message_names() -> None:
    """
    A client searches within the limit it was given and cannot exceed it.

    The top of the range is therefore the message's own gas rather than
    any figure of ours, and a message naming less has a tighter range for
    free.
    """
    outcome = derive(WRITES_A_SLOT, gas=200_000)
    assert outcome.bounds is not None
    assert outcome.bounds[1] == 200_000


def test_a_reverting_message_has_no_estimate_at_all() -> None:
    """
    No limit completes it, so a client answers with the revert.

    Distinct from every other outcome here: not a weaker assertion about
    a number but the absence of a number, which is why it is stored as an
    error rather than as a range.
    """
    outcome = derive(REVERTS)
    assert outcome.reverted
    assert outcome.minimum is None
    assert outcome.bounds is None
    assert outcome.result is None


def test_a_message_whose_cost_follows_its_limit_derives_nothing() -> None:
    """
    A message that quietly does less on less gas has no honest bound.

    Its callee runs out and the caller ignores the failure, so the
    message still *completes* on a limit that did half the work. The
    limits that complete it need not be contiguous and a client's search
    can legitimately land below anything found here, so no range is
    stored rather than one no client is bound by.
    """
    with pytest.raises(UnrunnableCallError, match="depends on what it is"):
        derive(CALLS_AND_IGNORES)


def test_a_declared_estimate_completes_the_message_it_stores() -> None:
    """
    The stored parameters are the ones executed, not the ones written.

    An author writes the part that carries meaning and the fields that
    only have to agree — the gas and the price — are filled in, since a
    client defaulting either would search over a different message.
    """
    declared = compute_declared_estimate(
        [{"from": str(Address(SENDER)), "to": str(BYSTANDER)}, "0x0"],
        [make_site()],
    )
    assert declared.params[0]["gas"] == hex(CALL_GAS_LIMIT)
    assert declared.params[0]["gasPrice"] == hex(7)
    assert declared.outcome.minimum == BASE_TRANSFER_COST


def test_an_estimate_at_a_block_the_chain_lacks_is_refused() -> None:
    """A message must name a state, and naming one is not enough."""
    with pytest.raises(UnrunnableCallError, match="does not have"):
        compute_declared_estimate(
            [{"from": str(Address(SENDER)), "to": str(BYSTANDER)}, "0x9"],
            [make_site()],
        )
