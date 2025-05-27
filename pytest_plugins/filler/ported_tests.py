"""
A pytest plugin that shows `ported_from` marker information.

This plugin extracts and displays information from @pytest.mark.ported_from markers,
showing either the static filler file paths or associated PR URLs.

Usage:
------
# Show static filler file paths
uv run fill --show-ported-from tests/

# Show PR URLs instead
uv run fill --show-ported-from=prs tests/

The plugin will:
1. Collect all test items with @pytest.mark.ported_from markers
2. Extract either the file paths (first positional argument) or PR URLs (pr keyword argument)
3. Output a deduplicated, sorted list, one per line
4. Skip test execution (collection only)

Marker Format:
--------------
@pytest.mark.ported_from(
    ["path/to/static_filler1.json", "path/to/static_filler2.json"],
    pr=[
        "https://github.com/ethereum/execution-spec-tests/pull/1234",
        "https://github.com/ethereum/execution-spec-tests/pull/5678",
    ],
)
"""

import re
from typing import List, Set
from urllib.parse import urlparse

import pytest


def convert_to_filled(file_path: str) -> str | None:
    """Convert source link to filler to filled test path."""
    path = urlparse(file_path).path
    if "/src/" in path:
        path = path.split("/src/", 1)[1]

    if path.endswith((".sh", ".js")):
        return None

    # Remove "Filler" from the path components
    path = path.replace("TestsFiller", "Tests")

    # Replace file extension to .json
    path = re.sub(r"Filler\.(yml|yaml|json)$", ".json", path)

    return path


def pytest_addoption(parser: pytest.Parser):
    """Add command-line options to pytest."""
    ported_from_group = parser.getgroup(
        "ported_from", "Arguments for showing ported_from marker information"
    )
    ported_from_group.addoption(
        "--show-ported-from",
        action="store",
        dest="show_ported_from",
        default=None,
        nargs="?",
        const="paths",
        help=(
            "Show information from @pytest.mark.ported_from markers. "
            "Use '--show-ported-from' or '--show-ported-from=paths' to show static filler paths. "
            "Use '--show-ported-from=prs' to show PR URLs."
        ),
    )
    ported_from_group.addoption(
        "--ported-from-output-file",
        action="store",
        dest="ported_from_output_file",
        default=None,
        help="Output file for ported_from information.",
    )
    ported_from_group.addoption(
        "--links-as-filled",
        action="store_true",
        dest="links_as_filled",
        default=False,
        help=(
            "Convert URLs or paths to filled test file paths for coverage script. "
            "Used in combination with --show-ported-from."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Register the plugin if the CLI option is provided."""
    if config.getoption("show_ported_from"):
        config.pluginmanager.register(PortedFromDisplay(config), "ported-from-display")


class PortedFromDisplay:
    """Pytest plugin class for displaying ported_from marker information."""

    def __init__(self, config) -> None:
        """Initialize the plugin with the given pytest config."""
        self.config = config
        self.show_mode = config.getoption("show_ported_from")
        self.links_as_filled = config.getoption("links_as_filled")
        self.ported_from_output_file = config.getoption("ported_from_output_file")

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_collection_modifyitems(
        self,
        session: pytest.Session,
        config: pytest.Config,
        items: List[pytest.Item],
    ):
        """Extract ported_from information from collected test items."""
        yield

        # Only run on master node when using pytest-xdist
        if hasattr(config, "workerinput"):
            return

        paths: Set[str] = set()
        prs: Set[str] = set()

        for item in items:
            ported_from_marker = item.get_closest_marker("ported_from")
            if ported_from_marker:
                # Extract paths (first positional argument)
                if ported_from_marker.args:
                    first_arg = ported_from_marker.args[0]
                    if isinstance(first_arg, list):
                        paths.update(first_arg)
                    elif isinstance(first_arg, str):
                        paths.add(first_arg)

                # Extract PRs (keyword argument 'pr')
                if "pr" in ported_from_marker.kwargs:
                    pr_arg = ported_from_marker.kwargs["pr"]
                    if isinstance(pr_arg, list):
                        prs.update(pr_arg)
                    elif isinstance(pr_arg, str):
                        prs.add(pr_arg)

        # Output results based on mode
        if self.show_mode == "prs":
            outputs = sorted(prs)
        else:  # default to "paths"
            outputs = sorted(paths)
        output_lines: List[str] = []
        if self.links_as_filled:
            for output in outputs:
                converted_link_output = convert_to_filled(output)
                if converted_link_output is not None:
                    output_lines.append(converted_link_output)
        else:
            output_lines.extend(outputs)
        if self.ported_from_output_file:
            with open(self.ported_from_output_file, "w") as f:
                f.write("\n".join(output_lines))
        else:
            for line in output_lines:
                print(line)

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtestloop(self, session):
        """Skip test execution, only show ported_from information."""
        return True

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        """Add a summary line."""
        if config.getoption("verbose") < 0:
            return
        mode_desc = "PR URLs" if self.show_mode == "prs" else "static filler paths"
        terminalreporter.write_sep("=", f"ported_from {mode_desc} displayed", bold=True)
