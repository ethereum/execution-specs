"""Test enumeration of RPC expectations from a filled fixture."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Address, Bytes, Hash, HexNumber
from execution_testing.exceptions import BlockException
from execution_testing.fixtures.blockchain import (
    BlockchainFixture,
    FixtureConfig,
    FixtureWithdrawal,
    InvalidFixtureBlock,
)
from execution_testing.forks import Amsterdam
from execution_testing.rpc.serialization import (
    UncomputableCallError,
    compute_result,
    derive_rpc_calls,
    filter_logs,
    validate_result,
)
from execution_testing.rpc.serialization import derive as derive_module
from execution_testing.rpc.serialization.derive import ProjectionError

from .test_projection import (
    RECIPIENT,
    make_access_list,
    make_block,
    make_header,
    make_receipt,
    make_transaction,
)


def make_fixture(blocks: List[Any]) -> BlockchainFixture:
    """Return a fixture wrapping the given blocks."""
    genesis = make_header(number=0, gas_used=0)
    return BlockchainFixture(
        fork=Amsterdam,
        genesis=genesis,
        genesis_rlp=Bytes(b"\xc0"),
        blocks=blocks,
        last_block_hash=genesis.block_hash,
        pre={},
        post_state={},
        config=FixtureConfig(fork=Amsterdam, chain_id=1),
    )


@pytest.fixture
def single_block_fixture() -> BlockchainFixture:
    """Return a fixture holding one block with two transactions."""
    transactions = [make_transaction(nonce=0), make_transaction(nonce=1)]
    receipts = [
        make_receipt(21_000, transaction_hash=Hash(0xAA)),
        make_receipt(42_000, transaction_hash=Hash(0xBB)),
    ]
    return make_fixture([make_block(transactions, receipts)])


def methods(calls: List[Any]) -> List[str]:
    """Return the method name of each call, in order."""
    return [call.method for call in calls]


def test_each_block_is_queried_both_ways(
    single_block_fixture: BlockchainFixture,
) -> None:
    """A block is fetched by number and by hash, with the same result."""
    calls = derive_rpc_calls(single_block_fixture)

    by_number = next(c for c in calls if c.method == "eth_getBlockByNumber")
    by_hash = next(c for c in calls if c.method == "eth_getBlockByHash")

    assert by_number.result == by_hash.result
    assert by_number.params[0] == "0x1"


def test_every_transaction_gets_a_receipt_lookup(
    single_block_fixture: BlockchainFixture,
) -> None:
    """Each transaction contributes a receipt call keyed by its hash."""
    calls = derive_rpc_calls(single_block_fixture)
    receipts = [
        c
        for c in calls
        if c.method == "eth_getTransactionReceipt" and c.result is not None
    ]

    assert [c.params[0] for c in receipts] == [
        str(Hash(0xAA)),
        str(Hash(0xBB)),
    ]


def test_parameters_come_from_the_chain(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    Every parameter is read off the fixture.

    Nothing is author-supplied, which is why the marker carries no
    parameter information.
    """
    calls = derive_rpc_calls(single_block_fixture)
    block = single_block_fixture.blocks[0]

    by_hash = next(c for c in calls if c.method == "eth_getBlockByHash")
    assert by_hash.params[0] == str(block.header.block_hash)  # type: ignore


def test_derived_results_conform_to_the_schema(
    single_block_fixture: BlockchainFixture,
) -> None:
    """Enumeration produces spec-conformant results, not just plausible."""
    for call in derive_rpc_calls(single_block_fixture):
        if call.error_code is not None or call.result_keccak is not None:
            continue  # Neither carries a result to validate.
        validate_result(call.method, call.result)


def test_invalid_blocks_are_skipped() -> None:
    """
    An invalid block contributes no expectations.

    It never joins the canonical chain, so a client is right to report
    nothing for it.
    """
    valid = make_block([make_transaction()], [make_receipt(21_000)])
    invalid = InvalidFixtureBlock(
        rlp=Bytes(b"\xc0"),
        expect_exception=BlockException.INCORRECT_BLOCK_FORMAT,
    )

    calls = derive_rpc_calls(make_fixture([valid, invalid]))

    # Two per canonical block: the hash form and the full-object form.
    assert numbered(calls).count("eth_getBlockByNumber") == 2


