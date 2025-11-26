"""
Script called during mkdocs build|serve to create the "Test Case Reference".

Called via the mkdocs-gen-files plugin; it's specified in mkdocs.yaml and
can't take command-line arguments. The main logic is implemented in
src/pytest_plugins/filler/gen_test_doc.py.
"""

import importlib
import logging
import sys
from os import getenv

import pytest
from click.testing import CliRunner
from execution_testing.cli.pytest_commands.fill import fill
from execution_testing.cli.pytest_commands.plugins.filler.gen_test_doc import (
    gen_test_doc,
)
from execution_testing.config import DocsConfig

importlib.reload(
    gen_test_doc
)  # get changes in plugin to trigger an update for `mkdocs serve`

TARGET_FORK = DocsConfig().TARGET_FORK
GENERATE_UNTIL_FORK = DocsConfig().GENERATE_UNTIL_FORK

logger = logging.getLogger("mkdocs")


# If docs are generated while FAST_DOCS is true, then use "tests/frontier"
# otherwise use "tests"
#
# USAGE 1 (use fast mode):
#       export FAST_DOCS=true && uv run mkdocs serve
# USAGE 2 (use fast mode + hide side-effect warnings):
#       export FAST_DOCS=true && uv run mkdocs serve 2>&1 | sed '/is not found among documentation files/d' #noqa: E501
test_arg = "tests"
fast_mode = getenv("FAST_DOCS")
if fast_mode is not None:
    if fast_mode.lower() == "true":
        print(
            "-" * 40, "\nWill generate docs using FAST_DOCS mode.\n" + "-" * 40
        )
        test_arg = "tests/frontier"

args = [
    "--override-ini",
    # suppress warnings due to reload ⬇️
    "filterwarnings=ignore::pytest.PytestAssertRewriteWarning",
    "-p",
    "execution_testing.cli.pytest_commands.plugins.filler.gen_test_doc.gen_test_doc",
    "-p",
    "execution_testing.cli.pytest_commands.plugins.filler.eip_checklist",
    "--gen-docs",
    f"--gen-docs-target-fork={TARGET_FORK}",
    f"--until={GENERATE_UNTIL_FORK}",
    "--checklist-doc-gen",
    "--skip-index",
    "-m",
    "not blockchain_test_engine and not benchmark",
    "-s",
    test_arg,
]

runner = CliRunner()
logger.info(
    f"Generating documentation for test cases until {GENERATE_UNTIL_FORK} as "
    f"fill {' '.join(args)}"
)
result = runner.invoke(fill, args)
for line in result.output.split("\n"):
    if "===" in line:
        logger.info(line.replace("===", "=="))
        continue
    logger.info(line)
if result.exit_code in [
    pytest.ExitCode.OK,
    pytest.ExitCode.NO_TESTS_COLLECTED,
]:
    logger.info("Documentation generation successful.")
    sys.exit(0)
logger.error(
    f"Documentation generation failed (exit: "
    f"{pytest.ExitCode(result.exit_code)}, "
    f"{pytest.ExitCode(result.exit_code).name})."
)
sys.exit(result.exit_code)
