"""
Replay a fixture's derived JSON-RPC expectations against a client.

The expectations were computed from the Python spec at fill time and
stored in the fixture, so this compares the client against the
specification rather than against another client. The fixture is the
contract: pinning a fixture release pins what "correct" means, regardless
of which version of this simulator replays it.

Comparison runs in two layers. The response is first checked against the
method's OpenRPC result schema, which gives a precise message for a
missing field or a malformed value, and is then compared value by value
against the stored expectation. The schema layer alone cannot catch a
wrong value of the right shape, which is the whole reason the expectation
is stored.

Three deliberate relaxations, all required for correctness rather than
convenience:

- **Hex case is normalized.** The schema's address pattern is
  `^0x[0-9a-fA-F]{40}$`, so a client returning EIP-55 checksummed
  addresses is conforming. Byte-wise comparison would fail it.
- **Set-valued fields are put in a fixed order on both sides.** An access
  list is a set of entries rather than a sequence, and no specification
  says which order a client serializes one in; see `canonical_result`.
- **Fields the expectation does not mention are ignored.** The projection
  is incomplete by design — it currently omits `withdrawals`, for
  instance — and a client returning a field we have not modelled yet is
  not thereby wrong. Only what we assert is enforced.

A handful of expectations are flagged `round_trip`, meaning their value
came from what this harness declared rather than from the spec. They are
replayed only by a consumer that made the declaration, and a failure of
one says so; see `_replayable`.

Each call also records how much of the response it pins. Most pin all of
it. A `partial` one pins the fields the spec can compute and is silent
about the rest; a `bounds` one pins a range the answer must lie in, for a
quantity the spec constrains without determining; and a `schema` one pins
no value at all — the response is held to its OpenRPC result schema and
nothing further, which is what is left for a method whose answer is a
client heuristic. All three are reported as such in the failure and
counted separately in the log, so a run's apparent coverage cannot quietly
outrun what it actually checked.
"""

import logging
import re
from collections import Counter
from typing import Any, Iterator, List

from execution_testing.base_types import Bytes
from execution_testing.fixtures.blockchain import (
    BlockchainEngineFixtureCommon,
    BlockchainFixture,
)
from execution_testing.fixtures.common import FixtureRPCCall
from execution_testing.rpc import EthRPC
from execution_testing.rpc.rpc_types import RPCCall
from execution_testing.rpc.serialization import (
    SchemaViolationError,
    validate_result,
)

logger = logging.getLogger(__name__)


ROUND_TRIP_NOTE = " [round trip: value declared by the harness, not derived]"
"""
Appended to a round-trip failure so the report says where the value came
from. A client team reading "expected block 2, got block 3" is owed the
fact that block 2 is the answer because the simulator said so in
`engine_forkchoiceUpdated`, not because the spec computed it.
"""

ASSERTION_NOTES = {
    "partial": (
        " [partial value: only the fields shown are asserted; the rest of "
        "the response has no spec-derived value]"
    ),
    "bounds": (
        " [bounds only: no exact value is derivable for this method, so "
        "the response is asserted to lie in a range rather than to equal "
        "anything — a weaker check than a value]"
    ),
    "schema": (
        " [schema only: no spec-derived value exists for this method, so "
        "only conformance to its OpenRPC result schema is asserted]"
    ),
}
"""
Appended to a failure so the report says how strong the assertion was.

The same duty `ROUND_TRIP_NOTE` discharges, one rung further down. Someone
reading a schema-only failure needs to know they are being told their
response is malformed and nothing at all about whether its value is right,
and someone reading a partial one needs to know the fields not named in
the diff were never checked. `exact` has no note, being the default the
rest of the suite is written in.
"""


def _describe(call: FixtureRPCCall) -> str:
    """Return a short identifier for a call, for use in failures."""
    described = f"{call.method}({', '.join(repr(p) for p in call.params)})"
    described += ASSERTION_NOTES.get(call.assertion, "")
    return described + (ROUND_TRIP_NOTE if call.round_trip else "")


def _unqualified(method: str, namespace: str) -> str:
    """
    Strip the namespace a client re-applies when building the request.

    Fixtures store the wire name (`eth_getBlockByNumber`) because that is
    what the OpenRPC schema keys on and what a client team reads. The RPC
    clients here are namespaced and prepend their own prefix, so passing
    the wire name through unchanged asks for `eth_eth_getBlockByNumber`.
    """
    prefix = f"{namespace}_"
    if not method.startswith(prefix):
        raise ValueError(
            f"{method} cannot be sent through a {namespace!r} client; "
            f"it needs a client for the {method.split('_')[0]!r} namespace"
        )
    return method.removeprefix(prefix)


