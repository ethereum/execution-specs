"""Tests for the `--timing-data` report, with and without xdist."""

import textwrap
from typing import Any

import pytest

CONFTEST = textwrap.dedent(
    """\
    import pytest

    pytest_plugins = [
        "execution_testing.cli.pytest_commands.plugins.consume."
        "simulators.timing_data",
    ]


    @pytest.fixture
    def client():
        return None
    """
)

TEST_MODULE = textwrap.dedent(
    """\
    def test_timed(timing_data):
        with timing_data.time("Step"):
            pass
    """
)


@pytest.mark.parametrize(
    "flag,workers", [(True, None), (True, "2"), (False, None)]
)
def test_timing_data_reaches_the_report(
    pytester: Any, capsys: Any, flag: bool, workers: str | None
) -> None:
    """Only `--timing-data` prints and records each test's timing data."""
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(test_timed=TEST_MODULE)
    junit = pytester.path / "report.xml"
    args = [f"--junitxml={junit}", "-p", "no:cacheprovider"]
    if flag:
        args.append("--timing-data")
    if workers is not None:
        args += ["-n", workers]
    result = pytester.runpytest_subprocess(*args)
    capsys.readouterr()

    assert result.ret == pytest.ExitCode.OK
    output = "\n".join(result.outlines)
    assert output.count("Total (seconds)") == int(flag)
    assert ("Step:" in output) is flag
    assert ('name="timing_data"' in junit.read_text()) is flag
    if flag:
        assert "test_timed.py::test_timed" in output
