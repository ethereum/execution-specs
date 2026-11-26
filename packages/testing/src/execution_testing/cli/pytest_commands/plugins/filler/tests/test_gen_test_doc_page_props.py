"""Tests for the page properties of the test case reference."""

from pathlib import Path

import pytest

from ..gen_test_doc.page_props import MarkdownPageProps


@pytest.mark.parametrize(
    "source,target",
    [
        ("tests/reorg/README.md", "tests/reorg/readme.md"),
        ("tests/reorg/notes.md", "tests/reorg/notes.md"),
    ],
)
def test_markdown_page_target(source: str, target: str) -> None:
    """
    A `README.md` is written as `readme.md`, which the site builder does
    not take for the directory's index page; other files keep their name.
    """
    page = MarkdownPageProps(
        title="README",
        source_code_url="",
        target_or_valid_fork="",
        path=Path(source),
        pytest_node_id=source,
        package_name="",
    )
    assert page.target_output_file == Path(target)
