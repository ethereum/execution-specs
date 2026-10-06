"""
Test that `fill` fails a test that calls a spec fixture more than once.

Every call writes its fixture under the same test ID, so without the check
only the last call's fixture would be written and the others silently lost.
"""

import textwrap

import pytest

FORK = "Osaka"

TEST_MODULE_DIR = "tests/osaka/dummy_test_module"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Op,
        StateTestFiller,
        Transaction,
    )

    @pytest.mark.valid_at("{fork}")
    def test_case(state_test: StateTestFiller, pre: Alloc) -> None:
        for value in range({calls}):
            contract = pre.deploy_contract(Op.SSTORE(0, value + 1))
            state_test(
                pre=pre,
                post={{contract: Account(storage={{0: value + 1}})}},
                tx=Transaction(
                    sender=pre.fund_eoa(),
                    to=contract,
                    gas_limit=100_000,
                ),
            )
    """
)


def fill(pytester: pytest.Pytester, calls: int) -> pytest.RunResult:
    """Fill a test that calls `state_test` `calls` times."""
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(MODULE_TEMPLATE.format(fork=FORK, calls=calls))
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
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
        str(module.relative_to(pytester.path)),
    )


def test_spec_called_twice_fails(pytester: pytest.Pytester) -> None:
    """A second `state_test` call in the same test fails the test."""
    result = fill(pytester, calls=2)

    result.assert_outcomes(passed=0, failed=1)
    output = "\n".join(result.outlines + result.errlines)
    assert "`state_test` can only be called once per test" in output, output


def test_spec_called_once_fills(pytester: pytest.Pytester) -> None:
    """Positive control: a single call fills as usual."""
    result = fill(pytester, calls=1)

    result.assert_outcomes(passed=1, failed=0)
