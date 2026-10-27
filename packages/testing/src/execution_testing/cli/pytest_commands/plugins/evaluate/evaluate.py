"""
Pytest plugin for the `evaluate` command.

An evaluation test requests the `spec` fixture (a `SpecRunner` for the test's
fork), runs blocks of transactions against the spec as often as it needs,
and asserts on the results. The outcome of the test is the outcome of the
evaluation: no fixture is written.

Values a test passes to `spec.record(...)` are shown in the terminal
summary and, with `--eval-report`, written to a JSON file together with the
test's parameters.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Type

import pytest
from _pytest.terminal import TerminalReporter

from execution_testing.fixtures import BlockchainFixture
from execution_testing.forks import Fork, TransitionFork
from execution_testing.specs import BaseTest, BlockchainTest, SpecRunner
from execution_testing.specs.base import OpMode
from execution_testing.specs.evaluate import to_primitive
from execution_testing.test_types.chain_config_types import (
    DEFAULT_CHAIN_ID,
    ChainConfigDefaults,
)
from execution_testing.tools.utility.versioning import (
    get_current_commit_hash_or_tag,
)

from ..shared.helpers import is_help_or_collectonly_mode
from ..shared.pre_alloc import AllocFlags
from ..shared.transition_tool import configure_transition_tool

EVALUATION_PROPERTY = "evaluation"

EVALUATION_REPORT_VERSION = 1
"""Version of the format of the evaluation report."""

evaluation_results: List[Dict[str, Any]] = []
"""Results of the session's evaluation tests, collected by the controller."""


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    evaluate_group = parser.getgroup(
        "evaluate", "Arguments defining evaluation output"
    )
    evaluate_group.addoption(
        "--eval-report",
        action="store",
        dest="eval_report",
        type=Path,
        default=None,
        help=(
            "Path of a JSON file to write the outcome and the recorded "
            "values of every evaluation test to."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Register the markers evaluation tests use and set up the spec."""
    for marker in (
        "pre_alloc_mutable: Marks a test to allow impossible mutations in "
        "the pre-state.",
        "slow: Marks a test as slow (deselect with '-m \"not slow\"')",
        "transition_tool_cache_key: Key used to match the transition tool "
        "cache for the test.",
        "fixture_subfolder(level, prefix): Unused by evaluate; set by the "
        "forks plugin.",
    ):
        config.addinivalue_line("markers", marker)

    ChainConfigDefaults.chain_id = DEFAULT_CHAIN_ID
    config.op_mode = OpMode.CONSENSUS  # type: ignore[attr-defined]
    evaluation_results.clear()

    if is_help_or_collectonly_mode(config):
        return
    configure_transition_tool(config)


@pytest.fixture(scope="function")
def spec_type() -> Type[BaseTest]:
    """
    Return the spec type whose genesis seeds `pre`.

    Evaluations run blocks, so `pre` holds the accounts of a blockchain
    genesis.
    """
    return BlockchainTest


@pytest.fixture(scope="function")
def fixture_format() -> Any:
    """Return the fixture format whose genesis seeds `pre`."""
    return BlockchainFixture


@pytest.fixture(scope="function")
def alloc_flags(request: pytest.FixtureRequest) -> AllocFlags:
    """Return the allocation mode of the test, from its markers."""
    flags = AllocFlags.NONE
    if request.node.get_closest_marker("pre_alloc_mutable"):
        flags |= AllocFlags.MUTABLE
    return flags


@pytest.fixture(scope="function")
def dump_dir_parameter_level(
    request: pytest.FixtureRequest, base_dump_dir: Path | None
) -> Path | None:
    """Directory for the transition tool debug output of the test."""
    if base_dump_dir is None:
        return None
    return base_dump_dir / re.sub(r"[^\w.-]+", "_", request.node.nodeid)


@pytest.fixture(scope="function")
def spec(
    t8n: Any,
    fork: Fork | TransitionFork,
) -> SpecRunner:
    """Return a runner of the spec for the test's fork."""
    return SpecRunner(t8n=t8n, fork=fork)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    """Attach the evaluation's runs and records to the report of the call."""
    del call
    outcome = yield
    report: pytest.TestReport = outcome.get_result()
    if report.when != "call":
        return
    funcargs = getattr(item, "funcargs", {})
    runner = funcargs.get("spec")
    if not isinstance(runner, SpecRunner):
        return
    fork = funcargs.get("fork")
    report.user_properties.append(
        (
            EVALUATION_PROPERTY,
            {
                "fork": fork.name() if fork is not None else None,
                "params": _test_params(item),
                "runs": runner.run_count,
                "records": runner.records,
            },
        )
    )


def _test_params(item: pytest.Item) -> Dict[str, Any]:
    """
    Return the parameters of the test, other than its fork.

    A parameter that cannot be converted to built-in types is left out,
    since a report must never fail the session.
    """
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return {}
    params: Dict[str, Any] = {}
    for name, value in callspec.params.items():
        if name == "fork":
            continue
        try:
            params[name] = to_primitive(value)
        except TypeError:
            continue
    return params


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Collect the evaluation results (also from xdist workers)."""
    if report.when != "call":
        return
    for name, value in report.user_properties:
        if name != EVALUATION_PROPERTY or not isinstance(value, dict):
            continue
        result: Dict[str, Any] = {
            "test": report.nodeid,
            "outcome": report.outcome,
            **value,
        }
        if report.failed:
            result["failure"] = _failure_message(report)
        evaluation_results.append(result)


def _failure_message(report: pytest.TestReport) -> str:
    """Return the first error line of the failure (the exception message)."""
    text = report.longreprtext.strip()
    for line in text.splitlines():
        if line.startswith("E "):
            return line[1:].strip()
    return text.splitlines()[-1] if text else ""


def pytest_terminal_summary(
    terminalreporter: TerminalReporter, config: pytest.Config
) -> None:
    """Show the recorded values of every evaluation test."""
    if hasattr(config, "workerinput"):
        return
    if not evaluation_results:
        return
    terminalreporter.section("evaluation results")
    for result in sorted(evaluation_results, key=lambda r: r["test"]):
        records = " ".join(f"{k}={v}" for k, v in result["records"].items())
        line = f"{result['outcome'].upper():7} {result['test']}"
        if records:
            line += f"  {records}"
        line += f"  (runs={result['runs']})"
        if "failure" in result:
            line += f"\n        {result['failure']}"
        terminalreporter.write_line(line)


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Write the evaluation report."""
    config = session.config
    if hasattr(config, "workerinput"):
        return
    path: Path | None = config.getoption("eval_report")
    if path is None:
        return
    t8n = getattr(config, "t8n", None)
    report = {
        "version": EVALUATION_REPORT_VERSION,
        "env": {
            "t8n": t8n.version() if t8n is not None else None,
            "commit": get_current_commit_hash_or_tag(),
        },
        "results": sorted(evaluation_results, key=lambda r: r["test"]),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, default=str) + "\n")
