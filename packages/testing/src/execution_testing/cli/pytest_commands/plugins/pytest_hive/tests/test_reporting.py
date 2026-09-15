"""Unit tests for the hive reporting guard helpers."""

import json
from pathlib import Path
from typing import Any, List

import pytest
from hive.testing import HiveTestResult

from execution_testing.cli.pytest_commands.plugins.pytest_hive.reporting import (  # noqa: E501
    count_skipped_test,
    end_test_and_count,
    executed_test_ids_key,
    hive_test_started_key,
    mark_hive_test_started,
    record_test_execution,
    reported_test_ids_key,
    skipped_test_ids_key,
    verify_reported_test_count,
    write_reported_test_count,
)


class FakeSession:
    """Session double exposing what `verify_reported_test_count` reads."""

    def __init__(self, testscollected: int):  # noqa: D107
        self.testscollected = testscollected
        self.shouldstop: bool | str = False
        self.shouldfail: bool | str = False


class FakeRequest:
    """FixtureRequest double carrying only a session."""

    def __init__(self, session: FakeSession):  # noqa: D107
        self.session = session


class FakeItem:
    """Item double exposing the state used by reporting hooks."""

    def __init__(self, config: pytest.Config, nodeid: str):  # noqa: D107
        self.config = config
        self.nodeid = nodeid
        self.stash = pytest.Stash()


class FakeHiveTest:
    """HiveTest double recording its end result."""

    def __init__(self, test_id: int):  # noqa: D107
        self.id = test_id
        self.result: HiveTestResult | None = None
        self.end_calls = 0

    def end(self, *, result: HiveTestResult) -> None:  # noqa: D102
        self.end_calls += 1
        self.result = result


class FakeHiveTestSuite:
    """HiveTestSuite double recording started meta-tests."""

    def __init__(self) -> None:  # noqa: D107
        self.started: List[FakeHiveTest] = []

    def start_test(self, name: str, description: str) -> FakeHiveTest:  # noqa: D102
        del name, description
        test = FakeHiveTest(test_id=len(self.started))
        self.started.append(test)
        return test


def write_count_file(
    folder: Path,
    worker_id: str,
    *,
    reported: int,
    skipped: int,
    executed: int,
    interrupted: bool = False,
) -> None:
    """Write a per-worker reported-test count file."""
    file = folder / f"hive_reported_test_count_{worker_id}.json"
    with open(file, "w") as f:
        json.dump(
            {
                "reported": reported,
                "skipped": skipped,
                "executed": executed,
                "interrupted": interrupted,
            },
            f,
        )


def test_end_test_records_reported_nodeid(
    pytestconfig: pytest.Config, monkeypatch: Any
) -> None:
    """A successfully ended hive test is recorded exactly once."""
    monkeypatch.setitem(pytestconfig.stash, reported_test_ids_key, set())
    test = FakeHiveTest(test_id=1)
    result = HiveTestResult(test_pass=True, details="passed")

    end_test_and_count(
        pytestconfig,
        "test_module.py::test_case",
        test,  # type: ignore[arg-type]
        result,
    )

    assert test.end_calls == 1
    assert test.result == result
    assert pytestconfig.stash[reported_test_ids_key] == {
        "test_module.py::test_case"
    }


def test_end_test_failure_is_not_retried_or_recorded(
    pytestconfig: pytest.Config, monkeypatch: Any
) -> None:
    """An ambiguous end failure propagates without a duplicate request."""
    monkeypatch.setitem(pytestconfig.stash, reported_test_ids_key, set())

    class FailingHiveTest(FakeHiveTest):
        def end(self, *, result: HiveTestResult) -> None:  # noqa: D102
            del result
            self.end_calls += 1
            raise RuntimeError("response disconnected")

    test = FailingHiveTest(test_id=1)
    result = HiveTestResult(test_pass=True, details="passed")

    with pytest.raises(RuntimeError, match="response disconnected"):
        end_test_and_count(
            pytestconfig,
            "test_module.py::test_case",
            test,  # type: ignore[arg-type]
            result,
        )

    assert test.end_calls == 1
    assert pytestconfig.stash[reported_test_ids_key] == set()


