"""
Enumerate JSON-RPC expectations from a filled blockchain fixture.

Nothing here is chosen by a test author. The calls are read off the chain
the test happened to produce: each block contributes a query by number and
by hash, and each transaction contributes a receipt lookup. The `rpc`
marker is only a switch — there is no parameter information for it to
carry.

Three kinds of question do not name anything the chain produced, and are
enumerated here anyway because they are universal rather than authored:
the block tags, which resolve to blocks this chain does have; the reads of
an account that does not exist, whose values the state model fixes at zero;
and the two malformed storage keys, which fail while the parameter is being
decoded and so never reach a state lookup. None of them needs a test author
to supply anything, and emitting them per marked test costs a few short
strings.

The one exception is the `safe` and `finalized` block tags, whose answer no
chain determines: a test declares which of its blocks those are and the
consumer tells the client, so the expectation is a round trip rather than a
derivation. Those calls are flagged as such; see `_forkchoice_tag_calls`.

What remains out of reach is anything requiring a chain shaped differently
from the one the test wrote — a reversed log range, a hash belonging to
another chain. Those belong in hand-written checks.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Sequence, Tuple

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.fixtures.blockchain import FixtureBlock
from execution_testing.fixtures.common import FixtureRPCCall

from .projection import (
    block_response,
    contract_address,
    receipt_responses,
    transaction_responses,
)
from .schema import SchemaViolationError, validate_result

if TYPE_CHECKING:
    from execution_testing.fixtures.blockchain import BlockchainFixture


logger = logging.getLogger(__name__)


class ProjectionError(AssertionError):
    """
    Raised when a derived expectation does not conform to the schema.

    Distinct from `SchemaViolationError`, which reports a *client* whose
    response is wrong. This reports *us*: the projection produced an
    expectation that no conforming client could ever satisfy.
    """


def _reject_unsatisfiable(calls: List[FixtureRPCCall]) -> None:
    """
    Refuse to emit an expectation no conforming client could satisfy.

    `FixtureRPCCall.result` is `Any`, so neither the fixture model nor
    `checkfixtures` can tell a projected block from a bare string. Without
    a check here a broken projection is written into a release and reaches
    a client team as "your response is wrong", sending them to debug an
    assertion that was never valid. Validating at the point of derivation
    keeps the bad state out of the artifact entirely.

    Unknown method names are rejected by the same call, since the schema
    has no result definition to validate against.
    """
    for call in calls:
        if call.error_code is not None:
            continue  # An expected error carries no result to check.
        if call.result_keccak is not None:
            continue  # A digest has no result to validate the shape of.
        try:
            validate_result(call.method, call.result)
        except SchemaViolationError as violation:
            raise ProjectionError(
                f"derived expectation for {call.method} is not "
                f"schema-conformant, so it cannot be satisfied by any "
                f"client. This is a projection bug, not a client bug.\n"
                f"{violation}"
            ) from violation
        except KeyError as unknown:
            raise ProjectionError(
                f"derived a call to {call.method}, which the vendored "
                f"OpenRPC schema does not define"
            ) from unknown


MAX_STORAGE_SLOTS_PER_ACCOUNT = 32
"""
Cap on asserted storage slots, so one storage-heavy account cannot dominate
a fixture. Exceeding it is logged rather than silently truncated.
"""

DIGEST_LENGTH = 32
"""
Size above which a code read is asserted by digest rather than by value.

At or below it the code is no larger than the digest would be, so storing
the digest would cost more and say less.
"""

INVALID_PARAMS = -32602
"""
JSON-RPC's own code for a parameter that could not be interpreted.

Used for the malformed storage keys below. Both fail while the key is being
decoded into a 32-byte word, before any account or block is consulted, so
this is a fact about parameter parsing rather than about a chain.
"""

MALFORMED_STORAGE_KEYS = (
    "0x" + "0" * 65,
    "0xasdf",
)
"""
Storage keys no client can decode: one nibble too long, and not hex at all.

