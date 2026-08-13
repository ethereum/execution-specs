"""Test the execution behind `eth_call` expectations."""

from typing import Any, Dict, List

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


def make_site(
    number: int = 0,
    base_fee: int = 7,
    forkchoice_tag: str | None = None,
) -> CallSite:
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
        block_hash=Hash(0xB10C_0000 + number),
        forkchoice_tag=forkchoice_tag,
    )


def call(site: CallSite, to: Address | None, **overrides: Any) -> Any:
    """Run a message from the funded sender at `site`."""
    arguments: Dict[str, Any] = {
        "sender": Address(SENDER),
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


def test_a_call_may_come_from_a_contract() -> None:
    """
    A contract is a valid sender, which a signed message could not be.

    The two things a signature implies — that the sender is recoverable,
    and that it is an externally owned account — are waived together
    when the sender is asserted instead. `RETURNS_A_WORD` holds code, so
    a spec still enforcing the second would reject this with "not EOA"
    rather than answer it, and a tool still signing could not name it at
    all.

    The probe returns `CALLER`, so the assertion is that the address the
    caller *named* is the one the EVM saw, not merely that something ran.
    """
    site = make_site()
    site.state.root[RETURNS_A_WORD] = Account(
        balance=10**18,
        code=bytes(Op.MSTORE(0, 0x1234) + Op.RETURN(0, 32)),
    )
    reports_caller = Address(0xCA11)
    site.state.root[reports_caller] = Account(
        balance=0,
        code=bytes(Op.MSTORE(0, Op.CALLER) + Op.RETURN(0, 32)),
    )
    outcome = call(site, reports_caller, sender=RETURNS_A_WORD)
    assert not outcome.reverted
    assert int(outcome.return_data, 16) == int.from_bytes(
        bytes(RETURNS_A_WORD), "big"
    )


def test_a_call_may_come_from_the_zero_address() -> None:
    """
    The zero address is a valid sender, and no key exists for it.

    It is the commonest `from` in real usage and the one case a tool that
    signs can never reach, since no private key recovers to it.

    The probe returns its caller's *balance* rather than its address, so
    the answer distinguishes the zero address having genuinely sent the
    message from an empty word being returned by accident: the value is
    the funded balance minus the gas the message bought, which no other
    account here holds.
    """
    site = make_site()
    zero = Address(0)
    site.state.root[zero] = Account(balance=10**18)
    probe = Address(0xBA2)
    site.state.root[probe] = Account(
        balance=0,
        code=bytes(Op.MSTORE(0, Op.BALANCE(Op.CALLER)) + Op.RETURN(0, 32)),
    )
    outcome = call(site, probe, sender=zero)
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
        pytest.param("safe", "no consensus layer told", id="safe"),
        pytest.param("finalized", "no consensus layer told", id="finalized"),
        pytest.param("pending", "does not exist", id="pending"),
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
    fixed by a chain, so a chain that tagged none of its blocks has
    nothing to resolve them against. `pending` is refused outright: a
    filled chain has no next block at all.
    """
    with pytest.raises(UnrunnableCallError, match=message):
        declared(reference)


def _timestamp_reading_sites(
    tags: Dict[int, str] | None = None,
) -> tuple[List[CallSite], Address]:
    """Return three sites whose only contract reports the timestamp."""
    tags = tags or {}
    sites = [
        make_site(number, forkchoice_tag=tags.get(number))
        for number in (0, 1, 2)
    ]
    reads_timestamp = Address(0x71E)
    for site in sites:
        site.state.root[reads_timestamp] = Account(
            balance=0,
            code=bytes(Op.MSTORE(0, Op.TIMESTAMP) + Op.RETURN(0, 32)),
        )
    return sites, reads_timestamp


def _block_named(reference: Any, sites: List[CallSite], to: Address) -> int:
    """Return the block number a declared call actually ran against."""
    result = compute_declared_call(
        [{"from": SENDER, "to": to}, reference], sites
    )
    return int(result.outcome.return_data, 16) - 1_000


def test_a_declared_call_resolves_a_bare_block_hash() -> None:
    """
    A hash names the same block its number does.

    The parameter is titled "Block number, tag, or block hash", and a
    filled chain is a single canonical line, so the two forms cannot
    disagree.
    """
    sites, reads_timestamp = _timestamp_reading_sites()
    assert _block_named(str(sites[1].block_hash), sites, reads_timestamp) == 1


def test_a_declared_call_resolves_an_eip_1898_hash() -> None:
    """The object form of a hash resolves the same block the bare one does."""
    sites, reads_timestamp = _timestamp_reading_sites()
    reference = {"blockHash": str(sites[1].block_hash)}
    assert _block_named(reference, sites, reads_timestamp) == 1


def test_a_declared_call_resolves_an_eip_1898_number() -> None:
    """The object form of a number resolves too."""
    sites, reads_timestamp = _timestamp_reading_sites()
    assert _block_named({"blockNumber": "0x2"}, sites, reads_timestamp) == 2


def test_require_canonical_changes_the_error_not_the_answer() -> None:
    """
    The flag asks for a failure on a hash off the canonical chain.

    Every block this chain produced is canonical, so a hash it does not
    have is exactly the case the flag is about, and the refusal says so
    rather than reporting a plain unknown block.
    """
    sites, _ = _timestamp_reading_sites()
    stranger = str(Hash(0xDEAD))
    with pytest.raises(UnrunnableCallError, match="requires it to be"):
        declared({"blockHash": stranger, "requireCanonical": True})
    with pytest.raises(UnrunnableCallError, match="did not produce"):
        declared({"blockHash": stranger})
    del sites


def test_an_eip_1898_object_names_exactly_one_thing() -> None:
    """Neither both forms at once nor neither of them is a reference."""
    with pytest.raises(UnrunnableCallError, match="exactly one"):
        declared({"blockNumber": "0x1", "blockHash": str(Hash(1))})
    with pytest.raises(UnrunnableCallError, match="exactly one"):
        declared({"requireCanonical": True})


def test_a_forkchoice_tag_resolves_to_the_block_it_was_declared_on() -> None:
    """
    `safe` and `finalized` resolve where the chain declared them.

    Not from the chain — nothing in a chain says which of its blocks are
    safe — but from the tag a test put on a block, which is the same
    declaration the consumer makes to the client.
    """
    sites, reads_timestamp = _timestamp_reading_sites(
        {1: "finalized", 2: "safe"}
    )
    assert _block_named("finalized", sites, reads_timestamp) == 1
    assert _block_named("safe", sites, reads_timestamp) == 2


def test_a_declared_call_needs_no_key_for_its_sender() -> None:
    """
    A bare address is enough; an author no longer has to pass an `EOA`.

    This is the whole point of asserting the sender rather than
    recovering it. `0x1` is an address the test holds no key for, and
    the call is answered anyway.
    """
    keyless = Address(0x1)
    site = make_site()
    site.state.root[keyless] = Account(balance=10**18)
    result = compute_declared_call(
        [{"from": keyless, "to": RETURNS_A_WORD}, "0x0"], [site]
    )
    assert result.outcome.return_data.endswith("1234")
    assert result.params[0]["from"] == str(keyless)


def test_a_keyless_sender_still_needs_a_balance() -> None:
    """
    Solvency is the one admission check the derivation does not waive.

    Recorded as a test rather than left implicit, because it is the
    restriction that survives asserting the sender, and an author whose
    zero-address call derives nothing needs to be told which of the two
    they hit.
    """
    with pytest.raises(UnrunnableCallError, match="cannot afford"):
        compute_declared_call(
            [{"from": Address(0), "to": RETURNS_A_WORD}, "0x0"], [make_site()]
        )


def test_a_declared_call_states_its_sender() -> None:
    """
    A message with no `from` derives nothing rather than guessing one.

    A client defaults the field to the zero address, which is a real
    sender with a real balance, so guessing it here would answer a
    question the author did not ask.
    """
    with pytest.raises(UnrunnableCallError, match="names no sender"):
        compute_declared_call([{"to": RETURNS_A_WORD}, "0x0"], [make_site()])


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
