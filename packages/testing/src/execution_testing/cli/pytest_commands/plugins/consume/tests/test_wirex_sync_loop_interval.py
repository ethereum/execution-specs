"""
Tests for the client sync loop interval of `consume wirex`.

The interval comes from the option, the simulator's environment or the
default, travels as a client environment hint, and a client that reports
its configuration is checked against it, so a run is never labeled with
an interval its client did not apply.
"""

import argparse
from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any, cast

import pytest
import requests
from hive.client import Client

from execution_testing.rpc import RPCCall
from execution_testing.rpc.rpc_types import JSONRPCResponse

from ..simulators.wirex import sync_loop_interval
from ..simulators.wirex.sync_loop_interval import (
    SYNC_LOOP_INTERVAL_VARIABLE,
    IntervalSource,
    SyncLoopInterval,
    mismatch,
    non_negative_milliseconds,
    reported_interval,
    resolve_interval,
)
from .direct_calls import fixture_body

BASE_ENVIRONMENT = {"HIVE_NETWORK_ID": "1"}
"""A client environment as `multi_test_client` caches it per group."""


def _config(interval: SyncLoopInterval) -> SimpleNamespace:
    """Return a config whose run resolved `interval`."""
    stash = pytest.Stash()
    stash[sync_loop_interval.sync_loop_interval_key] = interval
    return SimpleNamespace(stash=stash)


def _client_environment(interval: SyncLoopInterval) -> dict[str, str]:
    """Return the client environment the fixture builds for `interval`."""
    request = SimpleNamespace(config=_config(interval))
    base = dict(BASE_ENVIRONMENT)
    environment: dict[str, str] = fixture_body(sync_loop_interval.environment)(
        base, cast(pytest.FixtureRequest, request)
    )
    assert base == BASE_ENVIRONMENT, "the cached base must stay unmodified"
    return environment


class FakeRPC:
    """Answer `debug_getConfigValue` with a fixed result or error."""

    def __init__(
        self,
        result: Any = None,
        error: dict[str, Any] | None = None,
        failure: Exception | None = None,
    ) -> None:
        """Store the reply to give, or the transport `failure` to raise."""
        self.result = result
        self.error = error
        self.failure = failure
        self.calls: list[Any] = []

    def post_request(self, *, request: RPCCall) -> JSONRPCResponse:
        """Record the call and return the stored reply."""
        self.calls.append(request)
        if self.failure is not None:
            raise self.failure
        if self.error is not None:
            return JSONRPCResponse(id=1, error=self.error)
        return JSONRPCResponse(id=1, result=self.result)


INTERVAL_SOURCES = {
    "default": (None, {}, SyncLoopInterval(10, IntervalSource.DEFAULT)),
    "variable": (
        None,
        {SYNC_LOOP_INTERVAL_VARIABLE: "50"},
        SyncLoopInterval(50, IntervalSource.ENVIRONMENT),
    ),
    "option-over-variable": (
        5,
        {SYNC_LOOP_INTERVAL_VARIABLE: "50"},
        SyncLoopInterval(5, IntervalSource.OPTION),
    ),
    # An empty variable, as a Dockerfile `ENV` may leave, is unset.
    "empty-variable": (
        None,
        {SYNC_LOOP_INTERVAL_VARIABLE: " "},
        SyncLoopInterval(10, IntervalSource.DEFAULT),
    ),
    "zero-variable": (
        None,
        {SYNC_LOOP_INTERVAL_VARIABLE: "0"},
        SyncLoopInterval(0, IntervalSource.ENVIRONMENT),
    ),
    "one-ms-variable": (
        None,
        {SYNC_LOOP_INTERVAL_VARIABLE: "1"},
        SyncLoopInterval(1, IntervalSource.ENVIRONMENT),
    ),
}


@pytest.mark.parametrize(
    "option,environment,expected",
    INTERVAL_SOURCES.values(),
    ids=INTERVAL_SOURCES.keys(),
)
def test_the_interval_comes_from_option_variable_or_default(
    option: int | None,
    environment: dict[str, str],
    expected: SyncLoopInterval,
) -> None:
    """The option wins over the variable, which wins over the default."""
    assert resolve_interval(option, environment) == expected


@pytest.mark.parametrize("value", ["-5", "0.5", "fast"])
def test_a_malformed_interval_is_refused(value: str) -> None:
    """Negative and fractional values fail loudly, never fall back."""
    with pytest.raises(argparse.ArgumentTypeError):
        non_negative_milliseconds(value)
    with pytest.raises(argparse.ArgumentTypeError):
        resolve_interval(None, {SYNC_LOOP_INTERVAL_VARIABLE: value})