Measured against go-ethereum, which rejects both with `-32602`. The code is
asserted; the wording is not, in line with every other error here.
"""


def derive_rpc_calls(fixture: "BlockchainFixture") -> List[FixtureRPCCall]:
    """Return the RPC expectations implied by a fixture's chain."""
    return derive_rpc_calls_for_blocks(
        fixture.blocks,
        post_state=fixture.post_state,
        genesis=genesis_block(fixture),
    )


def genesis_block(fixture: "BlockchainFixture") -> FixtureBlock:
    """
    Reassemble the fixture's genesis block from its header and RLP.

    A fixture stores genesis as a header and an encoding rather than as a
    block, because nothing else needs it in block form. `withdrawals` is
    recovered from the header: a chain that commits to a withdrawals root
    reports an empty list at genesis, and an earlier one has no such field.
    """
    return FixtureBlock(
        header=fixture.genesis,
        txs=[],
        receipts=[],
        withdrawals=(
            [] if fixture.genesis.withdrawals_root is not None else None
        ),
        rlp=fixture.genesis_rlp,
    )


def touched_accounts(blocks: Sequence[Any]) -> List[Address]:
    """
    Return the accounts a chain plausibly changed, in a stable order.

    A post-state holds every pre-allocated account, most of which the test
    never went near. Asserting all of them would multiply the fixture for
    no added coverage, so the set is narrowed to the ones the blocks
    actually reach: senders, recipients, created contracts, withdrawal
    recipients, authorization authorities and the fee recipient.

    An authority is reached without ever appearing as a sender or a
    recipient, and it is the account an EIP-7702 transaction changes most
    visibly — its code becomes a delegation designator and its nonce
    advances — so leaving it out would miss the whole point of the
    transaction type.
    """
    seen: Dict[Address, None] = {}
    for block in blocks:
        if not isinstance(block, FixtureBlock):
            continue
        seen.setdefault(block.header.fee_recipient, None)
        for transaction in block.txs:
            if transaction.sender is not None:
                seen.setdefault(Address(transaction.sender), None)
            if transaction.to is not None:
                seen.setdefault(transaction.to, None)
            created = contract_address(transaction)
            if created is not None:
                seen.setdefault(created, None)
            for authorization in transaction.authorization_list or []:
                if authorization.signer is not None:
                    seen.setdefault(Address(authorization.signer), None)
        for withdrawal in block.withdrawals or []:
            seen.setdefault(withdrawal.address, None)
    return list(seen)


AccountRead = Tuple[str, List[Any], Any, Hash | None]
"""A read as (method, parameters before the block tag, result, digest)."""


def _account_reads(
    address: Address, account: Any, slots: Sequence[Tuple[Any, Any]]
) -> List[AccountRead]:
    """
    Return the four state reads for one account, minus the block tag.

    The tag is left off because each read is emitted twice; see
    `_tagged_and_untagged`.

    Contract code is asserted by digest once it is larger than the digest,
    for the reasons in `FixtureRPCCall.result_keccak`. Below that the code
    itself is both smaller and legible in a diff, which matters most for
    the two short values that carry meaning: empty code, and an EIP-7702
    delegation designator naming the account it points at.
    """
    code = Bytes(account.code or b"")
    reads: List[AccountRead] = [
        (
            "eth_getBalance",
            [str(address)],
            hex(int(account.balance or 0)),
            None,
        ),
        (
            "eth_getTransactionCount",
            [str(address)],
            hex(int(account.nonce or 0)),
            None,
        ),
        (
            "eth_getCode",
            [str(address)],
            str(code) if len(code) <= DIGEST_LENGTH else None,
            None if len(code) <= DIGEST_LENGTH else code.keccak256(),
        ),
    ]
    reads.extend(
        (
            "eth_getStorageAt",
            [str(address), str(Hash(slot))],
            str(Hash(value)),
            None,
        )
        for slot, value in slots
    )
    return reads


