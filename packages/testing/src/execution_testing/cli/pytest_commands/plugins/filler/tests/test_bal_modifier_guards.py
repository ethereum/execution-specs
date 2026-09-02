"""
Test the fill-time checks on block access list modifiers that can only run
once the transition tool has produced the list.

`override_rlp` commits the header to re-encoded bytes that only the engine
payload can carry. `fill` therefore refuses the RLP blockchain fixture
format for such a block, and refuses an explicit payload override that would
replace the committed bytes. The same block fills as an engine fixture.
"""

import textwrap

import pytest

FORK = "Amsterdam"

TEST_MODULE_DIR = "tests/amsterdam/dummy_test_module"

ENGINE_ONLY_MARKER = "@pytest.mark.blockchain_test_engine_only"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Block,
        BlockAccessList,
        BlockAccessListExpectation,
        BlockchainTestFiller,
        BlockException,
        Bytes,
        Transaction,
    )
    from execution_testing.test_types.block_access_list.modifiers import (
        override_rlp,
    )

    EMPTY_LIST = Bytes(b"\\xc0")

    {markers}
    @pytest.mark.valid_at("{fork}")
    @pytest.mark.exception_test
    def test_case(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
        tx = Transaction(to=pre.fund_eoa(amount=0), sender=pre.fund_eoa())
        blockchain_test(
            pre=pre,
            post={{}},
            blocks=[
                Block(
                    txs=[tx],
                    exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                    expected_block_access_list=(
                        BlockAccessListExpectation(){modifier}
                    ),
                    {block_kwargs}
                )
            ],
        )
    """
)

OVERRIDE_RLP = ".modify(override_rlp(lambda _: EMPTY_LIST))"


def write_test_module(
    pytester: pytest.Pytester,
    *,
    modifier: str,
    markers: str = ENGINE_ONLY_MARKER,
    block_kwargs: str = "",
) -> str:
    """
    Write a single-test module with the given BAL modifier chain and return
    its path relative to the pytester directory.
    """
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(
        MODULE_TEMPLATE.format(
            markers=markers,
            fork=FORK,
            modifier=modifier,
            block_kwargs=block_kwargs,
        )
    )
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return str(module.relative_to(pytester.path))


def run_fill(
    pytester: pytest.Pytester, module_path: str, fixture_format: str
) -> pytest.RunResult:
    """Fill the given module, generating only ``fixture_format``."""
    return pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "-m",
        fixture_format,
        "--no-html",
        "--output",
        "fixtures",
        module_path,
    )


def output_of(result: pytest.RunResult) -> str:
    """Return the combined output of a fill run."""
    return "\n".join(result.outlines + result.errlines)


def test_engine_format_fills_override_rlp(pytester: pytest.Pytester) -> None:
    """Positive control: the engine payload can carry the re-encoding."""
    module_path = write_test_module(pytester, modifier=OVERRIDE_RLP)

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=1, failed=0)


def test_rlp_format_refuses_override_rlp(pytester: pytest.Pytester) -> None:
    """Block RLP never carries the list, so the fixture cannot deliver it."""
    module_path = write_test_module(
        pytester, modifier=OVERRIDE_RLP, markers=""
    )

    result = run_fill(pytester, module_path, "blockchain_test")

    result.assert_outcomes(passed=0, failed=1)
    output = output_of(result)
    assert "cannot deliver the re-encoded bytes" in output, output
    assert "Mark the test `blockchain_test_engine_only`" in output, output


def test_explicit_payload_bal_with_override_rlp_is_refused(
    pytester: pytest.Pytester,
) -> None:
    """The explicit payload bytes would replace the committed ones."""
    module_path = write_test_module(
        pytester,
        modifier=OVERRIDE_RLP,
        block_kwargs=('engine_new_payload_block_access_list=Bytes(b"\\x80"),'),
    )

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=0, failed=1)
    output = output_of(result)
    assert "would replace the bytes the header commits to" in output, output
    assert "Keep one" in output, output