def test_write_reported_test_count(
    pytestconfig: pytest.Config, tmp_path: Path, monkeypatch: Any
) -> None:
    """Counts from the config stash are written to a per-worker file."""
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw7")
    monkeypatch.setitem(
        pytestconfig.stash,
        reported_test_ids_key,
        {"test_a", "test_b", "test_c"},
    )
    monkeypatch.setitem(
        pytestconfig.stash,
        skipped_test_ids_key,
        {"test_d"},
    )
    monkeypatch.setitem(
        pytestconfig.stash,
        executed_test_ids_key,
        {"test_a", "test_b", "test_c", "test_d"},
    )
    write_reported_test_count(
        pytestconfig,
        FakeSession(testscollected=4),  # type: ignore[arg-type]
        tmp_path,
    )
    file = tmp_path / "hive_reported_test_count_gw7.json"
    with open(file, "r") as f:
        assert json.load(f) == {
            "reported": 3,
            "skipped": 1,
            "executed": 4,
            "interrupted": False,
        }


def test_count_skipped_test(
    pytestconfig: pytest.Config, monkeypatch: Any
) -> None:
    """A test skipped before hive startup is accounted for once."""
    monkeypatch.setitem(
        pytestconfig.stash,
        skipped_test_ids_key,
        set(),
    )
    item = FakeItem(pytestconfig, "test_module.py::test_skipped")
    count_skipped_test(item)  # type: ignore[arg-type]
    count_skipped_test(item)  # type: ignore[arg-type]
    assert pytestconfig.stash[skipped_test_ids_key] == {
        "test_module.py::test_skipped"
    }


def test_skip_after_hive_test_start_is_not_counted(
    pytestconfig: pytest.Config, monkeypatch: Any
) -> None:
    """A late setup skip is accounted for only by its hive result."""
    monkeypatch.setitem(pytestconfig.stash, skipped_test_ids_key, set())
    item = FakeItem(pytestconfig, "test_module.py::test_late_skip")
    mark_hive_test_started(item)  # type: ignore[arg-type]

    count_skipped_test(item)  # type: ignore[arg-type]

    assert item.stash[hive_test_started_key] is True
    assert pytestconfig.stash[skipped_test_ids_key] == set()


def test_record_test_execution_is_unique(
    pytestconfig: pytest.Config, monkeypatch: Any
) -> None:
    """Repeated reports for one item do not inflate execution counts."""
    monkeypatch.setitem(pytestconfig.stash, executed_test_ids_key, set())
    item = FakeItem(pytestconfig, "test_module.py::test_case")

    record_test_execution(item)  # type: ignore[arg-type]
    record_test_execution(item)  # type: ignore[arg-type]

    assert pytestconfig.stash[executed_test_ids_key] == {
        "test_module.py::test_case"
    }


def test_verify_passes_when_all_tests_reported(tmp_path: Path) -> None:
    """No error and no meta-test when all collected tests are reported."""
    write_count_file(tmp_path, "gw0", reported=6, skipped=0, executed=6)
    write_count_file(tmp_path, "gw1", reported=3, skipped=1, executed=4)
    suite = FakeHiveTestSuite()
    request = FakeRequest(FakeSession(testscollected=10))
    error = verify_reported_test_count(request, suite, tmp_path)  # type: ignore[arg-type]
    assert error is None
    assert suite.started == []
    # Count files are consumed by the check.
    assert list(tmp_path.glob("hive_reported_test_count_*.json")) == []


def test_verify_detects_lost_test_results(tmp_path: Path) -> None:
    """A shortfall returns an error and reports a failing hive meta-test."""
    write_count_file(tmp_path, "gw0", reported=5, skipped=0, executed=6)
    write_count_file(tmp_path, "gw1", reported=3, skipped=0, executed=4)
    suite = FakeHiveTestSuite()
    request = FakeRequest(FakeSession(testscollected=10))
    error = verify_reported_test_count(request, suite, tmp_path)  # type: ignore[arg-type]
    assert error is not None
    assert "2 test result(s) were not reported to hive" in error
    assert len(suite.started) == 1
    meta_test = suite.started[0]
    assert meta_test.result is not None
    assert meta_test.result.test_pass is False
    assert error in meta_test.result.details


