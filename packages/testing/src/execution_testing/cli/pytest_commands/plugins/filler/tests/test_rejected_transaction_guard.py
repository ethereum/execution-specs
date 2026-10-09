"""
Test that `fill` refuses a block whose transaction is rejected while the
transition tool also rejects the block itself.

The block exception is not verified when a transaction is rejected, so the
fixture would otherwise carry two defects and name only one.
"""

import textwrap

import pytest

FORK = "Amsterdam"

TEST_MODULE_DIR = "tests/amsterdam/dummy_test_module"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Block,
        BlockchainTestFiller,
        Environment,
        Transaction,
        TransactionException,
    )

    @pytest.mark.valid_at("{fork}")
    @pytest.mark.exception_test
    def test_case(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
        tx = Transaction(
            to=pre.fund_eoa(),
            sender=pre.fund_eoa(),
            gas_limit={block_gas_limit} + 1,
            error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
        )
        blockchain_test(
            pre=pre,
            post={{}},
            genesis_environment=Environment(gas_limit={block_gas_limit}),
            blocks=[
                Block(
                    txs=[tx],
                    exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
                )
            ],
        )
    """
)


def fill(pytester: pytest.Pytester, block_gas_limit: int) -> pytest.RunResult:
    """Fill a block whose only transaction exceeds the block gas limit."""
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(
        MODULE_TEMPLATE.format(fork=FORK, block_gas_limit=block_gas_limit)
    )
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


def test_block_over_access_list_cap_is_refused(
    pytester: pytest.Pytester,
) -> None:
    """
    At this gas limit the system-contract reads every Amsterdam block makes
    already exceed the EIP-7928 item cap.
    """
    result = fill(pytester, block_gas_limit=21_000)

    result.assert_outcomes(passed=0, failed=1)
    output = "\n".join(result.outlines + result.errlines)
    assert "also rejects the block itself" in output, output
    assert "BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED" in output, output


def test_block_within_access_list_cap_fills(pytester: pytest.Pytester) -> None:
    """Positive control: only the transaction is invalid."""
    result = fill(pytester, block_gas_limit=100_000)

    result.assert_outcomes(passed=1, failed=0)
