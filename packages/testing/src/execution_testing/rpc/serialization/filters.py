"""
Compute the result of a declared call from the chain.

Derivation reads its parameters off the chain, so it can only ask
questions the chain answers: every log at once, never a filtered subset.
A test that wants to pin `eth_getLogs` topic matching has to say which
filter it means, which makes the call *declared* rather than enumerated.

The result still comes from the specification. The chain's logs are
already projected; a filter selects among them, and the selection rule is
the one the OpenRPC schema describes. Nothing here is hand-written, which
is the distinction that matters: a declared call supplies the question,
never the answer.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Sequence

from .execution import (
    UnrunnableCallError,
    compute_declared_access_list,
    compute_declared_call,
    compute_declared_estimate,
)

if TYPE_CHECKING:
    from .execution import CallSite


class UncomputableCallError(UnrunnableCallError):
    """
    Raised when a declared call has no rule for computing its result.

    A subclass of `UnrunnableCallError` so that the two reasons a
    declared result may not exist — no rule for the method, and a
    message that could not be run — are catchable as one. They are
    reported identically and neither reaches an artifact.
    """


def _matches_address(entry: Mapping[str, Any], criterion: Any) -> bool:
    """
    Return whether a log's address satisfies the filter's `address`.

    Absent means no constraint; a single address or a list of them means
    the log must name one of those.
    """
    if criterion is None:
        return True
    wanted = criterion if isinstance(criterion, list) else [criterion]
    return str(entry["address"]).lower() in {
        str(address).lower() for address in wanted
    }


def _matches_topics(entry: Mapping[str, Any], criterion: Any) -> bool:
    """
    Return whether a log's topics satisfy the filter's `topics`.

    Position `i` constrains topic `i`. `null` is a wildcard, a single
    value must match exactly, and a list matches if any of its entries
    does. A filter longer than the log's topics cannot match, but a
    shorter one leaves the remaining topics unconstrained.
    """
    if criterion is None:
        return True
    topics = [str(topic).lower() for topic in entry["topics"]]
    if len(criterion) > len(topics):
        return False
    for position, wanted in enumerate(criterion):
        if wanted is None:
            continue
        options = wanted if isinstance(wanted, list) else [wanted]
        if topics[position] not in {str(o).lower() for o in options}:
            return False
    return True


def _in_range(entry: Mapping[str, Any], filter_: Mapping[str, Any]) -> bool:
    """
    Return whether a log's block falls inside the filter's range.

    Only numeric bounds are honoured. A tag resolves against client state
    rather than the chain, so a filter naming one is refused rather than
    guessed at — see `filter_logs`.
    """
    number = int(str(entry["blockNumber"]), 16)
    low = filter_.get("fromBlock")
    high = filter_.get("toBlock")
    if low is not None and number < int(str(low), 16):
        return False
    if high is not None and number > int(str(high), 16):
        return False
    return True


BLOCK_TAGS = frozenset({"latest", "earliest", "pending", "safe", "finalized"})


def filter_logs(
    logs: Sequence[Mapping[str, Any]], params: Sequence[Any]
) -> List[Dict[str, Any]]:
    """
    Return the logs an `eth_getLogs` filter selects, in chain order.

    Order is the order the chain produced, which is what a client returns
    and what `logIndex` already encodes.
    """
    if not params or not isinstance(params[0], Mapping):
        raise UncomputableCallError(
            "eth_getLogs needs a filter object to compute a result"
        )
    filter_ = params[0]

    if "blockHash" in filter_:
        raise UncomputableCallError(
            "eth_getLogs by blockHash is not computed here; the hash is "
            "known only after filling, so declare the range instead"
        )
    for bound in ("fromBlock", "toBlock"):
        if str(filter_.get(bound, "")).lower() in BLOCK_TAGS:
            raise UncomputableCallError(
                f"eth_getLogs {bound} names a tag, which resolves against "
                "client state rather than the chain; use a block number"
            )

    return [
        dict(entry)
        for entry in logs
        if _in_range(entry, filter_)
        and _matches_address(entry, filter_.get("address"))
        and _matches_topics(entry, filter_.get("topics"))
    ]


def compute_result(
    method: str,
    params: Sequence[Any],
    logs: Sequence[Mapping[str, Any]],
    call_sites: Sequence["CallSite"] = (),
) -> Any:
    """
    Return the spec's answer to a declared call.

    Four rules exist, and they answer in different currencies. A filter
    is a *selection* over data the chain already produced, so its answer
    is the result itself. The other three are *executions*, which can end
    in a revert, and each reports one differently: `eth_call` as a
    JSON-RPC error, `eth_createAccessList` as a string beside an
    otherwise complete result, and `eth_estimateGas` as an error again,
    there being no gas limit that completes a message which reverts.
    Their answers also differ in kind — the last is a range rather than a
    value where nothing determines it. Each therefore answers with its
    own outcome object and the caller decides what the expectation
    becomes. Anything else has to be enumerated, expected to error, or
    expected to be null.
    """
    if method == "eth_getLogs":
        return filter_logs(logs, params)
    if method == "eth_call":
        return compute_declared_call(params, call_sites)
    if method == "eth_createAccessList":
        return compute_declared_access_list(params, call_sites)
    if method == "eth_estimateGas":
        return compute_declared_estimate(params, call_sites)
    raise UncomputableCallError(
        f"{method} has no rule for computing a declared result; it must "
        "expect an error or a null instead"
    )


COMPUTABLE_METHODS = frozenset(
    {"eth_getLogs", "eth_call", "eth_createAccessList", "eth_estimateGas"}
)
"""
Methods a declared call may ask to have computed.

Kept beside `compute_result` so the validation a test sees at
construction and the dispatch at fill time cannot disagree.
"""


__all__ = [
    "BLOCK_TAGS",
    "COMPUTABLE_METHODS",
    "UncomputableCallError",
    "compute_result",
    "filter_logs",
]
