"""
Test that `fill` refuses a block whose transaction is rejected when the block
has a second defect: the transition tool rejects the block itself, or the
accounts the rejected transaction touches take the BAL over its item cap.

The block exception is not verified when a transaction is rejected, so the
fixture would otherwise carry two defects and name only one.
"""

import textwrap

import pytest

from execution_testing.forks import Amsterdam

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


def test_rejected_tx_accounts_over_access_list_cap_are_refused(
    pytester: pytest.Pytester,
) -> None:
    """
    The transition tool's BAL fits the cap, but adding the rejected
    transaction's sender and recipient takes it one item over.
    """
    item_gas = Amsterdam.gas_costs().BLOCK_ACCESS_LIST_ITEM
    max_items = Amsterdam.empty_block_bal_item_count() + 1
    result = fill(pytester, block_gas_limit=max_items * item_gas)

    result.assert_outcomes(passed=0, failed=1)
    output = "\n".join(result.outlines + result.errlines)
    assert "listing the accounts it touches" in output, output


def test_rejected_tx_accounts_within_access_list_cap_fill(
    pytester: pytest.Pytester,
) -> None:
    """Positive control: the cap has room for the sender and recipient."""
    item_gas = Amsterdam.gas_costs().BLOCK_ACCESS_LIST_ITEM
    max_items = Amsterdam.empty_block_bal_item_count() + 2
    result = fill(pytester, block_gas_limit=max_items * item_gas)

    result.assert_outcomes(passed=1, failed=0)
