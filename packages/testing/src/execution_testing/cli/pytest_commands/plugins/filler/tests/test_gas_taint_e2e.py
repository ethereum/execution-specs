"""
End-to-end pytester tests for the gas_taint plugin.

These tests load the real fill plugin chain into a pytester subprocess
and verify that ``--detect-gas-checks`` produces the expected JSON
report. They cover the integration that the unit tests in
``test_gas_taint.py`` deliberately don't:

- ``pytest_addoption`` / ``pytest_configure`` parse and propagate the
  flag.
- ``install_taint`` runs once at session start.
- The hook inside ``BaseTestWrapper.__init__`` actually fires for each
  test and pushes hits into ``request.config._gas_taint_results``.
- ``pytest_sessionfinish`` / ``pytest_testnodedown`` write the JSON
  report to the path given to ``--gas-check-report``.

Each test runs a full ``fill`` invocation against a synthetic test
module, so an actual t8n binary must be available (defaults to ``evm``;
override with ``EVM_BIN`` like the benchmarking tests).
"""

import json
import os
import textwrap
from pathlib import Path

import pytest

GAS_TAINT_EVM_T8N = os.environ.get("EVM_BIN", "evm")


# A synthetic test module that asserts a gas-derived value in post
# storage via ``CodeGasMeasure``. Picks up via the ``storage`` sink kind
# in the report.
GAS_CHECK_TEST_MODULE = textwrap.dedent(
    """\
    import pytest
    from execution_testing import (
        Account,
        Alloc,
        CodeGasMeasure,
        Environment,
        Op,
        StateTestFiller,
        Transaction,
    )

    @pytest.mark.valid_at("Cancun")
    def test_dummy_gas_check(
        state_test: StateTestFiller, pre: Alloc, fork
    ) -> None:
        gas_measure = CodeGasMeasure(code=Op.PUSH1[1] + Op.POP)
        expected_gas = (Op.PUSH1[1] + Op.POP).gas_cost(fork)
        contract = pre.deploy_contract(code=gas_measure)
        sender = pre.fund_eoa()
        state_test(
            env=Environment(),
            pre=pre,
            post={contract: Account(storage={0: expected_gas})},
            tx=Transaction(sender=sender, to=contract, gas_limit=200_000),
        )
    """
)


# A synthetic OOG-style test marked with ``exception_test``. The walker
# must skip it even though it ends up running through the same hook.
OOG_TEST_MODULE = textwrap.dedent(
    """\
    import pytest
    from execution_testing import (
        Account,
        Alloc,
        Environment,
        Op,
        StateTestFiller,
        Transaction,
        TransactionException,
    )

    @pytest.mark.valid_at("Cancun")
    @pytest.mark.exception_test
    def test_dummy_oog(
        state_test: StateTestFiller, pre: Alloc
    ) -> None:
        contract = pre.deploy_contract(code=Op.STOP)
        sender = pre.fund_eoa()
        state_test(
            env=Environment(),
            pre=pre,
            post={},
            tx=Transaction(
                sender=sender,
                to=contract,
                gas_limit=20_999,
                error=TransactionException.INTRINSIC_GAS_TOO_LOW,
            ),
        )
    """
)


def _setup_pytester(
    pytester: pytest.Pytester, test_content: str, filename: str
) -> Path:
    """Drop a synthetic test module under ``tests/`` and copy fill.ini."""
    tests_dir = pytester.mkdir("tests")
    dummy_dir = tests_dir / "dummy_module"
    dummy_dir.mkdir()
    module_path = dummy_dir / filename
    module_path.write_text(test_content)
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return module_path


def test_detect_gas_checks_option_added(pytester: pytest.Pytester) -> None:
    """``--detect-gas-checks`` appears in ``fill --help``."""
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    result = pytester.runpytest("-c", "pytest-fill.ini", "--help")
    assert result.ret == 0
    assert any("--detect-gas-checks" in line for line in result.outlines), (
        "expected --detect-gas-checks in help output"
    )
    assert any("--gas-check-report" in line for line in result.outlines), (
        "expected --gas-check-report in help output"
    )


def test_gas_check_report_records_storage_hit(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    """A synthetic CodeGasMeasure test ends up in the JSON report."""
    _setup_pytester(pytester, GAS_CHECK_TEST_MODULE, "test_dummy_gas.py")
    report_path = tmp_path / "gas_check_report.json"
    output_dir = tmp_path / "fixtures"

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Cancun",
        "--detect-gas-checks",
        f"--gas-check-report={report_path}",
        "--no-html",
        "--skip-index",
        f"--output={output_dir}",
        "tests/dummy_module/",
        "-q",
    )
    assert result.ret == 0, f"fill failed:\n{result.outlines}"
    assert report_path.exists(), "expected report file to be written"

    report = json.loads(report_path.read_text())
    storage_entries = [
        (nodeid, hit)
        for nodeid, hits in report.items()
        for hit in hits
        if hit["kind"] == "storage"
    ]
    assert storage_entries, (
        f"expected at least one storage hit; got {report!r}"
    )
    for _, hit in storage_entries:
        # Origins should mention either Bytecode.gas_cost or one of the
        # underlying gas_costs.* constants.
        assert any("gas" in origin for origin in hit["origins"]), (
            f"unexpected origins for hit {hit!r}"
        )


def test_gas_check_report_excludes_oog_test(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    """Tests marked ``exception_test`` are excluded from the report."""
    _setup_pytester(pytester, OOG_TEST_MODULE, "test_dummy_oog.py")
    report_path = tmp_path / "gas_check_report.json"
    output_dir = tmp_path / "fixtures"

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Cancun",
        "--detect-gas-checks",
        f"--gas-check-report={report_path}",
        "--no-html",
        "--skip-index",
        f"--output={output_dir}",
        "tests/dummy_module/",
        "-q",
    )
    assert result.ret == 0, f"fill failed:\n{result.outlines}"
    assert report_path.exists()

    report = json.loads(report_path.read_text())
    # No entry should reference the OOG test.
    assert not any("test_dummy_oog" in nodeid for nodeid in report), (
        f"OOG test should be excluded; got report keys: {list(report)!r}"
    )


def test_no_report_written_without_flag(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    """Without ``--detect-gas-checks`` no report file is produced."""
    _setup_pytester(pytester, GAS_CHECK_TEST_MODULE, "test_dummy_gas.py")
    report_path = tmp_path / "gas_check_report.json"
    output_dir = tmp_path / "fixtures"

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Cancun",
        f"--gas-check-report={report_path}",  # path supplied but flag off
        "--no-html",
        "--skip-index",
        f"--output={output_dir}",
        "tests/dummy_module/",
        "-q",
    )
    assert result.ret == 0, f"fill failed:\n{result.outlines}"
    assert not report_path.exists(), (
        "report must not be written when detector is disabled"
    )