def _tagged_and_untagged(
    reads: Sequence[AccountRead], block_tag: str
) -> List[FixtureRPCCall]:
    """
    Emit each read twice: naming the head block, and naming no block.

    Omitting the block parameter defaults to latest, which post-merge is
    the head block the tagged form already names, so the two answers must
    agree. Asserting both is what catches a client that mishandles the
    default — a distinct code path from the one that resolves a number,
    and the reason execution-apis carries the omitted-parameter form as
    separate tests. A state read is a short string, so duplicating the
    cheapest section of the fixture is the whole cost.
    """
    calls: List[FixtureRPCCall] = []
    for method, params, result, digest in reads:
        calls.append(
            FixtureRPCCall(
                method=method,
                params=[*params, block_tag],
                result=result,
                result_keccak=digest,
            )
        )
        calls.append(
            FixtureRPCCall(
                method=method,
                params=list(params),
                result=result,
                result_keccak=digest,
            )
        )
    return calls


class _EmptyAccount:
    """
    The account the state model reports for an address that has none.

    Reading a missing account is not an error and does not return null: the
    state is a total function, so every unallocated address has zero
    balance, zero nonce, no code and an all-zero storage. Deriving those
    from the same code path as a real account keeps the four expectations
    computed rather than written down.
    """

    balance = 0
    nonce = 0
    code = b""


def _absent_account(head_block_hash: Hash) -> Address:
    """
    Return an address the chain cannot contain.

    Hashing the head block hash keeps this a parameter read off the chain
    rather than a constant a test might one day allocate, at the cost of an
    address that looks arbitrary in the fixture. Absence is still checked
    against the post-state before anything is asserted about it.
    """
    return Address(head_block_hash.keccak256()[-20:])


def _state_calls(
    blocks: Sequence[Any],
    post_state: Any,
    block_tag: str,
    head_block_hash: Hash | None,
) -> List[FixtureRPCCall]:
    """
    Return state reads for the accounts the chain touched, plus one it did
    not.

    The absent account and the malformed keys need a post-state as much as
    the real accounts do: without one there is nothing to prove an address
    is unallocated, and no account to address a well-formed request to.
    """
    if post_state is None:
        return []
    # `Alloc` is a pydantic root model with no mapping interface, while
    # tests pass a plain dict; normalize rather than special-casing.
    accounts = getattr(post_state, "root", post_state)

    calls: List[FixtureRPCCall] = []
    for address in touched_accounts(blocks):
        account = accounts.get(address)
        if account is None:
            continue
        # Not `account.storage or {}`: a `Storage` holding only zeros
        # tests as false, and a slot the chain explicitly zeroed is worth
        # asserting.
        storage = account.storage if account.storage is not None else {}
        slots = list(storage.items())
        if len(slots) > MAX_STORAGE_SLOTS_PER_ACCOUNT:
            logger.info(
                f"{address}: asserting "
                f"{MAX_STORAGE_SLOTS_PER_ACCOUNT} of {len(slots)} "
                f"storage slots"
            )
            slots = slots[:MAX_STORAGE_SLOTS_PER_ACCOUNT]
        calls.extend(
            _tagged_and_untagged(
                _account_reads(address, account, slots), block_tag
            )
        )

    if head_block_hash is not None:
        absent = _absent_account(head_block_hash)
        if accounts.get(absent) is None:
            calls.extend(
                _tagged_and_untagged(
                    _account_reads(absent, _EmptyAccount(), [(0, 0)]),
                    block_tag,
                )
            )

    calls.extend(_malformed_key_calls(accounts, blocks, block_tag))
    return calls


def _malformed_key_calls(
    accounts: Any, blocks: Sequence[Any], block_tag: str
) -> List[FixtureRPCCall]:
    """
    Return the storage reads whose key cannot be decoded.

    Addressed to an account that exists, so the only defect in the request
    is the key and a client has no other ground on which to refuse it.
    """
    addressee = next(
        (
            address
            for address in touched_accounts(blocks)
            if accounts.get(address) is not None
        ),
        None,
    )
    if addressee is None:
        return []
    return [
        FixtureRPCCall(
            method="eth_getStorageAt",
            params=[str(addressee), key, block_tag],
            error_code=INVALID_PARAMS,
        )
        for key in MALFORMED_STORAGE_KEYS
    ]


