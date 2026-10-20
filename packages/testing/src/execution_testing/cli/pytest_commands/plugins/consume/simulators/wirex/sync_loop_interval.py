"""
The client sync loop interval of `consume wirex`.

Ask clients, through the client environment hint
`HIVE_SYNC_LOOP_INTERVAL_MS`, to run their sync loop every few
milliseconds instead of on their own slower timer; a Hive client
wrapper may map the hint to its own setting, and clients without one
ignore it. Record the interval in the run's reports, since a client
that applies it runs at a non-default configuration, and check it on
the first client of each type on each worker. See
"Tuning" in `docs/running_tests/consume/wirex.md` for the reasons.
"""

import argparse
import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Protocol

import pytest
import requests
from hive.client import Client

from execution_testing.rpc import DebugRPC, RPCCall
from execution_testing.rpc.rpc_types import JSONRPCError, JSONRPCResponse

logger = logging.getLogger(__name__)

SYNC_LOOP_INTERVAL_VARIABLE = "HIVE_SYNC_LOOP_INTERVAL_MS"
"""The variable carrying the interval, in both environments."""

DEFAULT_SYNC_LOOP_INTERVAL_MS = 10
"""
The interval asked for when neither the option nor the variable is set.

Measured on nethermind: no shorter interval syncs faster, 1 ms nearly
doubles its CPU use, and no interval from 1000 ms down to 1 ms changed
any test outcome.
"""

SYNC_LOOP_INTERVAL_PROPERTY = "wirex_sync_loop_interval_ms"
"""The JUnit property recording the requested interval on every test."""

REPORTED_SETTING = ("SyncConfig", "MultiSyncModeSelectorLoopTimerMs")
"""
The category and name of nethermind's setting the hint maps to.

The category is the configuration class name, `SyncConfig`, although its
configuration files and command line call it `Sync`.
"""


class IntervalSource(StrEnum):
    """Where a run's interval can come from."""

    OPTION = "option"
    ENVIRONMENT = "environment"
    DEFAULT = "default"


SOURCES: Mapping[IntervalSource, str] = {
    IntervalSource.OPTION: "--wirex-sync-loop-interval",
    IntervalSource.ENVIRONMENT: SYNC_LOOP_INTERVAL_VARIABLE,
    IntervalSource.DEFAULT: "the wirex default",
}
"""How reports name each source of an interval."""


class RequestPoster(Protocol):
    """The part of an RPC client that `reported_interval` uses."""

    def post_request(self, *, request: RPCCall) -> JSONRPCResponse:
        """Send `request` and return the response."""
        ...


@dataclass(frozen=True)
class SyncLoopInterval:
    """The interval a run asks clients for, and where it came from."""

    milliseconds: int
    """The interval; `0` means no hint is sent."""

    source: IntervalSource
    """Where the interval came from."""

    @property
    def requested(self) -> bool:
        """Return whether a hint is sent to clients."""
        return self.milliseconds > 0

    @property
    def explicit(self) -> bool:
        """Return whether the run asked for this interval itself."""
        return self.source != IntervalSource.DEFAULT

    def describe(self) -> str:
        """Return the one-line statement of the setting used in reports."""
        if not self.requested:
            return (
                f"client sync loop interval: not requested "
                f"({SOURCES[self.source]} is 0), clients use their own"
            )
        return (
            f"client sync loop interval: {self.milliseconds} ms from "
            f"{SOURCES[self.source]}, sent as {SYNC_LOOP_INTERVAL_VARIABLE} "
            f"(non-default configuration for clients that apply it)"
        )


def non_negative_milliseconds(value: str) -> int:
    """
    Parse a sync loop interval in whole milliseconds.

    `0` means no interval is requested. It is not a short interval:
    nethermind fails to start its sync mode selector at zero and then
    never syncs, so it must never reach a client.
    """
    try:
        milliseconds = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"expected a whole number of milliseconds, got {value!r}"
        ) from error
    if milliseconds < 0:
        raise argparse.ArgumentTypeError(
            f"the interval must not be negative, got {milliseconds}"
        )
    return milliseconds


def resolve_interval(
    option: int | None, environment: Mapping[str, str]
) -> SyncLoopInterval:
    """
    Return the interval from the option, the environment or the default.

    Raise `argparse.ArgumentTypeError` for an invalid variable value.
    """
    if option is not None:
        return SyncLoopInterval(option, IntervalSource.OPTION)
    value = environment.get(SYNC_LOOP_INTERVAL_VARIABLE, "")
    if value.strip():
        return SyncLoopInterval(
            non_negative_milliseconds(value.strip()),
            IntervalSource.ENVIRONMENT,
        )
    return SyncLoopInterval(
        DEFAULT_SYNC_LOOP_INTERVAL_MS, IntervalSource.DEFAULT
    )


sync_loop_interval_key = pytest.StashKey[SyncLoopInterval]()

