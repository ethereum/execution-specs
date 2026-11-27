"""
Test the `with_all_operands` marker and the `operands` fixture.

A marked test runs once with each `Operands` source, its `push` or
`calldata` id segment last. Requesting the fixture without the marker, or
marking a test that does not request it, fails with a message pointing at
the fix, while `Operands.push()` and `Operands.calldata()` build a single
source without the marker.
"""

import textwrap

import pytest

FORK = "Cancun"

TEST_MODULE_DIR = "tests/cancun/dummy_test_module"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Op,
        Operands,
        StateTestFiller,
        Transaction,
    )

    {markers}
    @pytest.mark.valid_at("{fork}")
    def test_case(state_test: StateTestFiller, pre: Alloc{arguments}) -> None:
        {build_operands}
        contract = pre.deploy_contract(
            Op.SSTORE(0, Op.ADD(operands(2), operands(3)))
        )
        tx = Transaction(
            sender=pre.fund_eoa(), to=contract, data=operands.data
        )
        state_test(
            pre=pre, post={{contract: Account(storage={{0: 5}})}}, tx=tx
        )
    """
)


def write_test_module(
    pytester: pytest.Pytester,
    *,
    markers: str,
    arguments: str,
    build_operands: str,
) -> str:
    """
    Write a single-test module and return its path relative to the
    pytester directory.
    """
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(
        MODULE_TEMPLATE.format(
            markers=markers,
            fork=FORK,
            arguments=arguments,
            build_operands=build_operands,
        )
    )
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return str(module.relative_to(pytester.path))


def run_fill(
    pytester: pytest.Pytester, module_path: str, *args: str
) -> pytest.RunResult:
    """Fill the given module, generating only the state test format."""
    return pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "-m",
        "state_test",
        "--no-html",
        "--output",
        "fixtures",
        *args,
        module_path,
    )


def test_marker_runs_each_source(pytester: pytest.Pytester) -> None:
    """Fill a marked test and assert it runs once per source."""
    module_path = write_test_module(
        pytester,
        markers="@pytest.mark.with_all_operands",
        arguments=", operands: Operands",
        build_operands="",
    )

    result = run_fill(pytester, module_path, "-v")

    result.assert_outcomes(passed=2, failed=0)
    result.stdout.fnmatch_lines(
        [
            "*test_case?fork_Cancun-state_test-calldata?*",
            "*test_case?fork_Cancun-state_test-push?*",
        ],
        consecutive=False,
    )
    # Only the calldata case sends the operands, as two words.
    fixture = next(pytester.path.joinpath("fixtures").rglob("case.json"))
    assert fixture.read_text().count(f"0x{2:064x}{3:064x}") == 1


@pytest.mark.parametrize("source", ["push", "calldata"])
def test_class_method_builds_one_source(
    pytester: pytest.Pytester, source: str
) -> None:
    """Fill an unmarked test that builds its own `Operands` instance."""
    module_path = write_test_module(
        pytester,
        markers="",
        arguments="",
        build_operands=f"operands = Operands.{source}()",
    )

    result = run_fill(pytester, module_path)

    result.assert_outcomes(passed=1, failed=0)


def test_fixture_without_marker_fails(pytester: pytest.Pytester) -> None:
    """Fill an unmarked test that requests the fixture and assert it fails."""
    module_path = write_test_module(
        pytester,
        markers="",
        arguments=", operands: Operands",
        build_operands="",
    )

    result = run_fill(pytester, module_path)

    result.assert_outcomes(passed=0, errors=1)
    result.stdout.fnmatch_lines(["*without the `with_all_operands` marker*"])


def test_marker_without_fixture_fails(pytester: pytest.Pytester) -> None:
    """Collect a marked test that never requests the fixture."""
    module_path = write_test_module(
        pytester,
        markers="@pytest.mark.with_all_operands",
        arguments="",
        build_operands="operands = Operands.push()",
    )

    result = run_fill(pytester, module_path)

    assert result.ret != 0
    result.stdout.fnmatch_lines(["*does not request the `operands` fixture*"])
