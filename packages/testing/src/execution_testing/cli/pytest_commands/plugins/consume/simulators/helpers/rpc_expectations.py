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

Two deliberate relaxations, both required for correctness rather than
convenience:

- **Hex case is normalized.** The schema's address pattern is
  `^0x[0-9a-fA-F]{40}$`, so a client returning EIP-55 checksummed
  addresses is conforming. Byte-wise comparison would fail it.
- **Fields the expectation does not mention are ignored.** The projection
  is incomplete by design — it currently omits `withdrawals`, for
  instance — and a client returning a field we have not modelled yet is
  not thereby wrong. Only what we assert is enforced.
"""

import logging
import re
from typing import Any, Iterator, List

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


def _describe(call: FixtureRPCCall) -> str:
    """Return a short identifier for a call, for use in failures."""
    return f"{call.method}({', '.join(repr(p) for p in call.params)})"


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

    differences = list(
        _differences(_normalized(call.result), _normalized(response.result))
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
    calls: List[FixtureRPCCall] | None = fixture.rpc
    if not calls:
        return

    logger.info(f"Replaying {len(calls)} derived RPC expectations...")
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
