"""Test opcode metadata isolation during fixture generation."""

import json
import textwrap

import pytest


def test_opcode_metadata_excludes_probe(pytester: pytest.Pytester) -> None:
    """Exclude discarded probe executions from fixture opcode metadata."""
    test_dir = pytester.mkdir("tests") / "amsterdam"
    test_dir.mkdir()
    test_module = test_dir / "test_opcode_count_probe.py"
    test_module.write_text(
        textwrap.dedent(
            """\
            from copy import deepcopy

            import pytest
            from execution_testing import (
                Alloc,
                Block,
                BlockchainTest,
                BlockchainTestFiller,
                Fork,
            )
            from execution_testing.client_clis import TransitionTool
            from execution_testing.fixtures import BlockchainFixture

            @pytest.mark.valid_at("Amsterdam")
            @pytest.mark.parametrize("with_probe", [False, True])
            def test_opcode_count_probe(
                pre: Alloc,
                blockchain_test: BlockchainTestFiller,
                fork: Fork,
                t8n: TransitionTool,
                with_probe: bool,
            ) -> None:
                if with_probe:
                    BlockchainTest(
                        fork=fork,
                        pre=deepcopy(pre),
                        blocks=[Block(txs=[])],
                        post={},
                    ).generate(t8n=t8n, fixture_format=BlockchainFixture)

                blockchain_test(pre=pre, blocks=[Block(txs=[])], post={})
            """
        )
    )
    pytester.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands/pytest_ini_files/"
            "pytest-fill.ini"
        )
    )
    output_dir = pytester.path / "fixtures"

    # Isolate Pydantic's cached wrappers between nested fill sessions.
    result = pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Amsterdam",
        "-m",
        "blockchain_test",
        "--no-html",
        "--output",
        str(output_dir),
        str(test_module.relative_to(pytester.path)),
    )
    result.assert_outcomes(passed=2)

    fixture_files = list((output_dir / "blockchain_tests").rglob("*.json"))
    assert len(fixture_files) == 1
    fixtures = list(json.loads(fixture_files[0].read_text()).values())
    assert len(fixtures) == 2
    for fixture in fixtures:
        metadata = fixture["_info"]["metadata"]
        assert len(fixture["blocks"]) == 1
        assert len(metadata["opcode_count_per_block"]) == 1
        assert metadata["opcode_count"]
        assert (
            metadata["opcode_count"] == metadata["opcode_count_per_block"][0]
        )

    first_metadata, second_metadata = [
        fixture["_info"]["metadata"] for fixture in fixtures
    ]
    assert first_metadata["opcode_count"] == second_metadata["opcode_count"]
    assert (
        first_metadata["opcode_count_per_block"]
        == second_metadata["opcode_count_per_block"]
    )