def derive_rpc_calls_for_blocks(
    blocks: Sequence[Any],
    post_state: Any = None,
    genesis: FixtureBlock | None = None,
    forkchoice_tags: Mapping[str, Hash] | None = None,
) -> List[FixtureRPCCall]:
    """
    Return the RPC expectations implied by a canonical chain.

    Takes blocks rather than a fixture because the engine formats carry
    payloads instead, and their blocks have to be assembled during
    generation where the transition tool output is still available.
    `genesis` is separate for the same reason: it is not one of them.

    Invalid blocks are skipped: they never enter the canonical chain, so a
    client is right to report nothing for them.

    `forkchoice_tags` maps `safe` and `finalized` onto blocks of this
    chain, and is supplied only where a consumer can actually declare them.
    It is the one input here that is not read off the chain; see
    `_forkchoice_tag_calls`.

    Every derived expectation is validated before being returned; see
    `_reject_unsatisfiable`.
    """
    calls: List[FixtureRPCCall] = []
    all_logs: List[Any] = []
    highest_block = 0
    head: FixtureBlock | None = None

    for block in blocks:
        if not isinstance(block, FixtureBlock):
            continue

        header = block.header
        block_result = block_response(block).to_rpc()
        number = str(block_result["number"])
        if head is None or int(header.number) >= highest_block:
            head = block
        highest_block = max(highest_block, int(header.number))

        calls.append(
            FixtureRPCCall(
                method="eth_getBlockByNumber",
                params=[number, False],
                result=block_result,
            )
        )
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockByHash",
                params=[str(header.block_hash), False],
                result=block_result,
            )
        )

        full = block_response(block, full_transactions=True).to_rpc()
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockByNumber",
                params=[number, True],
                result=full,
            )
        )
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockByHash",
                params=[str(header.block_hash), True],
                result=full,
            )
        )

        count = len(block.txs)
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockTransactionCountByNumber",
                params=[number],
                result=hex(count),
            )
        )
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockTransactionCountByHash",
                params=[str(header.block_hash)],
                result=hex(count),
            )
        )

        receipts = receipt_responses(block)
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockReceipts",
                params=[number],
                result=[receipt.to_rpc() for receipt in receipts],
            )
        )
        for receipt in receipts:
            calls.append(
                FixtureRPCCall(
                    method="eth_getTransactionReceipt",
                    params=[str(receipt.transaction_hash)],
                    result=receipt.to_rpc(),
                )
            )

        for index, transaction in enumerate(transaction_responses(block)):
            projected = transaction.to_rpc()
            calls.append(
                FixtureRPCCall(
                    method="eth_getTransactionByHash",
                    params=[str(transaction.transaction_hash)],
                    result=projected,
                )
            )
            calls.append(
                FixtureRPCCall(
                    method="eth_getTransactionByBlockNumberAndIndex",
                    params=[number, hex(index)],
                    result=projected,
                )
            )
            calls.append(
                FixtureRPCCall(
                    method="eth_getTransactionByBlockHashAndIndex",
                    params=[str(header.block_hash), hex(index)],
                    result=projected,
                )
            )

        all_logs.extend(
            log.to_rpc() for receipt in receipts for log in receipt.logs
        )

    if all_logs:
        # Only when there is at least one log. The schema types this result
        # as `oneOf` an array of log objects and an array of hashes, and an
        # empty array satisfies both, which `oneOf` forbids — so an empty
        # result is unrepresentable even though it is perfectly legal in
        # practice. Worth reporting upstream rather than working around
        # more cleverly.
        calls.append(
            FixtureRPCCall(
                method="eth_getLogs",
                params=[{"fromBlock": "0x0", "toBlock": hex(highest_block)}],
                result=all_logs,
            )
        )
    calls.append(
        FixtureRPCCall(
            method="eth_blockNumber", params=[], result=hex(highest_block)
        )
    )
    calls.extend(_tag_calls(head if head is not None else genesis, genesis))
    calls.extend(_forkchoice_tag_calls(blocks, forkchoice_tags))
    calls.extend(
        _state_calls(
            blocks,
            post_state,
            hex(highest_block),
            head.header.block_hash if head is not None else None,
        )
    )
    calls.extend(_absent_entity_calls())

    _reject_unsatisfiable(calls)
    return calls


