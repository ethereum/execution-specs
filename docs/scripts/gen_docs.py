"""
Generate the documentation pages that are not tracked in git.

Run before `zensical build` / `zensical serve` (the `just docs*` recipes do
this). It replaces the `mkdocs-gen-files` plugin, which Zensical does not
support, by writing real Markdown files into `docs/` (all gitignored):

- `getting_started/contributing.md`, `getting_started/security.md`: copies of
  the repository's CONTRIBUTING.md and SECURITY.md.
- `filling_tests/filling_tests_command_line_options.md`: `fill --help`.
- `tests/**`: the "Test Case Reference", including `tests/navigation.md`,
  a nested literate-nav file linked from `docs/navigation.md`.

Usage:

    uv run python docs/scripts/gen_docs.py [--fast]

`--fast` (or `FAST_DOCS=true`) only generates the test case reference for
`tests/frontier` plus the test modules linked from the hand-written docs, so
that the strict build's link validation still passes.

Any warning or error logged during generation (e.g. by the `gen_test_doc`
plugin) makes the script exit non-zero, mirroring the old
`mkdocs build --strict` behavior.
"""

import argparse
import logging
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import List

from copy_repo_docs import copy_repo_docs
from gen_test_case_reference import generate_test_case_reference
from generate_fill_help import generate_command_line_options_docs

logger = logging.getLogger("gen_docs")

DOCS_DIR = Path("docs")
TESTS_DIR = Path("tests")
FAST_TEST_PATHS = ["tests/frontier"]

# Links from hand-written pages into the generated test case reference, e.g.
# `../tests/shanghai/eip3860_initcode/test_initcode/test_contract_creating_tx.md`  # noqa: E501
TEST_REFERENCE_LINK = re.compile(r"\]\((?:\.\./)*(tests/[^)#\s]+)")


class WarningCounter(logging.Handler):
    """Count records at WARNING level or above."""

    def __init__(self) -> None:
        """Initialize the counter."""
        super().__init__(level=logging.WARNING)
        self.count = 0

    def emit(self, record: logging.LogRecord) -> None:
        """Count the record."""
        del record
        self.count += 1


def linked_test_modules(docs_dir: Path) -> List[str]:
    """
    Return the test modules whose generated pages are linked from tracked
    docs pages, so that a fast build still resolves those links.
    """
    modules = set()
    for md_file in docs_dir.rglob("*.md"):
        if md_file.is_relative_to(docs_dir / TESTS_DIR):
            continue
        for link in TEST_REFERENCE_LINK.findall(md_file.read_text()):
            parts = Path(link).parts
            for i, part in enumerate(parts):
                if part.startswith("test_"):
                    module = Path(*parts[:i], part).with_suffix(".py")
                    if module.is_file():
                        modules.add(module.as_posix())
                    break
    return sorted(modules)


def main() -> int:
    """Generate all pages; return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--fast",
        action="store_true",
        default=(os.getenv("FAST_DOCS") or "").lower() == "true",
        help="Only generate a subset of the test case reference.",
    )
    parser.add_argument(
        "--skip-test-reference",
        action="store_true",
        help="Do not (re)generate the test case reference.",
    )
    args = parser.parse_args()

    # `fill` (run in-process via click's CliRunner) swaps sys.stdout/stderr
    # and reconfigures the root logger, so bind our own handler to the real
    # stderr and don't propagate.
    stream_handler = logging.StreamHandler(sys.__stderr__)
    stream_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    counter = WarningCounter()
    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    logger.addHandler(counter)
    logger.propagate = False

    start = time.perf_counter()
    copy_repo_docs(DOCS_DIR)
    generate_command_line_options_docs(DOCS_DIR)

    exit_code = 0
    if not args.skip_test_reference:
        shutil.rmtree(DOCS_DIR / TESTS_DIR, ignore_errors=True)
        if args.fast:
            test_paths = FAST_TEST_PATHS + linked_test_modules(DOCS_DIR)
            logger.info("Generating the test case reference in fast mode.")
        else:
            test_paths = [str(TESTS_DIR)]
        t0 = time.perf_counter()
        exit_code = generate_test_case_reference(
            DOCS_DIR, test_paths, include_benchmark=not args.fast
        )
        logger.info(
            f"Test case reference generated in "
            f"{time.perf_counter() - t0:.1f}s."
        )

    logger.info(f"Docs generation took {time.perf_counter() - start:.1f}s.")
    if exit_code != 0:
        return exit_code
    if counter.count:
        logger.error(
            f"Docs generation emitted {counter.count} warning(s); failing."
        )
        return 1
    return 0


if __name__ == "__main__":
    code = main()
    # Skip interpreter teardown: freeing the objects of ~95k collected test
    # items takes several seconds and nothing needs to be cleaned up.
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