@pytest.mark.parametrize(
    "interval,hint",
    [
        (SyncLoopInterval(0, IntervalSource.OPTION), None),
        (SyncLoopInterval(0, IntervalSource.ENVIRONMENT), None),
        (SyncLoopInterval(10, IntervalSource.DEFAULT), "10"),
        (SyncLoopInterval(50, IntervalSource.ENVIRONMENT), "50"),
        (SyncLoopInterval(5, IntervalSource.OPTION), "5"),
    ],
)
def test_a_requested_interval_reaches_the_client_environment(
    interval: SyncLoopInterval, hint: str | None
) -> None:
    """The interval travels under the documented name, and zero not at all."""
    expected = dict(BASE_ENVIRONMENT)
    if hint is not None:
        expected["HIVE_SYNC_LOOP_INTERVAL_MS"] = hint
    assert _client_environment(interval) == expected


@pytest.mark.parametrize(
    "interval,phrases",
    [
        (
            SyncLoopInterval(10, IntervalSource.DEFAULT),
            ["10 ms", "from the wirex default", "HIVE_SYNC_LOOP_INTERVAL_MS"],
        ),
        (SyncLoopInterval(0, IntervalSource.OPTION), ["not requested"]),
    ],
)
def test_the_description_names_value_source_and_hint(
    interval: SyncLoopInterval, phrases: list[str]
) -> None:
    """The report line names the interval, its source and the hint."""
    line = interval.describe()
    assert all(phrase in line for phrase in phrases)


TRANSPORT_FAILURES = {
    "http-error-status": requests.HTTPError("500 Server Error"),
    "no-answer-after-retries": requests.ConnectionError("refused"),
    "read-timeout": requests.ReadTimeout("read timed out"),
    "refused-socket": ConnectionRefusedError("refused"),
}

REPORTS: dict[str, tuple[dict[str, Any], str | None]] = {
    "configured-text": ({"result": '"50"'}, "50"),
    "default-number": ({"result": 1000}, "1000"),
    "unknown-setting": ({"result": None}, "null"),
    **{
        f"error-{-code}": (
            {"error": {"code": code, "message": "unsupported"}},
            None,
        )
        for code in (-32601, -32600, -32602, -32603, -32000)
    },
    **{
        name: ({"failure": failure}, None)
        for name, failure in TRANSPORT_FAILURES.items()
    },
}


@pytest.mark.parametrize(
    "reply,reported", REPORTS.values(), ids=REPORTS.keys()
)
def test_the_reported_setting_is_read_by_name(
    reply: dict[str, Any], reported: str | None
) -> None:
    """
    The check asks for nethermind's sync mode selector timer. Any error,
    whatever its code, or a transport failure means the client cannot
    report, while a null answer is a wrong lookup that must not pass.
    """
    rpc = FakeRPC(**reply)
    assert reported_interval(rpc) == reported
    (call,) = rpc.calls
    assert call.method == "getConfigValue"
    assert call.params == ["SyncConfig", "MultiSyncModeSelectorLoopTimerMs"]


@pytest.mark.parametrize(
    "interval,reported,agrees",
    [
        (SyncLoopInterval(50, IntervalSource.OPTION), "50", True),
        (SyncLoopInterval(50, IntervalSource.OPTION), "null", False),
        *(
            (SyncLoopInterval(10, source), reported, False)
            for source in IntervalSource
            for reported in ("1000", "unexpected")
        ),
    ],
)
def test_a_reported_interval_must_be_the_requested_one(
    interval: SyncLoopInterval, reported: str, agrees: bool
) -> None:
    """A wrapper that ignores the hint leaves the default in place."""
    reason = mismatch(interval, reported)
    assert (reason is None) == agrees
    if reason is not None:
        assert reported in reason
        assert SYNC_LOOP_INTERVAL_VARIABLE in reason


@pytest.mark.parametrize(
    "rpc,applied",
    [
        (FakeRPC(result="50"), True),
        (FakeRPC(result="1000"), False),
        (FakeRPC(error={"code": -32601, "message": "unsupported"}), True),
    ],
    ids=["applied", "ignored", "cannot-report"],
)
def test_a_client_is_confirmed_from_what_it_reports(
    monkeypatch: pytest.MonkeyPatch, rpc: FakeRPC, applied: bool
) -> None:
    """A reported mismatch is the reason, and a silent client passes."""
    monkeypatch.setattr(
        sync_loop_interval, "DebugRPC", lambda _url: nullcontext(rpc)
    )
    reason = sync_loop_interval.confirm_interval(
        cast(Client, SimpleNamespace(ip="10.0.0.2")),
        SyncLoopInterval(50, IntervalSource.OPTION),
    )
    assert (reason is None) == applied


