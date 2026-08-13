"""
Synthesize the ETH-transfer logs `traceTransfers` asks for.

These logs are not emitted by any contract and do not exist in consensus
data at all: the method manufactures an ERC-20 `Transfer` event for
every ETH movement, attributed to a fixed address that holds no code.
They are excluded from the block's bloom filter, which is the giveaway
that they are a presentation feature rather than part of the block.

Deriving them at every call depth needs value transfers reported from
inside the interpreter, which forks before EIP-7708 do not do:
`ethereum.trace` has no event for entering a message call and none of
its events carry a value. So before Amsterdam only the top-level
transfer is recoverable from outside, and the option is honoured to
that extent.

From Amsterdam the option is a **no-op**, and the reasoning is worth
stating because it is a deliberate position rather than an omission.
EIP-7708 makes a nonzero ETH transfer to a different account emit a
consensus log, which lands in the receipts whether or not
`traceTransfers` is set. The purpose the option exists to serve —
making ETH movements visible — is therefore already served before the
option is read. Synthesizing a second set of entries on top would
report every transfer twice, once per emitter address, and a consumer
counting transfers would double-count.

Two costs of that position, recorded so they are not rediscovered. A
consumer filtering on [`TRANSFER_LOG_EMITTER`] — which is exactly what
the documented behaviour instructs — sees nothing from Amsterdam. And
the scopes are close but not identical: EIP-7708 excludes
self-transfers normatively and omits the coinbase fee, the base-fee
burn and withdrawals from its closed inclusion list, so "already
reported" is not quite "reported the same way". Nothing states that
`traceTransfers` was ever meant to cover those.

The decision belongs upstream and should be raised against
`ethereum/execution-apis`: EIP-7708 does not mention `eth_simulateV1`,
the `eth_simulateV1` notes predate EIP-7708, and no client implements
both, so nobody has yet had to answer whether both logs appear.

[`TRANSFER_LOG_EMITTER`]:
    ref:ethereum_spec_tools.evm_tools.simulate.transfers.TRANSFER_LOG_EMITTER
"""

from typing import Any, List, Tuple

from ethereum_types.bytes import Bytes, Bytes20, Bytes32

from ethereum.crypto.hash import keccak256

TRANSFER_LOG_EMITTER = Bytes20(b"\xee" * 20)
"""The address `traceTransfers` attributes every synthetic transfer to."""

TRANSFER_TOPIC = keccak256(b"Transfer(address,address,uint256)")
"""The ERC-20 `Transfer` event signature, reused verbatim."""


def transfer_logs(
    log_class: Any,
    sender: Bytes20,
    recipient: Bytes20,
    value: int,
) -> Tuple[Any, ...]:
    """
    Return the synthetic log for one ETH transfer, or nothing for a zero.

    A zero-value call emits no log; a reverted call emits none either,
    which the caller enforces by not calling this at all.
    """
    if value == 0:
        return ()
    topics: List[Bytes32] = [
        Bytes32(TRANSFER_TOPIC),
        Bytes32(bytes(sender).rjust(32, b"\0")),
        Bytes32(bytes(recipient).rjust(32, b"\0")),
    ]
    return (
        log_class(
            address=TRANSFER_LOG_EMITTER,
            topics=tuple(topics),
            data=Bytes(value.to_bytes(32, "big")),
        ),
    )


__all__ = ["TRANSFER_LOG_EMITTER", "TRANSFER_TOPIC", "transfer_logs"]
