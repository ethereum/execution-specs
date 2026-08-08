"""
Enumerate JSON-RPC expectations from a filled blockchain fixture.

Nothing here is chosen by a test author. The calls are read off the chain
the test happened to produce: each block contributes a query by number and
by hash, and each transaction contributes a receipt lookup. The `rpc`
marker is only a switch — there is no parameter information for it to
carry.

The block tags are the one exception. They name nothing the chain
produced, but they resolve to blocks it does have, so no test author has
to supply anything for them either.

What remains out of reach is anything requiring a chain shaped differently
from the one the test wrote — a reversed log range, a hash belonging to
another chain. Those belong in hand-written checks.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Sequence

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
    recipients and the fee recipient.
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
        for withdrawal in block.withdrawals or []:
            seen.setdefault(withdrawal.address, None)
    return list(seen)


def _state_calls(
    blocks: Sequence[Any], post_state: Any, block_tag: str
) -> List[FixtureRPCCall]:
    """
    Return state reads for the accounts the chain touched.

    Contract code is asserted by digest; see `FixtureRPCCall.result_keccak`.
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
        calls.append(
            FixtureRPCCall(
                method="eth_getBalance",
                params=[str(address), block_tag],
                result=hex(int(account.balance or 0)),
            )
        )
        calls.append(
            FixtureRPCCall(
                method="eth_getTransactionCount",
                params=[str(address), block_tag],
                result=hex(int(account.nonce or 0)),
            )
        )
        code = Bytes(account.code or b"")
        calls.append(
            FixtureRPCCall(
                method="eth_getCode",
                params=[str(address), block_tag],
                result_keccak=code.keccak256(),
            )
        )
        slots = list((account.storage or {}).items())
        if len(slots) > MAX_STORAGE_SLOTS_PER_ACCOUNT:
            logger.info(
                f"{address}: asserting "
                f"{MAX_STORAGE_SLOTS_PER_ACCOUNT} of {len(slots)} "
                f"storage slots"
            )
            slots = slots[:MAX_STORAGE_SLOTS_PER_ACCOUNT]
        for slot, value in slots:
            calls.append(
                FixtureRPCCall(
                    method="eth_getStorageAt",
                    params=[str(address), str(Hash(slot)), block_tag],
                    result=str(Hash(value)),
                )
            )
    return calls


def derive_rpc_calls_for_blocks(
    blocks: Sequence[Any],
    post_state: Any = None,
    genesis: FixtureBlock | None = None,
) -> List[FixtureRPCCall]:
    """
    Return the RPC expectations implied by a canonical chain.

    Takes blocks rather than a fixture because the engine formats carry
    payloads instead, and their blocks have to be assembled during
    generation where the transition tool output is still available.
    `genesis` is separate for the same reason: it is not one of them.

    Invalid blocks are skipped: they never enter the canonical chain, so a
    client is right to report nothing for them.

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
    calls.extend(_state_calls(blocks, post_state, hex(highest_block)))

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

    `safe` and `finalized` are deliberately absent. Neither consume
    simulator sets a safe or a finalized block in its forkchoice state, and
    go-ethereum answers both with `-32000 safe block not found` rather than
    with the head. Asserting the head there would encode our own harness's
    forkchoice, and asserting the error would encode its absence; setting
    the two to the head instead would forbid the reorgs other tests depend
    on. The tags stay out until something makes them mean the chain rather
    than the harness.

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
