"""Include EEST's CONTRIBUTING.md and SECURITY.md in the HTML documentation."""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger("gen_docs")


def copy_markdown_file(
    source_path: str,
    destination_path: str,
    docs_dir: Path,
    fix_links: bool = True,
) -> None:
    """
    Copy a markdown file to `docs_dir / destination_path`, fixing links if
    requested.
    """
    source_file = Path(source_path)
    destination_file = docs_dir / destination_path
    destination_file.parent.mkdir(parents=True, exist_ok=True)

    if not source_file.is_file():
        raise FileNotFoundError(
            f"Error: Source file '{source_file}' not found at '{os.getcwd()}'."
        )

    try:
        with open(destination_file, "w") as destination:
            with open(source_file, "r") as f:
                for line in f.readlines():
                    if fix_links:
                        # Fix absolute website links to relative docs links
                        line = re.sub(
                            r"https://eest\.ethereum\.org/main/([^)\s]+)",
                            r"../\1.md",
                            line,
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

                        # Fix repo-relative docs/ links to work from
                        # docs/getting_started/<file>.md
                        line = re.sub(
                            r"\]\(docs/getting_started/",
                            r"](",
                            line,
                        )
                        line = re.sub(
                            r"\]\(docs/([^)]+)\)",
                            r"](../\1)",
                            line,
                        )

                    destination.write(line)
    except Exception as e:
        raise Exception(
            f"Error copying file {source_file} to {destination_file}"
        ) from e

    logger.info(f"Copied {source_file} to {destination_file}.")


def copy_repo_docs(docs_dir: Path) -> None:
    """Copy CONTRIBUTING.md and SECURITY.md to docs/getting_started/."""
    copy_markdown_file(
        "CONTRIBUTING.md", "getting_started/contributing.md", docs_dir
    )
    copy_markdown_file("SECURITY.md", "getting_started/security.md", docs_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    copy_repo_docs(Path("docs"))
