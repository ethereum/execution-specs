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

from typing import TYPE_CHECKING, List

from execution_testing.fixtures.blockchain import FixtureBlock
from execution_testing.fixtures.common import FixtureRPCCall

from .projection import block_response, receipt_responses

if TYPE_CHECKING:
    from execution_testing.fixtures.blockchain import BlockchainFixture


def derive_rpc_calls(fixture: "BlockchainFixture") -> List[FixtureRPCCall]:
    """
    Return the RPC expectations implied by a fixture's canonical chain.

    Invalid blocks are skipped: they never enter the canonical chain, so a
    client is right to report nothing for them.
    """
    calls: List[FixtureRPCCall] = []

    for block in fixture.blocks:
        if not isinstance(block, FixtureBlock):
            continue

        header = block.header
        block_result = block_response(block).to_rpc()
        number = str(block_result["number"])

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

        for receipt in receipt_responses(block):
            calls.append(
                FixtureRPCCall(
                    method="eth_getTransactionReceipt",
                    params=[str(receipt.transaction_hash)],
                    result=receipt.to_rpc(),
                )
            )

    return calls