def numbered(calls: List[Any]) -> List[str]:
    """Return the methods of the calls that name a block by number."""
    return [
        call.method
        for call in calls
        if call.params and str(call.params[0]).startswith("0x")
    ]


def test_empty_block_yields_no_receipt_calls() -> None:
    """A block with no transactions still gets its block queries."""
    calls = derive_rpc_calls(make_fixture([make_block([], [])]))
    from_chain = [c for c in calls if c.result is not None]

    assert "eth_getTransactionReceipt" not in methods(from_chain)
    assert "eth_getTransactionByHash" not in methods(from_chain)
    assert numbered(calls).count("eth_getBlockByNumber") == 2


def test_calls_serialize_into_the_fixture(
    single_block_fixture: BlockchainFixture,
) -> None:
    """The derived section round-trips through the fixture model."""
    single_block_fixture.rpc = derive_rpc_calls(single_block_fixture)

    dumped: Dict[str, Any] = single_block_fixture.model_dump(
        by_alias=True, mode="json"
    )

    assert len(dumped["rpc"]) == len(single_block_fixture.rpc)
    assert dumped["rpc"][0]["method"] == "eth_getBlockByNumber"


def test_absent_marker_leaves_the_section_unset(
    single_block_fixture: BlockchainFixture,
) -> None:
    """A fixture carries no `rpc` section unless one is derived."""
    assert single_block_fixture.rpc is None