def test_verify_skipped_when_peer_worker_was_interrupted(
    tmp_path: Path,
) -> None:
    """An interrupted peer prevents a false failure on the last worker."""
    write_count_file(
        tmp_path,
        "gw0",
        reported=1,
        skipped=0,
        executed=1,
        interrupted=True,
    )
    write_count_file(tmp_path, "gw1", reported=1, skipped=0, executed=1)
    suite = FakeHiveTestSuite()
    session = FakeSession(testscollected=10)
    request = FakeRequest(session)
    error = verify_reported_test_count(request, suite, tmp_path)  # type: ignore[arg-type]
    assert error is None
    assert suite.started == []


def test_verify_skipped_when_not_all_collected_tests_ran(
    tmp_path: Path,
) -> None:
    """A partial run is detected even without a local interruption flag."""
    write_count_file(tmp_path, "gw0", reported=2, skipped=0, executed=2)
    suite = FakeHiveTestSuite()
    request = FakeRequest(FakeSession(testscollected=10))

    error = verify_reported_test_count(request, suite, tmp_path)  # type: ignore[arg-type]

    assert error is None
    assert suite.started == []


def test_verify_detects_overcount(tmp_path: Path) -> None:
    """An overcount fails instead of masking another missing result."""
    write_count_file(tmp_path, "gw0", reported=10, skipped=1, executed=10)
    suite = FakeHiveTestSuite()
    request = FakeRequest(FakeSession(testscollected=10))

    error = verify_reported_test_count(request, suite, tmp_path)  # type: ignore[arg-type]

    assert error is not None
    assert "1 more hive result(s) than collected tests" in error
    assert len(suite.started) == 1


def test_xdist_early_stop_persists_interruption_across_workers(
    pytester: pytest.Pytester,
) -> None:
    """The aggregate check recognizes `-n 2 -x` as a partial run."""
    count_folder = pytester.mkdir("worker-counts")
    pytester.makeconftest(
        f"""
        import importlib
        import os
        from pathlib import Path

        import pytest

        reporting = importlib.import_module(
            "execution_testing.cli.pytest_commands.plugins."
            "pytest_hive.reporting"
        )

        count_folder = Path({str(count_folder)!r})

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            if report.when == "setup":
                reporting.record_test_execution(item)

        @pytest.fixture(scope="session", autouse=True)
        def persist_worker_counts(request):
            yield
            reporting.write_reported_test_count(
                request.config, request.session, count_folder
            )
            worker = os.environ["PYTEST_XDIST_WORKER"]
            (count_folder / f"collected_{{worker}}").write_text(
                str(request.session.testscollected)
            )
        """
    )
    pytester.makepyfile(
        """
        import time

        import pytest

        @pytest.mark.parametrize("case", range(40))
        def test_cases(case):
            if case == 0:
                pytest.fail("stop the distributed run")
            time.sleep(0.02)
        """
    )

    result = pytester.runpytest("-q", "-n", "2", "-x")

    assert result.ret == pytest.ExitCode.INTERRUPTED
    count_files = list(count_folder.glob("hive_reported_test_count_*.json"))
    counts = [json.loads(file.read_text()) for file in count_files]
    assert any(count["interrupted"] for count in counts)
    assert sum(count["executed"] for count in counts) < 40
    collected_files = count_folder.glob("collected_*")
    assert {int(file.read_text()) for file in collected_files} == {40}

    suite = FakeHiveTestSuite()
    request = FakeRequest(FakeSession(testscollected=40))
    error = verify_reported_test_count(
        request,  # type: ignore[arg-type]
        suite,  # type: ignore[arg-type]
        count_folder,
    )
    assert error is None
    assert suite.started == []
