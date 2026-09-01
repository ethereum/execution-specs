"""
Test the static check that the `inclusion_test` marker applies to a
`BlockchainTest`.

An inclusion test asserts whether one specific transaction can be included in
a block, and by convention that transaction is the last one of the last block.
Any other invalid transaction in the chain would leave the subject of the test
ambiguous, so `BlockchainTest` rejects such a layout on instantiation, before
any block is filled.

Tests without the marker are unaffected: an invalid transaction may sit at the
end of any block.
"""

import textwrap

import pytest

# Pinned so the fill runs against a single, stable fork: the invalid
# transaction is derived from the fork's intrinsic gas cost, which later forks
# reprice.
FORK = "Prague"

TEST_MODULE_DIR = "tests/prague/dummy_test_module"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Block,
        BlockchainTestFiller,
        Fork,
        Transaction,
        TransactionException,
    )

    INVALID = TransactionException.INTRINSIC_GAS_TOO_LOW

    {markers}
    @pytest.mark.valid_at("{fork}")
    def test_case(
        blockchain_test: BlockchainTestFiller, pre: Alloc, fork: Fork
    ) -> None:
        intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

        def valid_tx() -> Transaction:
            return Transaction(to=0, sender=pre.fund_eoa(),
                               gas_limit=intrinsic_gas)

        def invalid_tx() -> Transaction:
            return Transaction(to=0, sender=pre.fund_eoa(),
                               gas_limit=intrinsic_gas - 1, error=INVALID)

        blockchain_test(pre=pre, post={{}}, blocks={blocks})
    """
)

INCLUSION_TEST_MARKERS = (
    "@pytest.mark.inclusion_test\n@pytest.mark.exception_test"
)
EXCEPTION_TEST_MARKER = "@pytest.mark.exception_test"

# Invalid transaction in a block other than the last one.
INVALID_TX_IN_EARLIER_BLOCK = (
    "[Block(txs=[invalid_tx()], exception=INVALID), Block(txs=[valid_tx()])]"
)
# Invalid transaction in the last block, but not as its last transaction.
INVALID_TX_BEFORE_LAST_IN_LAST_BLOCK = (
    "[Block(txs=[valid_tx()]), "
    "Block(txs=[invalid_tx(), valid_tx()], exception=INVALID)]"
)
# The only layout an inclusion test is allowed to use.
INVALID_TX_LAST_IN_LAST_BLOCK = (
    "[Block(txs=[valid_tx()]), "
    "Block(txs=[valid_tx(), invalid_tx()], exception=INVALID)]"
)


def write_test_module(
    pytester: pytest.Pytester, markers: str, blocks: str
) -> str:
    """
    Write a single-test module using the given markers and block layout, and
    return its path relative to the pytester directory.
    """
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(
        MODULE_TEMPLATE.format(markers=markers, fork=FORK, blocks=blocks)
    )
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return str(module.relative_to(pytester.path))


def run_fill(pytester: pytest.Pytester, module_path: str) -> pytest.RunResult:
    """
    Fill the given module, generating only the blockchain test fixture format.
    """
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
        module_path,
    )


@pytest.mark.parametrize(
    "blocks,expected_block_number",
    [
        pytest.param(
            INVALID_TX_IN_EARLIER_BLOCK, 0, id="invalid_tx_in_earlier_block"
        ),
        pytest.param(
            INVALID_TX_BEFORE_LAST_IN_LAST_BLOCK,
            1,
            id="invalid_tx_before_last_in_last_block",
        ),
    ],
)
def test_misplaced_invalid_tx_is_rejected(
    pytester: pytest.Pytester,
    blocks: str,
    expected_block_number: int,
) -> None:
    """
    Fill an inclusion test whose invalid transaction is not the last one of the
    last block, and assert it fails pointing at the offending block.
    """
    module_path = write_test_module(pytester, INCLUSION_TEST_MARKERS, blocks)

    result = run_fill(pytester, module_path)

    result.assert_outcomes(passed=0, failed=1)
    output = "\n".join(result.outlines + result.errlines)
    assert "in an inclusion test the only transaction allowed" in output, (
        f"Inclusion test check did not report the failure:\n{output}"
    )
    assert f"but block {expected_block_number} contains" in output, (
        f"Expected block {expected_block_number} to be reported:\n{output}"
    )


@pytest.mark.parametrize(
    "markers,blocks",
    [
        pytest.param(
            INCLUSION_TEST_MARKERS,
            INVALID_TX_LAST_IN_LAST_BLOCK,
            id="inclusion_test_with_invalid_tx_last_in_last_block",
        ),
        pytest.param(
            EXCEPTION_TEST_MARKER,
            INVALID_TX_IN_EARLIER_BLOCK,
            id="unmarked_test_with_invalid_tx_in_earlier_block",
        ),
    ],
)
def test_allowed_invalid_tx_placement_fills(
    pytester: pytest.Pytester,
    markers: str,
    blocks: str,
) -> None:
    """
    Fill a test whose invalid transaction placement is allowed and assert the
    check does not reject it.

    The first case is the layout an inclusion test is meant to have; the second
    is the same layout the check rejects, minus the marker that enables it.
    """
    module_path = write_test_module(pytester, markers, blocks)

    result = run_fill(pytester, module_path)

    result.assert_outcomes(passed=1, failed=0)