HEX_STRING = re.compile(r"^0x[0-9a-fA-F]*$")

MAX_REPORTED_DIFFERENCES = 10
"""Cap per call, so one badly wrong response cannot bury the others."""


def _normalized(value: Any) -> Any:
    """
    Lowercase hex strings so equal values compare equal.

    Only hex is touched. Quantities and hashes are already lowercase by
    schema, so this is a no-op for them and matters only where mixed case
    is permitted.
    """
    if isinstance(value, str):
        return value.lower() if HEX_STRING.match(value) else value
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in value.items()}
    return value


def _differences(expected: Any, actual: Any, path: str = "") -> Iterator[str]:
    """
    Yield a path-anchored message for each field the response gets wrong.

    Walks the expectation rather than the response, so fields we do not
    assert are not treated as errors.
    """
    where = path or "<root>"

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            yield f"{where}: expected an object, got {type(actual).__name__}"
            return
        for key, want in expected.items():
            if key not in actual:
                yield f"{path}/{key}".lstrip("/") + ": missing from response"
                continue
            yield from _differences(
                want, actual[key], f"{path}/{key}".lstrip("/")
            )
        return

    if isinstance(expected, list):
        if not isinstance(actual, list):
            yield f"{where}: expected a list, got {type(actual).__name__}"
            return
        if len(expected) != len(actual):
            yield (
                f"{where}: expected {len(expected)} entries, got {len(actual)}"
            )
            return
        for index, (want, got) in enumerate(
            zip(expected, actual, strict=False)
        ):
            yield from _differences(want, got, f"{path}/{index}".lstrip("/"))
        return

    if expected != actual:
        yield f"{where}: expected {expected!r}, got {actual!r}"


def canonical_result(method: str, result: Any) -> Any:
    """
    Return a result with its set-valued fields put in a fixed order.

    Almost every result in this suite is a sequence whose order carries
    meaning — a block's transactions, a receipt's logs — and comparing
    those positionally is right. An access list is not one of them: it is
    a *set* of entries, and a set of keys within each entry, and no
    specification says which order a client should serialize either in.
    Comparing them positionally would fail a client whose answer is
    correct and merely differently arranged.

    Both sides are canonicalized rather than only the expectation, so the
    rule is a genuine relaxation of the comparison rather than a
    requirement that clients sort. Applied to the response of a method
    with nothing set-valued, this returns it unchanged.
    """
    if method != "eth_createAccessList" or not isinstance(result, dict):
        return result
    entries = result.get("accessList")
    if not isinstance(entries, list):
        return result
    ordered = [
        {
            **entry,
            "storageKeys": sorted(entry["storageKeys"]),
        }
        if isinstance(entry, dict)
        and isinstance(entry.get("storageKeys"), list)
        else entry
        for entry in entries
    ]
    return {
        **result,
        "accessList": sorted(
            ordered,
            key=lambda entry: str(entry.get("address", ""))
            if isinstance(entry, dict)
            else "",
        ),
    }


def _outside_bounds(call: FixtureRPCCall, result: Any) -> str | None:
    """
    Return a failure for a bounded response, or None if it lies in range.

    The two edges fail for different reasons and the report says which,
    because they are not equally interesting. Below the minimum is the
    failure the tier exists to catch: the client has named a gas limit at
    which the message it was asked about cannot complete, so anyone
    following its advice sends a transaction that runs out of gas. Above
    the maximum is a client ignoring the limit it was given, which is a
    smaller sin but still not an answer to the question asked.
    """
    assert call.bounds is not None
    if not isinstance(result, str):
        return (
            f"{_describe(call)}: expected a quantity, got "
            f"{type(result).__name__}"
        )
    value = int(result, 16)
    # Both sides in decimal. The bounds are quantities and render as hex,
    # which would leave a failure comparing a number against a string.
    minimum, maximum = int(call.bounds.minimum), int(call.bounds.maximum)
    if value < minimum:
        return (
            f"{_describe(call)}: {value} is below {minimum}, the least "
            f"gas at which this message completes, so a transaction sent "
            f"with it would run out of gas"
        )
    if value > maximum:
        return (
            f"{_describe(call)}: {value} is above {maximum}, the gas the "
            f"message itself names, which no search within that limit "
            f"could have returned"
        )
    return None


