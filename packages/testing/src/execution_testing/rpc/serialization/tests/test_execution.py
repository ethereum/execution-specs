"""Test the execution behind `eth_call` expectations."""

from typing import Any, Dict

import pytest

from execution_testing.base_types import Account, Address, Bytes, Hash
from execution_testing.forks import Amsterdam
from execution_testing.rpc.serialization import compute_result
from execution_testing.rpc.serialization.execution import (
    CALL_GAS_LIMIT,
    CallSite,
    UnrunnableCallError,
    call_message,
    compute_declared_call,
    environment_at,
    run_call,
)
from execution_testing.test_types import Alloc, Environment
from execution_testing.test_types.account_types import EOA
from execution_testing.vm.opcodes import Opcodes as Op

SENDER_KEY = Hash(0x1234)
SENDER = EOA(key=SENDER_KEY)

RETURNS_A_WORD = Address(0xC0DE)
REVERTS = Address(0xDEAD)
MISSING = Address(0xABBA)
HALTS = Address(0xBAD0)


def make_site(number: int = 0, base_fee: int = 7) -> CallSite:
    """Return a site holding one funded sender and two contracts."""
    state = Alloc(
        {
            Address(SENDER): Account(balance=10**18, nonce=3),
            RETURNS_A_WORD: Account(
                balance=0,
                code=bytes(Op.MSTORE(0, 0x1234) + Op.RETURN(0, 32)),
            ),
            REVERTS: Account(
                balance=0,
                code=bytes(Op.MSTORE(0, 0xBEEF) + Op.REVERT(0, 32)),
            ),
            HALTS: Account(balance=0, code=bytes(Op.INVALID)),
        }
    )
    return CallSite(
        number=number,
        state=state,
        environment=Environment(
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


def call(site: CallSite, to: Address | None, **overrides: Any) -> Any:
    """Run a message from the funded sender at `site`."""
    arguments: Dict[str, Any] = {
        "sender": Address(SENDER),
        "signing_key": SENDER_KEY,
        "to": to,
        "data": Bytes(b""),
        "value": 0,
        "gas": CALL_GAS_LIMIT,
    }
    arguments.update(overrides)
    return run_call(site, **arguments)


def test_a_returning_call_reports_its_output() -> None:
    """A contract's return data is the answer, and is not a revert."""
    outcome = call(make_site(), RETURNS_A_WORD)
    assert outcome.return_data == "0x" + "00" * 30 + "1234"
    assert not outcome.reverted


def test_a_reverting_call_keeps_its_data_and_is_flagged() -> None:
    """
    A revert reports data *and* the fact that it reverted.

    Both halves matter: the flag is what turns the expectation into an
    error rather than a result, and losing the data would make a revert
    indistinguishable from a successful empty return.
    """
    outcome = call(make_site(), REVERTS)
    assert outcome.reverted
    assert outcome.return_data == "0x" + "00" * 30 + "beef"


def test_a_call_to_a_missing_account_succeeds_emptily() -> None:
    """
    An unallocated recipient is not an error.

    The state is a total function, so an address with no account has no
    code, and running no code returns nothing successfully. A client
    reporting an error here would be wrong, so the distinction from the
    reverting case above is asserted rather than assumed.
    """
    outcome = call(make_site(), MISSING)
    assert not outcome.reverted
    assert outcome.return_data == "0x"


def test_the_call_sees_the_state_it_is_given() -> None:
    """
    A balance read answers from the site's state, minus the gas bought.

    The sender is debited `gas * gasPrice` before the frame runs, exactly
    as a transaction is, and a client does the same — go-ethereum's
    `eth_call` buys gas against an ephemeral state before executing. The
    debit is asserted rather than avoided, because a message priced at
    the block's base fee is *supposed* to be paid for; a derivation that
    skipped the purchase would disagree with every client at the first
    contract that reads its caller's balance.
    """
    site = make_site()
    probe = Address(0xBA1)
    site.state.root[probe] = Account(
        balance=0,
        code=bytes(Op.MSTORE(0, Op.BALANCE(SENDER)) + Op.RETURN(0, 32)),
    )
    outcome = call(site, probe)
    assert int(outcome.return_data, 16) == 10**18 - CALL_GAS_LIMIT * 7


def test_an_unaffordable_message_derives_nothing() -> None:
    """
    A message the sender cannot pay for is refused before it is run.

    Both sides would reject it, so there is no disagreement to catch;
    what there would be is an expectation asserting nothing about the
    EVM, which is worse than no expectation at all.
    """
    site = make_site()
    with pytest.raises(UnrunnableCallError, match="cannot afford"):
        call(site, MISSING, value=10**19)


def test_a_halting_message_derives_nothing() -> None:
    """
    A halt that is not a revert has no expectation worth storing.

    Clients report one under a code no specification fixes —
    go-ethereum uses `-32000` — so pinning it would enshrine a single
    client's choice, which is the trap this whole suite exists to avoid.
    A revert is the one exception, and is derived; see above.
    """
    site = make_site()
    with pytest.raises(UnrunnableCallError, match="halted with"):
        call(site, HALTS)


def test_the_message_states_every_field() -> None:
    """
    Nothing is left for a client to default.

    A client defaulting `gas` picks its own ceiling and one defaulting
    `gasPrice` picks zero and waives the fee check with it, so an
    incomplete message is not the message whose answer was derived.
    """
    message = call_message(
        sender=Address(SENDER),
        to=RETURNS_A_WORD,
        data=Bytes(b"\x01"),
        value=2,
        gas=3,
        gas_price=4,
    )
    assert message == {
        "from": str(Address(SENDER)),
        "to": str(RETURNS_A_WORD),
        "input": "0x01",
        "value": "0x2",
        "gas": "0x3",
        "gasPrice": "0x4",
    }


def test_a_creation_names_no_recipient() -> None:
    """`to` is omitted rather than null, which the schema forbids."""
    message = call_message(
        sender=Address(SENDER),
        to=None,
        data=Bytes(b""),
        value=0,
        gas=1,
        gas_price=1,
    )
    assert "to" not in message


def test_the_context_is_the_named_block_s_own() -> None:
    """
    A call names a block, and takes that block's context with its state.

    Reproducing only the state would leave the two sides disagreeing
    about `NUMBER`, `TIMESTAMP` and `BASEFEE`.
    """
    from execution_testing.fixtures.blockchain import FixtureHeader

    header = FixtureHeader(
        parent_hash=Hash(0),
        ommers_hash=Hash(0),
        fee_recipient=Address(0xC0FFEE),
        state_root=Hash(0),
        transactions_trie=Hash(0),
        receipts_root=Hash(0),
        logs_bloom=bytes(256),
        difficulty=0,
        number=5,
        gas_limit=1_000_000,
        gas_used=0,
        timestamp=99,
        extra_data=b"",
        prev_randao=Hash(0xAB),
        nonce=bytes(8),
        base_fee_per_gas=11,
    )
    environment = environment_at(
        header, {4: Hash(0x44), 5: Hash(0x55), 6: Hash(0x66)}
    )
    assert int(environment.number) == 5
    assert int(environment.timestamp) == 99
    assert environment.base_fee_per_gas is not None
    assert int(environment.base_fee_per_gas) == 11
    assert environment.fee_recipient == Address(0xC0FFEE)
    # Only blocks strictly before the named one are reachable by
    # `BLOCKHASH`; the named block's own hash is not yet determined
    # while it is being executed against.
    assert set(int(number) for number in environment.block_hashes) == {4}


def declared(reference: Any, **message: Any) -> Any:
    """Compute a declared call naming `reference`, over three sites."""
    sites = [make_site(number) for number in (0, 1, 2)]
    return compute_declared_call(
        [{"from": SENDER, "to": RETURNS_A_WORD, **message}, reference], sites
    )


@pytest.mark.parametrize(
    "reference,expected",
    [
        pytest.param("0x1", 1, id="number"),
        pytest.param("latest", 2, id="latest"),
        pytest.param("earliest", 0, id="earliest"),
    ],
)
def test_a_declared_call_resolves_the_block_it_names(
    reference: str, expected: int
) -> None:
    """
    Numbers and the two tags a chain determines all resolve.

    Each site here carries a different `TIMESTAMP`, so the block the
    message actually ran against can be read back out of the answer
    rather than inferred from the call not raising.
    """
    sites = [make_site(number) for number in (0, 1, 2)]
    reads_timestamp = Address(0x71E)
    for site in sites:
        site.state.root[reads_timestamp] = Account(
            balance=0,
            code=bytes(Op.MSTORE(0, Op.TIMESTAMP) + Op.RETURN(0, 32)),
        )
    result = compute_declared_call(
        [{"from": SENDER, "to": reads_timestamp}, reference], sites
    )
    assert result.params[1] == reference
    assert int(result.outcome.return_data, 16) == 1_000 + expected


@pytest.mark.parametrize(
    "reference,message",
    [
        pytest.param("safe", "no chain determines", id="safe"),
        pytest.param("finalized", "no chain determines", id="finalized"),
        pytest.param("pending", "no chain determines", id="pending"),
        pytest.param("0x9", "does not have", id="beyond_the_chain"),
        pytest.param("nonsense", "neither a quantity", id="malformed"),
    ],
)
def test_a_declared_call_refuses_a_block_it_cannot_resolve(
    reference: str, message: str
) -> None:
    """
    A block with no state here derives nothing rather than guessing.

    `safe` and `finalized` are declared by a consensus layer rather than
    fixed by a chain, so an answer computed for them would describe the
    harness rather than the specification.
    """
    with pytest.raises(UnrunnableCallError, match=message):
        declared(reference)


def test_a_declared_call_needs_a_sender_it_can_sign_for() -> None:
    """
    A bare address carries no key, so the message cannot be signed.

    The failure names the restriction rather than the symptom, because
    the fix is to pass the `EOA` the test already holds.
    """
    sites = [make_site()]
    with pytest.raises(UnrunnableCallError, match="carries no key"):
        compute_declared_call(
            [{"from": Address(0x1), "to": RETURNS_A_WORD}, "0x0"], sites
        )


def test_a_declared_call_completes_the_message_it_stores() -> None:
    """
    The stored parameters are the executed ones, not the written ones.

    An author writes the part that carries meaning; `gas` and `gasPrice`
    are filled in because a client left to default them would execute a
    different message from the one whose answer was derived.
    """
    result = declared("0x1")
    message = result.params[0]
    assert message["gas"] == hex(CALL_GAS_LIMIT)
    assert message["gasPrice"] == "0x7"
    assert message["value"] == "0x0"
    assert message["input"] == "0x"


def test_compute_result_dispatches_a_call() -> None:
    """`eth_call` reaches the same computation through the dispatcher."""
    sites = [make_site()]
    result = compute_result(
        "eth_call",
        [{"from": SENDER, "to": RETURNS_A_WORD}, "0x0"],
        [],
        sites,
    )
    assert result.outcome.return_data.endswith("1234")


def test_a_declared_call_may_be_expected_to_revert() -> None:
    """A revert is an answer, and the outcome says which kind it is."""
    result = compute_declared_call(
        [{"from": SENDER, "to": REVERTS}, "0x0"], [make_site()]
    )
    assert result.outcome.reverted


def test_a_test_may_declare_a_call() -> None:
    """`eth_call` is accepted as a computable declared method."""
    from execution_testing.specs.blockchain import RPCExpectation

    RPCExpectation(
        method="eth_call",
        params=[{"from": SENDER, "to": RETURNS_A_WORD}, "0x0"],
        derive_result=True,
    )
