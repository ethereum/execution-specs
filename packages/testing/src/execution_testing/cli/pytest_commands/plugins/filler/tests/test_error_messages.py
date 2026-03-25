"""Regression tests for fill error messages."""

import subprocess
import sys
import textwrap
from typing import Any

invalid_fee_payment_test_module = textwrap.dedent(
    """\
    from execution_testing import Transaction


    def test_invalid_fee_payment_error(state_test, pre) -> None:
        tx = Transaction(
            to=0,
            gas_limit=21_000,
            sender=pre.fund_eoa(),
            gas_price=1,
            max_fee_per_gas=2,
        )
        state_test(pre=pre, post={}, tx=tx)
    """
)


def test_fill_reports_conflicting_fee_fields(pytester: Any) -> None:
    """Test that fill surfaces the conflicting fee fields in failures."""
    tests_dir = pytester.mkdir("tests")
    berlin_tests_dir = tests_dir / "berlin"
    berlin_tests_dir.mkdir()
    fee_test_dir = berlin_tests_dir / "invalid_fee_payment_module"
    fee_test_dir.mkdir()
    test_module = fee_test_dir / "test_invalid_fee_payment_error.py"
    test_module.write_text(invalid_fee_payment_test_module)

    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest-fill.ini",
            "--fork",
            "Berlin",
            "-m",
            "state_test",
            "--no-html",
            "--output=stdout",
            str(test_module),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=pytester.path,
    )

    assert result.returncode != 0, "Fill command was expected to fail"

    output = "\n".join((result.stdout, result.stderr))
    expected_message = (
        "cannot mix fee fields in a single tx: "
        "'gas_price' (legacy/type-1), 'max_fee_per_gas' (type-2+)"
    )
    assert expected_message in output

    error_line = next(
        line for line in output.splitlines() if expected_message in line
    )
    print(error_line)
