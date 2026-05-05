"""Regression tests for diff listing labels in docc-generated pages."""

from pathlib import PurePath

from docc.context import Context
from docc.plugins import html
from docc.plugins.listing import Listing, ListingNode, render_html
from docc.source import Source

from ethereum_spec_tools.docc import DiffSource, _diff_source_paths


def _render_listing_label(source: DiffSource[Source]) -> str:
    """Render a leaf listing for a single source and return its label text."""
    listing = Listing()
    listing.add_source(source)

    context = Context({Source: source, Listing: listing})
    root = html.HTMLRoot(context)
    render_html(context, root, ListingNode(True))

    for child in root.children:
        if isinstance(child, html.HTMLTag):
            return "".join(child._to_element().itertext()).strip()

    raise AssertionError("listing render produced no HTML output")


def test_diff_source_renders_init_label_but_writes_to_index() -> None:
    """Render `__init__.py` in Browse while preserving the `index` output."""
    relative_path, output_path = _diff_source_paths(
        PurePath("diffs/frontier/homestead"),
        PurePath("vm/__init__.py"),
    )

    old_shape_source: DiffSource[Source] = DiffSource(
        "frontier",
        None,
        "homestead",
        None,
        PurePath("diffs/frontier/homestead/vm/index"),
        PurePath("diffs/frontier/homestead/vm/index"),
    )
    diff_source: DiffSource[Source] = DiffSource(
        "frontier",
        None,
        "homestead",
        None,
        relative_path,
        output_path,
    )

    assert _render_listing_label(old_shape_source) == "index"
    assert _render_listing_label(diff_source) == "__init__.py"
    assert diff_source.output_path == PurePath(
        "diffs/frontier/homestead/vm/index"
    )
    assert diff_source.index_dir == PurePath("diffs/frontier/homestead/vm")


def test_diff_source_renders_normal_module_label() -> None:
    """Render normal modules with their filename unchanged."""
    relative_path, output_path = _diff_source_paths(
        PurePath("diffs/frontier/homestead"),
        PurePath("vm/gas.py"),
    )

    diff_source: DiffSource[Source] = DiffSource(
        "frontier",
        None,
        "homestead",
        None,
        relative_path,
        output_path,
    )

    assert _render_listing_label(diff_source) == "gas.py"
    assert diff_source.output_path == diff_source.relative_path
    assert diff_source.index_dir is None
