"""Include EEST's CONTRIBUTING.md and SECURITY.md in the HTML documentation."""

import logging
import re
from pathlib import Path

import mkdocs_gen_files

logger = logging.getLogger("mkdocs")


def copy_markdown_file(source_path, destination_path, fix_links=True):
    """Copy a markdown file to the destination, fixing links if requested."""
    source_file = Path(source_path)
    destination_file = Path(destination_path)

    if not source_file.is_file():
        raise FileNotFoundError(
            f"Error: Source file '{source_file}' not found in current directory."
        )

    try:
        with mkdocs_gen_files.open(destination_file, "w") as destination:
            with open(source_file, "r") as f:
                for line in f.readlines():
                    if fix_links:
                        # Fix absolute website links to relative docs links
                        line = re.sub(
                            r"https://eest\.ethereum\.org/main/([^)\s]+)", r"../\1.md", line
                        )

                        # Fix SECURITY.md link
                        line = re.sub(
                            r"\[Security Policy\]\(SECURITY\.md\)",
                            r"[Security Policy](security.md)",
                            line,
                        )

                        # Fix EIP checklist template link
                        line = re.sub(
                            r"\[EIP checklist template\]\(./docs/writing_tests/checklist_templates/eip_testing_checklist_template.md\)",  # noqa: E501
                            r"[EIP checklist template](../writing_tests/checklist_templates/eip_testing_checklist_template.md)",  # noqa: E501
                            line,
                        )

                    destination.write(line)
    except Exception as e:
        raise Exception(f"Error copying file {source_file} to {destination_file}") from e

    logger.info(f"Copied {source_file} to {destination_file}.")


def include_contributing_in_docs():
    """Copy CONTRIBUTING.md to ./docs/ to include in HTML docs."""
    copy_markdown_file("CONTRIBUTING.md", "getting_started/contributing.md")


def include_security_in_docs():
    """Copy SECURITY.md to ./docs/getting_started/ to include in HTML docs."""
    copy_markdown_file("SECURITY.md", "getting_started/security.md")


include_contributing_in_docs()
include_security_in_docs()