def _tag_calls(
    head: FixtureBlock | None, genesis: FixtureBlock | None
) -> List[FixtureRPCCall]:
    """
    Return the queries that name a block by tag rather than by number.

    Post-merge `latest` is the head block and `earliest` is genesis, both
    of which are projected already, so the expectations cost nothing beyond
    a second copy of a response — which the release tarball's compression
    largely removes again.

    `safe` and `finalized` are absent here and handled by
    `_forkchoice_tag_calls` instead, because their answer comes from what
    the harness declared rather than from the chain.

    Only the full-transaction form is emitted per tag: it strictly contains
    the hash form, and the hash form is already asserted by number.
    """
    calls: List[FixtureRPCCall] = []
    for tag, block in (("earliest", genesis), ("latest", head)):
        if block is None:
            continue
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockByNumber",
                params=[tag, True],
                result=block_response(block, full_transactions=True).to_rpc(),
            )
        )
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockReceipts",
                params=[tag],
                result=[
                    receipt.to_rpc() for receipt in receipt_responses(block)
                ],
            )
        )
    return calls


FORKCHOICE_TAGS = ("safe", "finalized")
"""
The two block tags no chain can answer on its own.

Ordered head-wards first, matching the order `latest`, `safe`, `finalized`
walks back through the chain.
"""


def _forkchoice_tag_calls(
    blocks: Sequence[Any], tags: Mapping[str, Hash] | None
) -> List[FixtureRPCCall]:
    """
    Return the queries answered by what the harness declared.

    `safe` and `finalized` are the one place in this module where the
    expected value is not spec-derived. The consensus layer tells the
    execution client which blocks those are, through
    `engine_forkchoiceUpdated`, and the client's only obligation is to hand
    them back. The property is still well defined — "return the block I
    told you about" — but it is a different kind of assertion, so every
    call produced here is flagged `round_trip` and a consumer that cannot
    make the declaration must skip it rather than assert it.

    What the declaration buys is a test the recorded corpus cannot express.
    `rpc-compat` points head, safe and finalized at the *same* block, so a
    client that ignores both fields and answers with the head passes every
    tag. Because this chain is ours to shape, the three can name three
    different blocks, and then only a client tracking three separate
    pointers can answer all of them.

    A tag naming a block outside this chain is a harness bug rather than a
    client bug, and is rejected here for the same reason
    `_reject_unsatisfiable` exists: no client could satisfy it.
    """
    if not tags:
        return []
    by_hash = {
        block.header.block_hash: block
        for block in blocks
        if isinstance(block, FixtureBlock)
    }
    calls: List[FixtureRPCCall] = []
    for tag in FORKCHOICE_TAGS:
        block_hash = tags.get(tag)
        if block_hash is None:
            continue
        block = by_hash.get(block_hash)
        if block is None:
            raise ProjectionError(
                f"the {tag!r} tag names block {block_hash}, which is not a "
                f"valid block of this chain, so no client could resolve it"
            )
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockByNumber",
                params=[tag, True],
                result=block_response(block, full_transactions=True).to_rpc(),
                round_trip=True,
            )
        )
        calls.append(
            FixtureRPCCall(
                method="eth_getBlockReceipts",
                params=[tag],
                result=[
                    receipt.to_rpc() for receipt in receipt_responses(block)
                ],
                round_trip=True,
            )
        )
    return calls


def _absent_entity_calls() -> List[FixtureRPCCall]:
    """
    Return the lookups of entities that do not exist.

    The zero hash is the one hash guaranteed to name nothing: no block or
    transaction can hash to it, so the answer is null on every chain and
    needs nothing read off this one. Unlike a missing account, which has
    zero-valued fields, a missing block or transaction really is null —
    the distinction these assert.
    """
    nothing = str(Hash(0))
    return [
        FixtureRPCCall(method="eth_getTransactionByHash", params=[nothing]),
        FixtureRPCCall(method="eth_getTransactionReceipt", params=[nothing]),
        FixtureRPCCall(method="eth_getBlockByHash", params=[nothing, False]),
        FixtureRPCCall(method="eth_getBlockReceipts", params=[nothing]),
    ]
