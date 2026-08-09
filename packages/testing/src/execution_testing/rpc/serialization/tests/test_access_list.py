"""Test the derivation behind `eth_createAccessList` expectations."""

from typing import Any, Dict

import pytest

from execution_testing.base_types import Account, Address, Bytes, Hash
from execution_testing.forks import Amsterdam
from execution_testing.rpc.serialization import compute_result
from execution_testing.rpc.serialization.execution import (
    CALL_GAS_LIMIT,
    CallSite,
    UnrunnableCallError,
    compute_declared_access_list,
    create_access_list,
)
from execution_testing.test_types import Alloc, Environment
from execution_testing.test_types.account_types import EOA
from execution_testing.vm.opcodes import Opcodes as Op

SENDER_KEY = Hash(0x4321)
SENDER = EOA(key=SENDER_KEY)

READS_A_SLOT = Address(0xC0DE)
READS_A_BALANCE = Address(0xBA1A)
CALLS_ANOTHER = Address(0xCA11)
READS_THE_SENDER = Address(0x5E4D)
REVERTS_AFTER_READING = Address(0xDEAD)
HALTS = Address(0xBAD0)
BYSTANDER = Address(0x0B57)
COINBASE = Address(0xC01B)
IDENTITY_PRECOMPILE = Address(4)

SLOT = 0x2A
SLOT_KEY = "0x" + f"{SLOT:064x}"


def make_site(number: int = 0, base_fee: int = 7) -> CallSite:
    """Return a site holding a funded sender and a handful of probes."""
    state = Alloc(
        {
            Address(SENDER): Account(balance=10**18, nonce=3),
            BYSTANDER: Account(balance=11),
            COINBASE: Account(balance=1),
            READS_A_SLOT: Account(
                balance=0,
                code=bytes(Op.POP(Op.SLOAD(SLOT)) + Op.STOP),
                storage={SLOT: 0x99},
            ),
            READS_A_BALANCE: Account(
                balance=0, code=bytes(Op.POP(Op.BALANCE(BYSTANDER)) + Op.STOP)
            ),
            CALLS_ANOTHER: Account(
                balance=0,
                code=bytes(
                    Op.POP(Op.CALL(Op.GAS, READS_A_SLOT, 0, 0, 0, 0, 0))
                    + Op.STOP
                ),
            ),
            READS_THE_SENDER: Account(
                balance=0,
                code=bytes(
                    Op.POP(Op.BALANCE(Address(SENDER)))
                    + Op.POP(Op.BALANCE(COINBASE))
                    + Op.POP(Op.BALANCE(IDENTITY_PRECOMPILE))
                    + Op.STOP
                ),
            ),
            REVERTS_AFTER_READING: Account(
                balance=0,
                code=bytes(Op.POP(Op.SLOAD(SLOT)) + Op.REVERT(0, 0)),
                storage={SLOT: 0x99},
            ),
            HALTS: Account(balance=0, code=bytes(Op.INVALID)),
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
            base_fee_per_gas=base_fee,
            excess_blob_gas=0,
            prev_randao=0,
        ),
        fork=Amsterdam,
        chain_id=1,
    )


def derive(to: Address | None, **overrides: Any) -> Any:
    """Derive the access list for a message from the funded sender."""
    arguments: Dict[str, Any] = {
        "sender": Address(SENDER),
        "to": to,
        "data": Bytes(b""),
        "value": 0,
        "gas": CALL_GAS_LIMIT,
    }
    arguments.update(overrides)
    site = arguments.pop("site", make_site())
    return create_access_list(site, **arguments)


def test_a_transfer_declares_nothing() -> None:
    """
    Both parties to a transfer are warm by rule, so neither is declared.

    The empty list is the strongest assertion in the method: a client
    naming the sender or the recipient here proposes a list that makes
    the message more expensive than sending none at all.
    """
    outcome = derive(BYSTANDER, value=1)
    assert outcome.access_list == []
    assert not outcome.reverted


def test_a_storage_read_declares_the_recipient_with_its_slot() -> None:
    """
    The recipient's address is warm and its slots are not.

    Excluding the recipient outright would drop the one entry that
    matters, because the entry is what makes the slot warm.
    """
    outcome = derive(READS_A_SLOT)
    assert outcome.access_list == [
        {"address": str(READS_A_SLOT), "storageKeys": [SLOT_KEY]}
    ]


def test_a_balance_read_declares_the_account_with_no_slots() -> None:
    """An address touched but never read from carries an empty list."""
    outcome = derive(READS_A_BALANCE)
    assert outcome.access_list == [
        {"address": str(BYSTANDER), "storageKeys": []}
    ]


def test_a_nested_frame_contributes_its_own_entries() -> None:
    """
    An entry names the account whose storage was read.

    Not the account whose code read it: the callee is declared with the
    slot, and the caller — which is the recipient, and warm — is not
    declared at all.
    """
    outcome = derive(CALLS_ANOTHER)
    assert outcome.access_list == [
        {"address": str(READS_A_SLOT), "storageKeys": [SLOT_KEY]}
    ]