client_checked_key = pytest.StashKey[set[str]]()
"""The client types whose interval this worker has checked."""


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the sync loop interval option."""
    group = parser.getgroup("wirex", "Arguments for the wirex simulator")
    group.addoption(
        "--wirex-sync-loop-interval",
        action="store",
        dest="wirex_sync_loop_interval",
        type=non_negative_milliseconds,
        default=None,
        help=(
            "Sync loop interval, in milliseconds, to ask clients for "
            f"through {SYNC_LOOP_INTERVAL_VARIABLE}; 0 sends no hint. "
            f"Default: the simulator's own {SYNC_LOOP_INTERVAL_VARIABLE}, "
            f"else {DEFAULT_SYNC_LOOP_INTERVAL_MS} ms. Clients that "
            "start a sync only on a fixed timer (nethermind) spend most "
            "of a short sync waiting for it."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Resolve the run's interval once, failing on an invalid variable."""
    try:
        interval = resolve_interval(
            config.getoption("wirex_sync_loop_interval", None), os.environ
        )
    except argparse.ArgumentTypeError as error:
        raise pytest.UsageError(
            f"{SYNC_LOOP_INTERVAL_VARIABLE}: {error}"
        ) from error
    config.stash[sync_loop_interval_key] = interval


def run_interval(config: pytest.Config) -> SyncLoopInterval:
    """Return the run's resolved interval."""
    return config.stash[sync_loop_interval_key]


def pytest_report_header(config: pytest.Config) -> list[str]:
    """State the sync loop interval in the report header."""
    return [run_interval(config).describe()]


@pytest.fixture(scope="module")
def test_suite_description(
    test_suite_description: str, request: pytest.FixtureRequest
) -> str:
    """Extend the wirex suite description with a requested interval."""
    interval = run_interval(request.config)
    if not interval.requested:
        return test_suite_description
    return f"{test_suite_description} The {interval.describe()}."


@pytest.fixture(scope="function")
def environment(
    environment: dict[str, str], request: pytest.FixtureRequest
) -> dict[str, str]:
    """
    Add the sync loop interval hint to the client environment.

    Extends the `multi_test_client` fixture of the same name, whose
    result is cached per pre-allocation group and must stay unmodified.
    """
    interval = run_interval(request.config)
    if not interval.requested:
        return environment
    return {
        **environment,
        SYNC_LOOP_INTERVAL_VARIABLE: str(interval.milliseconds),
    }


def reported_interval(rpc: RequestPoster) -> str | None:
    """
    Return the interval `rpc`'s client reports it runs with.

    `None` means the client answers `debug_getConfigValue`, which only
    nethermind implements, with an error of any code, or the request
    fails in transport (an HTTP error status, or no answer after the
    RPC client's retries), so the interval cannot be confirmed. A
    client that has the method but no such setting reports `"null"`,
    which is a mismatch, never a pass.
    """
    category, name = REPORTED_SETTING
    try:
        value = rpc.post_request(
            request=RPCCall(method="getConfigValue", params=[category, name])
        ).result_or_raise()
    except (JSONRPCError, requests.RequestException, OSError) as error:
        logger.debug(f"debug_getConfigValue unavailable: {error!r}")
        return None
    return "null" if value is None else str(value).strip('"')


def mismatch(interval: SyncLoopInterval, reported: str) -> str | None:
    """Return why a client's reported interval disagrees, or `None`."""
    try:
        if int(reported) == interval.milliseconds:
            return None
    except ValueError:
        pass
    return (
        f"A {interval.milliseconds} ms sync loop interval was requested "
        f"(from {SOURCES[interval.source]}), but the client reports "
        f"{'.'.join(REPORTED_SETTING)} = {reported}: its Hive client "
        f"wrapper does not map {SYNC_LOOP_INTERVAL_VARIABLE}"
    )


def confirm_interval(client: Client, interval: SyncLoopInterval) -> str | None:
    """
    Return why `client` did not apply `interval`, or `None` if it did.

    A client that cannot report its configuration is given the benefit of
    the doubt, with a warning.
    """
    with DebugRPC(f"http://{client.ip}:8545") as rpc:
        reported = reported_interval(rpc)
    if reported is None:
        logger.warning(
            f"The client does not report its configuration; cannot "
            f"confirm the requested {interval.milliseconds} ms sync loop "
            f"interval"
        )
        return None
    reason = mismatch(interval, reported)
    if reason is None:
        logger.info(f"The client confirms a {reported} ms sync loop interval")
    return reason


@pytest.fixture(scope="function", autouse=True)
def _record_sync_loop_interval(request: pytest.FixtureRequest) -> None:
    """
    Record a requested interval on the test and check the first client
    of each type.

    The client is requested only when an interval is, so runs without
    one set up exactly the fixtures they did before. The check is per
    client type, since a client that cannot report must not use up the
    check for a later one that can.
    """
    interval = run_interval(request.config)
    if not interval.requested:
        return
    request.node.user_properties.append(
        (SYNC_LOOP_INTERVAL_PROPERTY, str(interval.milliseconds))
    )
    client_type = request.getfixturevalue("client_type")
    checked = request.config.stash.setdefault(client_checked_key, set())
    if client_type.name in checked:
        return
    client = request.getfixturevalue("client")
    checked.add(client_type.name)
    reason = confirm_interval(client, interval)
    if reason is None:
        return
    if not interval.explicit:
        # A Hive whose client wrapper predates the hint: the run is still
        # a valid run at the client's own default, so carry on, loudly.
        logger.warning(f"{reason}; continuing at the client's default")
        return
    # `shouldstop` rather than `pytest.exit`: an exit inside an xdist
    # worker crashes it, while `shouldstop` reaches the controller, which
    # stops the whole run with this reason.
    logger.error(reason)
    request.session.shouldstop = reason
    pytest.fail(reason)
