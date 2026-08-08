"""
Replay a fixture's derived JSON-RPC expectations against a client.

The expectations were computed from the Python spec at fill time and
stored in the fixture, so this compares the client against the
specification rather than against another client. The fixture is the
contract: pinning a fixture release pins what "correct" means, regardless
of which version of this simulator replays it.

Comparison is currently schema-based. Every response is checked against
the method's OpenRPC result schema, which catches missing required fields,
wrong types and malformed values, but not a wrong value of the right
shape. Exact comparison is the intended end state and is what the stored
results exist for; see the design notes on the two-phase rollout.
"""

import logging
from typing import Any, List

from execution_testing.fixtures import BlockchainFixture
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
    return None


def verify_rpc_expectations(
    eth_rpc: EthRPC,
    fixture: BlockchainFixture,
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