def test_the_rule_warmed_addresses_are_never_declared() -> None:
    """
    The sender, the fee recipient and a precompile are all left out.

    Every one is warm from the moment the message starts, so declaring
    any of them costs gas and buys nothing. The probe touches all three
    and the list stays empty, which is what distinguishes "excluded by
    rule" from "never touched".
    """
    outcome = derive(READS_THE_SENDER)
    assert outcome.access_list == []


def test_a_reverting_message_still_has_an_answer() -> None:
    """
    A revert is reported beside the list rather than instead of it.

    The list survives because the top-level frame's warm sets do, and
    the tier drops because the failure reaches a client as free text.
    """
    outcome = derive(REVERTS_AFTER_READING)
    assert outcome.reverted
    assert outcome.assertion == "partial"
    assert outcome.access_list == [
        {"address": str(REVERTS_AFTER_READING), "storageKeys": [SLOT_KEY]}
    ]


def test_a_successful_message_is_stored_exactly() -> None:
    """Nothing about a successful response is left unasserted."""
    assert derive(READS_A_SLOT).assertion == "exact"


def test_the_gas_is_the_gas_with_the_list_attached() -> None:
    """
    The reported gas belongs to the list beside it, not to a plain call.

    Declaring an entry is charged up front and makes the entry warm, so
    the two figures differ by construction. Asserting only that they
    differ keeps the test from restating the fork's gas schedule, which
    is the specification's business rather than this module's.
    """
    from execution_testing.rpc.serialization.execution import _run_message

    plain = _run_message(
        make_site(),
        sender=Address(SENDER),
        to=READS_A_SLOT,
        data=Bytes(b""),
        value=0,
        gas=CALL_GAS_LIMIT,
    )
    outcome = derive(READS_A_SLOT)
    assert outcome.gas_used != plain.gas_used


def test_the_result_is_the_body_a_client_returns() -> None:
    """The two fields the schema defines, and the gas as a quantity."""
    outcome = derive(READS_A_SLOT)
    assert outcome.result == {
        "accessList": outcome.access_list,
        "gasUsed": hex(outcome.gas_used),
    }


def test_a_message_that_cannot_run_derives_nothing() -> None:
    """
    A halt that is not a revert has no answer worth storing.

    Consistent with `eth_call`: the codes clients report such a halt
    under are their own, so deriving one would enshrine a client's
    choice.
    """
    with pytest.raises(UnrunnableCallError, match="halted with"):
        derive(HALTS)


def test_a_declared_message_completes_what_it_stores() -> None:
    """`gas` and `gasPrice` are filled in, as they are for a call."""
    result = compute_declared_access_list(
        [{"from": SENDER, "to": READS_A_SLOT}, "0x0"], [make_site()]
    )
    message = result.params[0]
    assert message["gas"] == hex(CALL_GAS_LIMIT)
    assert message["gasPrice"] == "0x7"
    assert result.outcome.access_list


def test_a_declared_message_needs_a_sender() -> None:
    """The same requirement a declared call has, and the same message."""
    with pytest.raises(UnrunnableCallError, match="names no sender"):
        compute_declared_access_list(
            [{"to": READS_A_SLOT}, "0x0"], [make_site()]
        )


def test_compute_result_dispatches_an_access_list() -> None:
    """The dispatcher reaches the same derivation."""
    result = compute_result(
        "eth_createAccessList",
        [{"from": SENDER, "to": READS_A_SLOT}, "0x0"],
        [],
        [make_site()],
    )
    assert result.outcome.access_list == [
        {"address": str(READS_A_SLOT), "storageKeys": [SLOT_KEY]}
    ]


def test_a_test_may_declare_an_access_list() -> None:
    """`eth_createAccessList` is accepted as a computable method."""
    from execution_testing.specs.blockchain import RPCExpectation

    RPCExpectation(
        method="eth_createAccessList",
        params=[{"from": SENDER, "to": READS_A_SLOT}, "0x0"],
        derive_result=True,
    )


DELEGATED = Address(0xDE1E)
DELEGATE_TARGET = Address(0x7A76)


def test_a_delegated_recipient_derives_nothing() -> None:
    """
    The one disagreement where the specification is the right side.

    Resolving a delegation reads the target's account and warms it, so
    declaring the target saves gas and it belongs in the list. Clients
    build the list by watching opcodes and no opcode names a delegation
    target, so they omit it. Asserting the correct answer would fail
    every client, and a list missing an entry is a wrong answer rather
    than a partial one, so nothing is derived at all.
    """
    site = make_site()
    site.state.root[DELEGATE_TARGET] = Account(balance=0, code=bytes(Op.STOP))
    site.state.root[DELEGATED] = Account(
        balance=0, code=bytes.fromhex("ef0100") + bytes(DELEGATE_TARGET)
    )

    with pytest.raises(UnrunnableCallError, match="is delegated"):
        derive(DELEGATED, site=site)