CLIENT = SimpleNamespace(id="client")
REASON = "the client reports SyncConfig.MultiSyncModeSelectorLoopTimerMs"


class _Request:
    """The slice of a test's request the interval gate reads."""

    def __init__(
        self, interval: SyncLoopInterval, client_type: str = "nethermind"
    ) -> None:
        """Hold a run resolved to `interval` and record what is asked."""
        self.config = _config(interval)
        self.client_type = SimpleNamespace(name=client_type)
        self.node = SimpleNamespace(user_properties=[])
        self.session = SimpleNamespace(shouldstop=False)
        self.fixtures_requested: list[str] = []

    def getfixturevalue(self, name: str) -> Any:
        """Record the request and return the test's client or its type."""
        self.fixtures_requested.append(name)
        return self.client_type if name == "client_type" else CLIENT


class TestTheIntervalGate:
    """The first client of each type is checked against the interval."""

    @pytest.fixture
    def confirmed(self, monkeypatch: pytest.MonkeyPatch) -> list[Any]:
        """Record each client check; every check reports `REASON`."""
        checks: list[Any] = []

        def confirm_interval(client: Any, interval: Any) -> str | None:
            checks.append((client, interval))
            return REASON

        monkeypatch.setattr(
            sync_loop_interval, "confirm_interval", confirm_interval
        )
        return checks

    @staticmethod
    def _gate(request: _Request) -> None:
        """Run the autouse gate fixture for one test."""
        fixture_body(sync_loop_interval._record_sync_loop_interval)(request)

    @pytest.mark.parametrize("source", list(IntervalSource))
    def test_only_an_explicit_interval_not_applied_stops_the_run(
        self,
        confirmed: list[Any],
        caplog: pytest.LogCaptureFixture,
        source: IntervalSource,
    ) -> None:
        """
        The run stops rather than carry a label it did not run under,
        while a wrapper without the hint still runs at the client's
        default, warning.
        """
        request = _Request(SyncLoopInterval(50, source))
        if source == IntervalSource.DEFAULT:
            self._gate(request)
            assert request.session.shouldstop is False
            assert f"{REASON}; continuing at the client's default" in (
                caplog.text
            )
        else:
            with pytest.raises(pytest.fail.Exception, match=REASON):
                self._gate(request)
            assert request.session.shouldstop == REASON
        assert confirmed == [(CLIENT, SyncLoopInterval(50, source))]

    def test_only_the_first_client_of_each_type_is_checked(
        self, confirmed: list[Any]
    ) -> None:
        """
        A later client of a checked type is neither set up nor checked,
        while the first of another type on the same worker still is.
        """
        interval = SyncLoopInterval(10, IntervalSource.DEFAULT)
        first, second, third = (
            _Request(interval, client_type)
            for client_type in ("go-ethereum", "go-ethereum", "nethermind")
        )
        second.config = third.config = first.config  # the same worker
        for request in (first, second, third):
            self._gate(request)
        assert first.fixtures_requested == ["client_type", "client"]
        assert second.fixtures_requested == ["client_type"]
        assert third.fixtures_requested == ["client_type", "client"]
        assert len(confirmed) == 2

    def test_every_test_records_the_requested_interval(
        self, confirmed: list[Any]
    ) -> None:
        """Each test's JUnit properties carry the interval it ran under."""
        del confirmed
        request = _Request(SyncLoopInterval(10, IntervalSource.DEFAULT))
        request.config.stash[sync_loop_interval.client_checked_key] = {
            "nethermind"
        }
        self._gate(request)
        assert request.node.user_properties == [
            ("wirex_sync_loop_interval_ms", "10")
        ]

    def test_zero_neither_checks_nor_records(
        self, confirmed: list[Any]
    ) -> None:
        """Without a hint the gate sets up no client and adds nothing."""
        request = _Request(SyncLoopInterval(0, IntervalSource.OPTION))
        self._gate(request)
        assert request.fixtures_requested == []
        assert request.node.user_properties == []
        assert confirmed == []
        stash = request.config.stash
        assert sync_loop_interval.client_checked_key not in stash
