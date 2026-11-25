"""Tests for the page properties of the test case reference."""

import io
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any, Dict, Iterator

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..gen_test_doc.page_props import FunctionPageProps, MarkdownPageProps

TEMPLATES = next(
    parent / "docs" / "templates"
    for parent in Path(__file__).resolve().parents
    if (parent / "docs" / "templates").is_dir()
)


class MemoryWriter:
    """Keep written pages in memory, by path."""

    def __init__(self) -> None:
        """Start without pages."""
        self.pages: Dict[Path, str] = {}

    @contextmanager
    def open(self, path: Path, mode: str) -> Iterator[IO[Any]]:
        """Collect what is written to `path`."""
        del mode
        buffer = io.StringIO()
        yield buffer
        self.pages[path] = buffer.getvalue()


def test_function_page_has_a_plain_title() -> None:
    """
    A test function's page states its title in the front matter. Its
    navigation entry is wrapped in `<code>`, which would otherwise end up
    in the page's social card and `og:title`.

    The social card gets the name with a space after each underscore, as
    it only wraps a title at spaces.
    """
    page = FunctionPageProps(
        title="test_example",
        source_code_url="https://example.org/test_module.py#L1",
        target_or_valid_fork="Prague",
        path=Path("tests/prague/test_module.py"),
        pytest_node_id="tests/prague/test_module.py::test_example",
        package_name="tests.prague.test_module.test_example",
        test_case_count=1,
    )
    assert page.nav_entry("Test Case Reference")[-1] == (
        "<code>test_example</code>"
    )
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        trim_blocks=True,
        undefined=StrictUndefined,
    )
    env.globals.update(short_git_ref="abc1234")
    writer = MemoryWriter()
    page.write_page(writer, env)

    written = writer.pages[page.target_output_file]
    front_matter = written.split("---")[1]
    lines = front_matter.splitlines()
    assert 'title: "test_example"' in lines
    assert '    title: "test_ example"' in lines


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
