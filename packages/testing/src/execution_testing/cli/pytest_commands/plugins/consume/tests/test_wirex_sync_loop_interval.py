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
    DEFAULT_SYNC_LOOP_INTERVAL_MS,
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


@pytest.mark.parametrize("value,expected", [("0", 0), ("1", 1), ("50", 50)])
def test_whole_intervals_parse(value: str, expected: int) -> None:
    """Whole milliseconds are accepted; zero means no hint."""
    assert non_negative_milliseconds(value) == expected


@pytest.mark.parametrize("value", ["-5", "0.5", "fast"])
def test_other_intervals_are_rejected(value: str) -> None:
    """Negative and fractional values are refused."""
    with pytest.raises(argparse.ArgumentTypeError):
        non_negative_milliseconds(value)


def test_the_default_applies_without_option_or_variable() -> None:
    """With nothing set, the run asks for the default interval."""
    interval = resolve_interval(None, {})
    assert interval == SyncLoopInterval(
        DEFAULT_SYNC_LOOP_INTERVAL_MS, IntervalSource.DEFAULT
    )
    assert interval.requested and not interval.explicit


def test_the_variable_overrides_the_default() -> None:
    """A Hive simulator image sets the interval through the variable."""
    interval = resolve_interval(None, {SYNC_LOOP_INTERVAL_VARIABLE: "50"})
    assert interval == SyncLoopInterval(50, IntervalSource.ENVIRONMENT)
    assert interval.explicit


def test_the_option_overrides_the_variable() -> None:
    """A local run's option wins over the environment."""
    interval = resolve_interval(5, {SYNC_LOOP_INTERVAL_VARIABLE: "50"})
    assert interval == SyncLoopInterval(5, IntervalSource.OPTION)


def test_an_empty_variable_is_unset() -> None:
    """An empty variable, as a Dockerfile `ENV` may leave, is ignored."""
    interval = resolve_interval(None, {SYNC_LOOP_INTERVAL_VARIABLE: " "})
    assert interval.source == "default"


def test_an_invalid_variable_is_refused() -> None:
    """A malformed variable fails loudly rather than falling back."""
    with pytest.raises(argparse.ArgumentTypeError):
        resolve_interval(None, {SYNC_LOOP_INTERVAL_VARIABLE: "fast"})


@pytest.mark.parametrize(
    "source", [IntervalSource.OPTION, IntervalSource.ENVIRONMENT]
)
def test_zero_sends_no_hint(source: IntervalSource) -> None:
    """Zero leaves the client environment without the hint."""
    interval = SyncLoopInterval(0, source)
    assert not interval.requested
    assert "not requested" in interval.describe()
    assert _client_environment(interval) == BASE_ENVIRONMENT


@pytest.mark.parametrize(
    "interval,value",
    [
        (SyncLoopInterval(10, IntervalSource.DEFAULT), "10"),
        (SyncLoopInterval(50, IntervalSource.ENVIRONMENT), "50"),
        (SyncLoopInterval(5, IntervalSource.OPTION), "5"),
    ],
)
def test_a_requested_interval_reaches_the_client_environment(
    interval: SyncLoopInterval, value: str
) -> None:
    """The resolved interval is added under the documented hint name."""
    assert _client_environment(interval) == {
        **BASE_ENVIRONMENT,
        "HIVE_SYNC_LOOP_INTERVAL_MS": value,
    }


def test_the_description_names_value_source_and_hint() -> None:
    """The report line names the interval, its source and the hint."""
    line = SyncLoopInterval(10, IntervalSource.DEFAULT).describe()
    assert "10 ms" in line
    assert "from the wirex default" in line
    assert SYNC_LOOP_INTERVAL_VARIABLE in line
    assert "non-default" in line


def test_the_reported_setting_is_requested_by_name() -> None:
    """The check asks for nethermind's sync mode selector timer."""
    rpc = FakeRPC(result="50")
    assert reported_interval(rpc) == "50"
    (call,) = rpc.calls
    assert call.method == "getConfigValue"
    assert call.params == ["SyncConfig", "MultiSyncModeSelectorLoopTimerMs"]


@pytest.mark.parametrize("result,expected", [(1000, "1000"), ('"50"', "50")])
def test_reported_values_are_normalized(result: Any, expected: str) -> None:
    """A default comes back as a number, a configured value as text."""
    assert reported_interval(FakeRPC(result=result)) == expected


def test_an_unknown_setting_is_a_mismatch() -> None:
    """A null answer means a wrong lookup, which must not pass."""
    reported = reported_interval(FakeRPC(result=None))
    assert reported == "null"
    assert (
        mismatch(SyncLoopInterval(50, IntervalSource.OPTION), reported)
        is not None
    )


@pytest.mark.parametrize("code", [-32601, -32600, -32602, -32603, -32000])
def test_any_error_means_the_client_cannot_report(code: int) -> None:
    """Clients differ in the error they give for an unknown method."""
    rpc = FakeRPC(error={"code": code, "message": "unsupported"})
    assert reported_interval(rpc) is None


TRANSPORT_FAILURES = {
    "http-error-status": requests.HTTPError("500 Server Error"),
    "no-answer-after-retries": requests.ConnectionError("refused"),
    "read-timeout": requests.ReadTimeout("read timed out"),
    "refused-socket": ConnectionRefusedError("refused"),
}


@pytest.mark.parametrize(
    "failure", TRANSPORT_FAILURES.values(), ids=TRANSPORT_FAILURES.keys()
)
def test_a_transport_failure_means_the_client_cannot_report(
    failure: Exception,
) -> None:
    """A request that fails in transport is no answer, not a crash."""
    assert reported_interval(FakeRPC(failure=failure)) is None


def test_an_applied_interval_agrees() -> None:
    """The requested interval, reported back, is no mismatch."""
    assert mismatch(SyncLoopInterval(50, IntervalSource.OPTION), "50") is None


@pytest.mark.parametrize("reported", ["1000", "unexpected"])
@pytest.mark.parametrize("source", list(IntervalSource))
def test_an_ignored_interval_is_a_mismatch(
    source: IntervalSource, reported: str
) -> None:
    """A wrapper that ignores the hint leaves the default in place."""
    reason = mismatch(SyncLoopInterval(10, source), reported)
    assert reason is not None
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

    @pytest.mark.parametrize(
        "source", [IntervalSource.OPTION, IntervalSource.ENVIRONMENT]
    )
    def test_an_explicit_interval_not_applied_stops_the_run(
        self, confirmed: list[Any], source: IntervalSource
    ) -> None:
        """The run stops rather than carry a label it did not run under."""
        request = _Request(SyncLoopInterval(50, source))
        with pytest.raises(pytest.fail.Exception, match=REASON):
            self._gate(request)
        assert request.session.shouldstop == REASON
        assert confirmed == [(CLIENT, SyncLoopInterval(50, source))]

    def test_the_default_not_applied_only_warns(
        self, confirmed: list[Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A wrapper without the hint still runs at the client's default."""
        request = _Request(SyncLoopInterval(10, IntervalSource.DEFAULT))
        self._gate(request)
        assert request.session.shouldstop is False
        assert len(confirmed) == 1
        assert f"{REASON}; continuing at the client's default" in caplog.text

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
