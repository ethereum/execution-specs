"""
Test that a `pre` a test builds itself must opt into the genesis accounts.

The `pre` fixture starts out holding the accounts the fork allocates at
genesis. An allocation built outside it gets them only through
`with_genesis_accounts()`, and fails the fill without it, so a genesis never
silently lacks the system contracts.
"""

import json
import textwrap

import pytest

FORK = "Prague"

BEACON_ROOTS_ADDRESS = "0x000f3df6d732807ef1319fb7b8bb8522d0beac02"

TEST_MODULE_DIR = "tests/prague/dummy_test_module"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Account, Alloc, Block, BlockchainTestFiller

    @pytest.mark.valid_at("{fork}")
    def test_case(blockchain_test: BlockchainTestFiller) -> None:
        blockchain_test(pre={pre}, blocks=[Block()], post={{}})
    """
)


def fill(pytester: pytest.Pytester, pre: str) -> pytest.RunResult:
    """Fill a test that passes `pre` to `blockchain_test`."""
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(MODULE_TEMPLATE.format(fork=FORK, pre=pre))
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "-m",
        "blockchain_test",
        "--no-html",
        "--output",
        "fixtures",
        str(module.relative_to(pytester.path)),
    )


def test_pre_without_genesis_accounts_fails(pytester: pytest.Pytester) -> None:
    """A `pre` that never opted into the genesis accounts fails the fill."""
    result = fill(pytester, pre="{0x1000: Account(balance=1)}")

    result.assert_outcomes(failed=1)
    output = "\n".join(result.outlines + result.errlines)
    assert "lacks the accounts" in output, output


def test_pre_with_genesis_accounts_fills(pytester: pytest.Pytester) -> None:
    """The genesis holds both the test's accounts and the fork's."""
    result = fill(
        pytester,
        pre="Alloc({0x1000: Account(balance=1)}).with_genesis_accounts()",
    )

    result.assert_outcomes(passed=1)
    (fixture_file,) = (pytester.path / "fixtures" / "blockchain_tests").rglob(
        "*.json"
    )
    (fixture,) = json.loads(fixture_file.read_text()).values()
    assert BEACON_ROOTS_ADDRESS in fixture["pre"]
    assert 0x1000 in [int(address, 16) for address in fixture["pre"]]
