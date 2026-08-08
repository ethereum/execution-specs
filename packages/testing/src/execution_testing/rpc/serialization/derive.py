"""
Enumerate JSON-RPC expectations from a filled blockchain fixture.

Nothing here is chosen by a test author. The calls are read off the chain
the test happened to produce: each block contributes a query by number and
by hash, and each transaction contributes a receipt lookup. The `rpc`
marker is only a switch — there is no parameter information for it to
carry.

That also bounds what this can cover. Enumeration answers "given this
chain, is the response correct"; it cannot answer "given a nonsensical
request, is the error correct", because no chain produces a nonsensical
request. Block tags, reversed ranges and missing entities belong in
hand-written tests instead.
"""

from typing import TYPE_CHECKING, Any, List, Sequence

from execution_testing.fixtures.blockchain import FixtureBlock
from execution_testing.fixtures.common import FixtureRPCCall

from .projection import (
    block_response,
    receipt_responses,
    transaction_responses,
)
from .schema import SchemaViolationError, validate_result

if TYPE_CHECKING:
    from execution_testing.fixtures.blockchain import BlockchainFixture


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


def derive_rpc_calls(fixture: "BlockchainFixture") -> List[FixtureRPCCall]:
    """Return the RPC expectations implied by a fixture's chain."""
    return derive_rpc_calls_for_blocks(fixture.blocks)


def derive_rpc_calls_for_blocks(
    blocks: Sequence[Any],
) -> List[FixtureRPCCall]:
    """
    Return the RPC expectations implied by a canonical chain.

    Takes blocks rather than a fixture because the engine formats carry
    payloads instead, and their blocks have to be assembled during
    generation where the transition tool output is still available.

    Invalid blocks are skipped: they never enter the canonical chain, so a
    client is right to report nothing for them.

    Every derived expectation is validated before being returned; see
    `_reject_unsatisfiable`.
    """
    calls: List[FixtureRPCCall] = []
    all_logs: List[Any] = []
    highest_block = 0

    for block in blocks:
        if not isinstance(block, FixtureBlock):
            continue

        header = block.header
        block_result = block_response(block).to_rpc()
        number = str(block_result["number"])
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

    _reject_unsatisfiable(calls)
    return calls
