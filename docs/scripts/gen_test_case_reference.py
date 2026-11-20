"""
Generate the "Test Case Reference" pages of the documentation site.

Called by `docs/scripts/gen_docs.py` before `zensical build`. The main logic
is implemented in the `gen_test_doc` pytest plugin:
packages/testing/src/execution_testing/cli/pytest_commands/plugins/filler/gen_test_doc/gen_test_doc.py
"""

import logging
from pathlib import Path
from typing import List

import pytest
from click.testing import CliRunner
from execution_testing.cli.pytest_commands.fill import fill
from execution_testing.config import DocsConfig

logger = logging.getLogger("gen_docs")


def generate_test_case_reference(
    docs_dir: Path, test_paths: List[str], include_benchmark: bool
) -> int:
    """
    Run `fill` with the doc generation plugins over `test_paths`.

    Pages are written below `docs_dir / "tests"`. Returns the pytest exit
    code (0 on success).
    """
    target_fork = DocsConfig().TARGET_FORK
    generate_until_fork = DocsConfig().GENERATE_UNTIL_FORK
    args = [
        "--override-ini",
        "filterwarnings=ignore::pytest.PytestAssertRewriteWarning",
        "-p",
        "execution_testing.cli.pytest_commands.plugins.filler.gen_test_doc.gen_test_doc",
        "-p",
        "execution_testing.cli.pytest_commands.plugins.filler.eip_checklist",
        # No tests run; skip the plugin's `gc.collect()` calls at exit,
        # which take ~10s with the ~95k collected items in memory.
        "-p",
        "no:unraisableexception",
        "--gen-docs",
        f"--gen-docs-target-fork={target_fork}",
        f"--gen-docs-output-dir={docs_dir}",
        f"--until={generate_until_fork}",
        "--checklist-doc-gen",
        "--skip-index",
        "--ignore=tests/ported_static",
        "-m",
        "not blockchain_test_engine",
        "-s",
    ]
    if include_benchmark:
        args.append("--include-benchmark")
    args.extend(test_paths)

    logger.info(
        f"Generating documentation for test cases until "
        f"{generate_until_fork} as fill {' '.join(args)}"
    )
    result = CliRunner().invoke(fill, args)
    for line in result.output.split("\n"):
        logger.info(line.replace("===", "=="))
    if result.exception is not None and not isinstance(
        result.exception, SystemExit
    ):
        logger.error(f"fill raised: {result.exception!r}")
        return 1
    if result.exit_code in [
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    ]:
        logger.info("Test case reference generation successful.")
        return 0
    logger.error(
        f"Test case reference generation failed (exit: "
        f"{pytest.ExitCode(result.exit_code)}, "
        f"{pytest.ExitCode(result.exit_code).name})."
    )
    return result.exit_code