def _compare(call: FixtureRPCCall, response: Any) -> str | None:
    """
    Return a failure message for one response, or None if it is acceptable.

    Errors are compared on code only. Their wording is client-specific and
    unspecified, so matching on it would fail conforming clients.
    """
    if call.error_code is not None:
        if response.error is None:
            return (
                f"{_describe(call)}: expected error code "
                f"{call.error_code}, got a successful response"
            )
        if response.error.code != call.error_code:
            return (
                f"{_describe(call)}: expected error code "
                f"{call.error_code}, got {response.error.code}"
            )
        return None

    if response.error is not None:
        return (
            f"{_describe(call)}: expected a result, got error "
            f"{response.error.code} ({response.error.message})"
        )

    try:
        validate_result(call.method, response.result)
    except SchemaViolationError as violation:
        return f"{_describe(call)}: {violation}"

    if call.assertion == "schema":
        # The whole assertion. The schema check above has already run
        # against the full result schema — a schema-only call weakens what
        # is asserted, never how strictly the shape is judged — and there
        # is no stored value to compare against.
        return None

    if call.bounds is not None:
        return _outside_bounds(call, response.result)

    if call.result_keccak is not None:
        if not isinstance(response.result, str):
            return (
                f"{_describe(call)}: expected a hex string, got "
                f"{type(response.result).__name__}"
            )
        digest = Bytes(response.result).keccak256()
        if digest != call.result_keccak:
            return (
                f"{_describe(call)}: digest mismatch, expected "
                f"{call.result_keccak}, got {digest} "
                f"({len(response.result) // 2 - 1} bytes returned)"
            )
        return None

    differences = list(
        _differences(
            canonical_result(call.method, _normalized(call.result)),
            canonical_result(call.method, _normalized(response.result)),
        )
    )
    if not differences:
        return None

    shown = differences[:MAX_REPORTED_DIFFERENCES]
    remaining = len(differences) - len(shown)
    if remaining:
        shown.append(f"... and {remaining} more")
    return f"{_describe(call)}:\n" + "\n".join(
        f"      {difference}" for difference in shown
    )


def _replayable(
    calls: List[FixtureRPCCall],
    fixture: BlockchainFixture | BlockchainEngineFixtureCommon,
) -> List[FixtureRPCCall]:
    """
    Drop the expectations this consumer is not in a position to assert.

    A `round_trip` call is only true because someone told the client so,
    and the only channel for that is `engine_forkchoiceUpdated`. A consumer
    that never opens the engine port therefore has no standing to assert
    it: `consume rlp` waits on 8545 and sends no forkchoice update at all,
    so a client it drives has no safe or finalized block and is right to
    say so.

    The filler already keeps these out of the RLP fixture, which is why
    only the engine formats declare a forkchoice state. The check is
    repeated here so that the two facts cannot drift apart into a
    confidently wrong assertion, keyed on the declaration rather than on
    the format name: whoever can honour the declaration can assert what it
    implies, and nobody else.
    """
    declared = getattr(fixture, "rpc_forkchoice", None)
    if declared is not None:
        return calls
    replayable = [call for call in calls if not call.round_trip]
    skipped = len(calls) - len(replayable)
    if skipped:
        logger.info(
            f"Skipping {skipped} round-trip expectations: this fixture "
            f"declares no forkchoice state for them to round-trip against"
        )
    return replayable


def verify_rpc_expectations(
    eth_rpc: EthRPC,
    fixture: BlockchainFixture | BlockchainEngineFixtureCommon,
) -> None:
    """
    Check a client's responses against the fixture's stored expectations.

    Does nothing when the fixture carries no `rpc` section, which is the
    case for every test not marked `rpc`.

    All calls are sent as one batch and every mismatch is reported
    together: a client that gets one field wrong usually gets it wrong
    everywhere, and surfacing them one run at a time wastes a slow loop.
    """
    stored: List[FixtureRPCCall] | None = fixture.rpc
    if not stored:
        return
    calls = _replayable(stored, fixture)
    if not calls:
        return

    tiers = Counter(call.assertion for call in calls)
    round_trips = sum(call.round_trip for call in calls)
    logger.info(
        f"Replaying {len(calls)} RPC expectations: {tiers['exact']} exact, "
        f"{tiers['partial']} partial-value, {tiers['bounds']} bounded, "
        f"{tiers['schema']} schema-only; "
        f"{round_trips} of them round trips rather than derivations..."
    )
    responses = eth_rpc.post_batch_request(
        calls=[
            RPCCall(
                method=_unqualified(call.method, eth_rpc.namespace),
                params=call.params,
            )
            for call in calls
        ]
    )

    failures = [
        message
        for call, response in zip(calls, responses, strict=True)
        if (message := _compare(call, response)) is not None
    ]
    if failures:
        raise AssertionError(
            f"{len(failures)} of {len(calls)} RPC expectations failed:\n"
            + "\n".join(f"  - {failure}" for failure in failures)
        )