def test_broken_projection_fails_at_derivation(
    single_block_fixture: BlockchainFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A non-conformant projection is refused rather than written out.

    `FixtureRPCCall.result` is `Any`, so nothing downstream can tell a
    projected block from a bare string. Were this to reach a release it
    would surface as "your response is wrong" to a client team debugging
    an assertion that was never satisfiable.
    """
    good = derive_rpc_calls(single_block_fixture)[0].result
    monkeypatch.setattr(
        derive_module,
        "block_response",
        lambda _block, **_kwargs: _BadProjection(good),
    )

    with pytest.raises(ProjectionError, match="projection bug"):
        derive_rpc_calls(single_block_fixture)


def test_unknown_method_fails_at_derivation(
    single_block_fixture: BlockchainFixture,
) -> None:
    """A call the schema does not define is refused at derivation."""
    calls = derive_rpc_calls(single_block_fixture)
    calls[0].method = "eth_notAMethod"

    with pytest.raises(ProjectionError, match="does not define"):
        derive_module._reject_unsatisfiable(calls)


class _BadProjection:
    """
    Stand-in projection with a realistic defect.

    Structurally a block, but quantities are zero-padded the way the
    consensus types encode them. This is the exact regression the guard
    exists for: plausible enough to survive every downstream check, and
    unsatisfiable by any conforming client.
    """

    def __init__(self, good: Dict[str, Any]) -> None:
        self.payload = dict(good, number="0x01")

    def to_rpc(self) -> Dict[str, Any]:
        """Return the defective block object."""
        return self.payload


def test_blocks_can_be_supplied_directly(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    Derivation accepts a block list, not only a fixture.

    The engine formats carry payloads rather than blocks, so their blocks
    are assembled during generation and handed over directly.
    """
    from_fixture = derive_rpc_calls(single_block_fixture)
    from_blocks = derive_module.derive_rpc_calls_for_blocks(
        single_block_fixture.blocks,
        post_state=single_block_fixture.post_state,
        genesis=derive_module.genesis_block(single_block_fixture),
    )

    assert [c.method for c in from_blocks] == [c.method for c in from_fixture]
    assert [c.result for c in from_blocks] == [c.result for c in from_fixture]


def make_post_state(**accounts: Any) -> Dict[Any, Any]:
    """Return a post-state mapping addresses to accounts."""
    return dict(accounts)


def test_touched_accounts_covers_the_parties_involved() -> None:
    """
    Senders, recipients, creations, withdrawals and the coinbase.

    A post-state holds every pre-allocated account, so asserting all of
    them would multiply the fixture without adding coverage.
    """
    from execution_testing.rpc.serialization.derive import touched_accounts

    block = make_block(
        [make_transaction(), make_transaction(to=None, nonce=1)],
        [
            make_receipt(21_000, transaction_hash=Hash(0xAA)),
            make_receipt(42_000, transaction_hash=Hash(0xBB)),
        ],
    )
    block.withdrawals = [
        FixtureWithdrawal(
            index=0, validator_index=0, address=Address(0xCC), amount=1
        )
    ]

    touched = touched_accounts([block])

    assert Address(0xA1) in touched  # sender
    assert Address(0xB2) in touched  # recipient
    assert Address(0xCC) in touched  # withdrawal recipient
    assert Address(3) in touched  # fee recipient
    assert len(touched) == len(set(touched)), "addresses must not repeat"


def test_authorization_authority_is_touched() -> None:
    """
    The account a delegation is written to is asserted.

    An authority is neither the sender nor the recipient, so nothing else
    reaches it — yet it is the account an EIP-7702 transaction changes:
    its code becomes a delegation designator and its nonce advances.
    """
    from execution_testing.fixtures.common import FixtureAuthorizationTuple
    from execution_testing.rpc.serialization.derive import touched_accounts

    authority = Address(0xDD)
    transaction = make_transaction(
        ty=4,
        authorization_list=[
            FixtureAuthorizationTuple(
                chain_id=1,
                address=RECIPIENT,
                nonce=0,
                v=0,
                r=1,
                s=2,
                signer=authority,
            )
        ],
    )
    block = make_block([transaction], [make_receipt(21_000)])

    assert authority in touched_accounts([block])


def test_state_reads_are_absent_without_a_post_state(
    single_block_fixture: BlockchainFixture,
) -> None:
    """No post-state means no state reads, rather than empty assertions."""
    calls = derive_module.derive_rpc_calls_for_blocks(
        single_block_fixture.blocks, post_state=None
    )

    assert "eth_getBalance" not in methods(calls)


def code_read(code: bytes) -> Any:
    """Return the `eth_getCode` expectation for an account with that code."""
    from execution_testing.test_types.account_types import Account

    block = make_block([make_transaction()], [make_receipt(21_000)])
    post_state = {
        RECIPIENT: Account(nonce=0, balance=5, code=code, storage={})
    }

    calls = derive_module.derive_rpc_calls_for_blocks(
        [block], post_state=post_state
    )
    return next(
        c
        for c in calls
        if c.method == "eth_getCode" and c.params[0] == str(RECIPIENT)
    )


def test_long_code_is_asserted_by_digest() -> None:
    """
    `eth_getCode` stores a digest, not the bytecode.

    The code is already in `pre` and `postState`, so repeating it would
    duplicate the largest field in the fixture for no added assertion.
    """
    code = b"\x60\x00" * 32

    call = code_read(code)

    assert call.result is None
    assert call.result_keccak == Bytes(code).keccak256()


def test_short_code_is_asserted_by_value() -> None:
    """
    Code no larger than a digest is stored as itself.

    A digest would be the bigger of the two and would turn a legible
    failure into "digest mismatch" — which matters for the short values
    that carry meaning, such as an EIP-7702 delegation designator naming
    the account it points at.
    """
    designator = b"\xef\x01\x00" + bytes(RECIPIENT)

    call = code_read(designator)

    assert call.result == str(Bytes(designator))
    assert call.result_keccak is None


def test_state_reads_query_the_head_block() -> None:
    """State reads name the head block, which the post-state describes."""
    from execution_testing.test_types.account_types import Account

    block = make_block([make_transaction()], [make_receipt(21_000)], number=1)
    post_state = {RECIPIENT: Account(nonce=1, balance=7, code=b"", storage={})}

    calls = derive_module.derive_rpc_calls_for_blocks(
        [block], post_state=post_state
    )
    balance = next(c for c in calls if c.method == "eth_getBalance")

    assert balance.params[1] == "0x1"
    assert balance.result == "0x7"


def test_state_reads_are_emitted_with_and_without_a_block_tag() -> None:
    """
    Every state read is asserted twice, once naming no block at all.

    Omitting the parameter defaults to latest, so the answers must agree;
    the point is the client's defaulting path, which the numbered form
    never exercises.
    """
    from execution_testing.test_types.account_types import Account

    block = make_block([make_transaction()], [make_receipt(21_000)], number=1)
    post_state = {RECIPIENT: Account(nonce=1, balance=7, code=b"", storage={})}

    calls = derive_module.derive_rpc_calls_for_blocks(
        [block], post_state=post_state
    )
    balances = [c for c in calls if c.method == "eth_getBalance"]
    for_recipient = [c for c in balances if c.params[0] == str(RECIPIENT)]

    assert [c.params for c in for_recipient] == [
        [str(RECIPIENT), "0x1"],
        [str(RECIPIENT)],
    ]
    assert {c.result for c in for_recipient} == {"0x7"}


def test_a_zeroed_storage_slot_is_still_asserted() -> None:
    """
    A slot the chain wrote zero to is read back.

    `Storage` tests as false when every value is zero, so the obvious
    `account.storage or {}` silently drops exactly the case where a client
    might wrongly report the previous value.
    """
    from execution_testing.test_types.account_types import Account

    block = make_block([make_transaction()], [make_receipt(21_000)])
    post_state = {
        RECIPIENT: Account(nonce=0, balance=0, code=b"", storage={7: 0})
    }

    calls = derive_module.derive_rpc_calls_for_blocks(
        [block], post_state=post_state
    )
    slots = [
        c
        for c in calls
        if c.method == "eth_getStorageAt"
        and c.params[0] == str(RECIPIENT)
        and c.error_code is None
    ]

    assert slots, "the zeroed slot was dropped"
    assert slots[0].params[1] == str(Hash(7))
    assert slots[0].result == str(Hash(0))


def test_genesis_is_reached_through_the_earliest_tag(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    `earliest` names genesis, which no chain block covers.

    Genesis is the one block with no parent and no transactions, and the
    fixture stores it as a header rather than a block, so it is otherwise
    never projected.
    """
    calls = derive_rpc_calls(single_block_fixture)
    earliest = [c for c in calls if c.params and c.params[0] == "earliest"]

    block = next(c for c in earliest if c.method == "eth_getBlockByNumber")
    receipts = next(c for c in earliest if c.method == "eth_getBlockReceipts")

    assert block.result["number"] == "0x0"
    assert block.result["hash"] == str(single_block_fixture.genesis.block_hash)
    assert receipts.result == []


def test_latest_resolves_to_the_head_block(
    single_block_fixture: BlockchainFixture,
) -> None:
    """`latest` asserts the same object as the head block's own number."""
    calls = derive_rpc_calls(single_block_fixture)
    head = single_block_fixture.blocks[0].header  # type: ignore[union-attr]

    latest = next(
        c
        for c in calls
        if c.method == "eth_getBlockByNumber" and c.params[0] == "latest"
    )
    by_number = next(
        c
        for c in calls
        if c.method == "eth_getBlockByNumber"
        and c.params == [str(HexNumber(head.number)), True]
    )

    assert latest.result == by_number.result


def test_safe_and_finalized_need_a_declaration(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    Without a declaration the forkchoice tags are left alone.

    Measured against go-ethereum: a client whose forkchoice state names no
    safe or finalized block answers `-32000 safe block not found` rather
    than returning the head. An expectation emitted here anyway would
    describe our harness rather than the chain, so it is emitted only where
    the harness actually makes the declaration.
    """
    tags = {
        str(call.params[0])
        for call in derive_rpc_calls(single_block_fixture)
        if call.params
    }

    assert "safe" not in tags
    assert "finalized" not in tags


def three_block_chain() -> List[Any]:
    """Return three blocks whose projections differ from each other."""
    return [
        make_block(
            [make_transaction(nonce=number - 1)],
            [make_receipt(21_000, transaction_hash=Hash(number))],
            number=number,
        )
        for number in (1, 2, 3)
    ]


def forkchoice_calls(blocks: List[Any], **tags: Hash) -> List[Any]:
    """Return the calls derived for a chain with the given tags."""
    return derive_module.derive_rpc_calls_for_blocks(
        blocks, forkchoice_tags=tags
    )


def test_declared_tags_resolve_to_their_own_blocks() -> None:
    """
    Each tag returns the block it was pointed at, not the head.

    Three distinct blocks is the whole point: `rpc-compat` points head,
    safe and finalized at one block, so a client that answers every tag
    with the head passes. Here only a client tracking three pointers can.
    """
    blocks = three_block_chain()
    calls = forkchoice_calls(
        blocks,
        safe=blocks[1].header.block_hash,
        finalized=blocks[0].header.block_hash,
    )

    resolved = {
        call.params[0]: call.result["hash"]
        for call in calls
        if call.method == "eth_getBlockByNumber"
        and call.params[0] in ("latest", "safe", "finalized")
    }

    assert resolved == {
        "finalized": str(blocks[0].header.block_hash),
        "safe": str(blocks[1].header.block_hash),
        "latest": str(blocks[2].header.block_hash),
    }
    assert len(set(resolved.values())) == 3


def test_declared_tags_are_flagged_as_round_trips() -> None:
    """
    Only the declared tags claim a value the spec did not produce.

    The flag is what lets a consumer that cannot make the declaration skip
    them, and what tells a client team reading the fixture that this one
    expectation describes the harness.
    """
    blocks = three_block_chain()
    calls = forkchoice_calls(
        blocks,
        safe=blocks[1].header.block_hash,
        finalized=blocks[0].header.block_hash,
    )

    flagged = {
        (call.method, call.params[0]) for call in calls if call.round_trip
    }

    assert flagged == {
        ("eth_getBlockByNumber", "safe"),
        ("eth_getBlockByNumber", "finalized"),
        ("eth_getBlockReceipts", "safe"),
        ("eth_getBlockReceipts", "finalized"),
    }


def test_declared_receipts_follow_the_tagged_block() -> None:
    """`eth_getBlockReceipts` resolves the tag to the same block."""
    blocks = three_block_chain()
    calls = forkchoice_calls(
        blocks,
        safe=blocks[1].header.block_hash,
        finalized=blocks[0].header.block_hash,
    )

    receipts = {
        call.params[0]: call.result
        for call in calls
        if call.method == "eth_getBlockReceipts"
        and call.params[0] in ("safe", "finalized")
    }

    assert receipts["finalized"][0]["blockNumber"] == "0x1"
    assert receipts["safe"][0]["blockNumber"] == "0x2"


def test_a_tag_naming_another_chain_is_rejected() -> None:
    """
    A tag pointing outside the chain fails at derivation.

    No client could resolve it, so this is a harness bug of exactly the
    kind `_reject_unsatisfiable` exists to keep out of an artifact.
    """
    blocks = three_block_chain()

    with pytest.raises(ProjectionError, match="not a valid block"):
        forkchoice_calls(
            blocks,
            safe=Hash(0xDEADBEEF),
            finalized=blocks[0].header.block_hash,
        )


def test_absent_account_reads_are_zero_valued(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    A missing account reads as empty, not as null.

    The state is a total function, so an unallocated address has zero
    balance, zero nonce, no code and all-zero storage — the distinction
    from a missing block, which really is null.
    """
    calls = derive_rpc_calls(single_block_fixture)
    absent = derive_module._absent_account(
        single_block_fixture.blocks[0].header.block_hash  # type: ignore
    )
    for_absent = [c for c in calls if c.params and c.params[0] == str(absent)]
    by_method = {c.method: c for c in for_absent}

    assert by_method["eth_getBalance"].result == "0x0"
    assert by_method["eth_getTransactionCount"].result == "0x0"
    assert by_method["eth_getCode"].result == "0x"
    assert by_method["eth_getStorageAt"].result == str(Hash(0))


def test_absent_account_is_skipped_when_the_address_exists() -> None:
    """
    Nothing is asserted about an address the chain allocated.

    The address is derived by hashing, so a collision is not credible, but
    a wrong absence claim would be a projection bug rather than a client
    one.
    """
    from execution_testing.test_types.account_types import Account

    block = make_block([make_transaction()], [make_receipt(21_000)])
    absent = derive_module._absent_account(block.header.block_hash)
    post_state = {
        RECIPIENT: Account(nonce=0, balance=1, code=b"", storage={}),
        absent: Account(nonce=3, balance=9, code=b"", storage={}),
    }

    calls = derive_module.derive_rpc_calls_for_blocks(
        [block], post_state=post_state
    )
    for_absent = [c for c in calls if c.params and c.params[0] == str(absent)]

    assert for_absent == []


def test_absent_entities_expect_null(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    The zero hash names nothing, on any chain.

    Distinct from a missing account: a lookup by hash that finds nothing
    returns null rather than a zero-valued object.
    """
    calls = derive_rpc_calls(single_block_fixture)
    nothing = str(Hash(0))
    for_nothing = [c for c in calls if c.params and c.params[0] == nothing]

    assert {c.method for c in for_nothing} == {
        "eth_getTransactionByHash",
        "eth_getTransactionReceipt",
        "eth_getBlockByHash",
        "eth_getBlockReceipts",
    }
    assert all(c.result is None for c in for_nothing)
    assert all(c.error_code is None for c in for_nothing)


def test_malformed_storage_keys_expect_invalid_params() -> None:
    """
    A key that cannot be decoded is rejected before any lookup.

    Measured against go-ethereum, which answers `-32602` to both. The
    request names an account that exists, so the key is the only thing
    wrong with it.
    """
    from execution_testing.test_types.account_types import Account

    block = make_block([make_transaction()], [make_receipt(21_000)])
    post_state = {RECIPIENT: Account(nonce=0, balance=1, code=b"", storage={})}

    calls = derive_module.derive_rpc_calls_for_blocks(
        [block], post_state=post_state
    )
    malformed = [c for c in calls if c.error_code is not None]

    assert [c.params[1] for c in malformed] == [
        "0x" + "0" * 65,
        "0xasdf",
    ]
    assert all(c.error_code == -32602 for c in malformed)
    assert all(c.params[0] == str(RECIPIENT) for c in malformed)


def test_explicit_check_requires_an_expectation() -> None:
    """
    A check must expect an error or a null, and not both.

    Anything else has a spec-derived value and belongs to derivation; a
    hand-written result would reintroduce the maintained expectation this
    design avoids.
    """
    from execution_testing.specs.blockchain import RPCExpectation

    with pytest.raises(ValueError, match="written\nby hand|by hand"):
        RPCExpectation(method="eth_getBlockByNumber", params=["0x1"])

    with pytest.raises(ValueError, match="more than one kind"):
        RPCExpectation(
            method="eth_getBlockByNumber",
            params=["0x1"],
            error_code=-32602,
            expect_null=True,
        )

    with pytest.raises(ValueError, match="no rule exists"):
        RPCExpectation(
            method="eth_getBlockByNumber",
            params=["0x1"],
            derive_result=True,
        )

    RPCExpectation(method="eth_getLogs", params=[{}], derive_result=True)


def make_log_entry(address: str, topic: str, block: str) -> Dict[str, Any]:
    """Return a projected log, as the chain's own projection emits it."""
    return {
        "address": address,
        "topics": [topic],
        "data": "0x",
        "blockNumber": block,
    }


LOG_A = make_log_entry("0x" + "a1" * 20, "0x" + "aa" * 32, "0x1")
LOG_B = make_log_entry("0x" + "b2" * 20, "0x" + "bb" * 32, "0x2")


@pytest.mark.parametrize(
    "filter_,expected",
    [
        pytest.param({}, [LOG_A, LOG_B], id="unfiltered"),
        pytest.param(
            {"address": "0x" + "a1" * 20}, [LOG_A], id="single_address"
        ),
        pytest.param(
            {"address": ["0x" + "a1" * 20, "0x" + "b2" * 20]},
            [LOG_A, LOG_B],
            id="address_list",
        ),
        pytest.param(
            {"topics": ["0x" + "bb" * 32]}, [LOG_B], id="single_topic"
        ),
        pytest.param(
            {"topics": [["0x" + "aa" * 32, "0x" + "bb" * 32]]},
            [LOG_A, LOG_B],
            id="topic_alternatives",
        ),
        pytest.param({"topics": [None]}, [LOG_A, LOG_B], id="topic_wildcard"),
        pytest.param(
            {"fromBlock": "0x2", "toBlock": "0x2"}, [LOG_B], id="range"
        ),
        pytest.param(
            {"topics": ["0x" + "aa" * 32, "0x" + "bb" * 32]},
            [],
            id="filter_longer_than_topics",
        ),
        pytest.param(
            {"address": "0x" + "a1" * 20, "topics": ["0x" + "bb" * 32]},
            [],
            id="address_and_topic_must_both_match",
        ),
    ],
)
def test_log_filters(filter_: Dict[str, Any], expected: List[Any]) -> None:
    """A declared filter selects the logs the schema says it should."""
    assert filter_logs([LOG_A, LOG_B], [filter_]) == expected


def test_address_matching_ignores_hex_case() -> None:
    """A checksummed address in a filter still matches."""
    upper = ("0x" + "a1" * 20).upper().replace("0X", "0x")

    assert filter_logs([LOG_A, LOG_B], [{"address": upper}]) == [LOG_A]


@pytest.mark.parametrize(
    "filter_,reason",
    [
        pytest.param({"blockHash": "0x" + "11" * 32}, "blockHash", id="hash"),
        pytest.param({"fromBlock": "latest"}, "tag", id="tag"),
    ],
)
def test_uncomputable_filters_are_refused(
    filter_: Dict[str, Any], reason: str
) -> None:
    """
    A filter whose result the chain cannot supply is refused, not guessed.

    A block hash is unknown until after filling and a tag resolves against
    client state, so either would have to be invented.
    """
    with pytest.raises(UncomputableCallError, match=reason):
        filter_logs([LOG_A], [filter_])


def test_uncomputable_method_is_refused() -> None:
    """Only methods with a stated rule can have a result computed."""
    with pytest.raises(UncomputableCallError, match="eth_getBalance"):
        compute_result("eth_getBalance", [], [])


def access_list_calls(block: Any) -> List[Any]:
    """Return the access-list expectations derived from one block."""
    return [
        call
        for call in derive_module.derive_rpc_calls_for_blocks([block])
        if call.method == "eth_getBlockAccessList"
    ]


def test_access_list_is_queried_by_number_hash_and_tag() -> None:
    """
    Every way of naming the head block reaches the same access list.

    Three references rather than two: the head is also `latest`, and that
    tag is the one a client resolves through a different path.
    """
    block = make_block(
        [make_transaction()],
        [make_receipt(21_000)],
        block_access_list=make_access_list(),
    )

    calls = access_list_calls(block)

    assert [call.params[0] for call in calls] == [
        "0x1",
        str(block.header.block_hash),
        "latest",
    ]
    assert len({str(call.result) for call in calls}) == 1


def test_access_list_is_absent_where_the_fork_produces_none() -> None:
    """
    A fork without access lists derives no query at all.

    This is what keeps the method fork-specific without any fork knowledge
    in the derivation: a block that has an access list carries it, and a
    block that does not says nothing about one.
    """
    block = make_block([make_transaction()], [make_receipt(21_000)])

    assert access_list_calls(block) == []


def test_broken_access_list_projection_fails_at_derivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    An access list of the wrong shape never reaches a fixture.

    The negative control for a method no client implements yet: with
    nothing to replay against, the fill-time guard is the only thing
    standing between a projection bug and a release.
    """
    block = make_block(
        [make_transaction()],
        [make_receipt(21_000)],
        block_access_list=make_access_list(),
    )
    monkeypatch.setattr(
        derive_module,
        "block_access_list_response",
        lambda _block: [_BadAccountAccess()],
    )

    with pytest.raises(ProjectionError, match="projection bug"):
        derive_module.derive_rpc_calls_for_blocks([block])


class _BadAccountAccess:
    """
    Stand-in account access whose block access index is zero-padded.

    The same defect `_BadProjection` models for blocks, in the place it is
    likeliest to recur: the consensus access list stores every index as a
    `ZeroPaddedHexNumber`, so forwarding one unconverted is a single
    missing call away.
    """

    def to_rpc(self) -> Dict[str, Any]:
        """Return the defective account access object."""
        return {
            "address": str(RECIPIENT),
            "balanceChanges": [{"index": "0x01", "value": "0x1"}],
            "codeChanges": [],
            "nonceChanges": [],
            "storageChanges": [],
            "storageReads": [],
        }
