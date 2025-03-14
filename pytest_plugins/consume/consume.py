"""A pytest plugin providing common functionality for consuming test fixtures."""

import re
import sys
import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urlparse

import platformdirs
import pytest
import requests
import rich

from cli.gen_index import generate_fixtures_index
from ethereum_test_fixtures import BaseFixture
from ethereum_test_fixtures.consume import TestCases
from ethereum_test_forks import get_forks, get_relative_fork_markers, get_transition_forks
from ethereum_test_tools.utility.versioning import get_current_commit_hash_or_tag

from .releases import ReleaseTag, get_release_page_url, get_release_url

CACHED_DOWNLOADS_DIRECTORY = (
    Path(platformdirs.user_cache_dir("ethereum-execution-spec-tests")) / "cached_downloads"
)


def default_input() -> str:
    """
    Directory (default) to consume generated test fixtures from. Defined as a
    function to allow for easier testing.
    """
    return "./fixtures"


def default_html_report_file_path() -> str:
    """
    Filepath (default) to store the generated HTML test report. Defined as a
    function to allow for easier testing.
    """
    return ".meta/report_consume.html"


@dataclass
class FixturesSource:
    """Represents the source of test fixtures."""

    input_option: str
    path: Path
    url: str = ""
    release_page: str = ""
    is_local: bool = True
    is_stdin: bool = False
    was_cached: bool = False

    @classmethod
    def from_input(cls, input_source: str) -> "FixturesSource":
        """Determine the fixture source type and return an instance."""
        if input_source == "stdin":
            return cls(input_option=input_source, path=Path(), is_local=False, is_stdin=True)
        if is_url(input_source):
            return cls.from_url(input_source)
        if ReleaseTag.is_release_string(input_source):
            return cls.from_release_spec(input_source)
        return cls.validate_local_path(Path(input_source))

    @classmethod
    def from_url(cls, url: str) -> "FixturesSource":
        """Create a fixture source from a direct URL."""
        release_page = get_release_page_url(url)
        was_cached, path = download_and_extract(url, CACHED_DOWNLOADS_DIRECTORY)
        return cls(
            input_option=url,
            path=path,
            url=url,
            release_page=release_page,
            is_local=False,
            was_cached=was_cached,
        )

    @classmethod
    def from_release_spec(cls, spec: str) -> "FixturesSource":
        """Create a fixture source from a release spec (e.g., develop@latest)."""
        url = get_release_url(spec)
        release_page = get_release_page_url(url)
        was_cached, path = download_and_extract(url, CACHED_DOWNLOADS_DIRECTORY)
        return cls(
            input_option=spec,
            path=path,
            url=url,
            release_page=release_page,
            is_local=False,
            was_cached=was_cached,
        )

    @staticmethod
    def validate_local_path(path: Path) -> "FixturesSource":
        """Validate that a local fixture path exists and contains JSON files."""
        if not path.exists():
            pytest.exit(f"Specified fixture directory '{path}' does not exist.")
        if not any(path.glob("**/*.json")):
            pytest.exit(f"Specified fixture directory '{path}' does not contain any JSON files.")
        return FixturesSource(input_option=str(path), path=path)


def is_url(string: str) -> bool:
    """Check if a string is a remote URL."""
    result = urlparse(string)
    return all([result.scheme, result.netloc])


def download_and_extract(url: str, base_directory: Path) -> Tuple[bool, Path]:
    """Download the URL and extract it locally if it hasn't already been downloaded."""
    parsed_url = urlparse(url)
    filename = Path(parsed_url.path).name
    version = Path(parsed_url.path).parts[-2]
    extract_to = base_directory / version / filename.removesuffix(".tar.gz")
    already_cached = extract_to.exists()
    if already_cached:
        return already_cached, extract_to / "fixtures"

    extract_to.mkdir(parents=True, exist_ok=False)
    response = requests.get(url)
    response.raise_for_status()

    with tarfile.open(fileobj=BytesIO(response.content), mode="r:gz") as tar:
        tar.extractall(path=extract_to)
    return already_cached, extract_to / "fixtures"


class SimLimitBehavior:
    """Represents options derived from the `--sim.limit` argument."""

    def __init__(self, pattern: str, collectonly: bool = False):  # noqa: D107
        self.pattern = pattern
        self.collectonly = collectonly

    @staticmethod
    def _escape_id(pattern: str) -> str:
        """
        Escape regex char in the pattern; prepend and append '.*' (for `fill` IDs).

        The `pattern` is prefixed and suffixed with a wildcard match to allow `fill`
        test case IDs to be specified, otherwise the full `consume` test ID must be
        specified.
        """
        return f".*{re.escape(pattern)}.*"

    @classmethod
    def from_string(cls, pattern: str) -> "SimLimitBehavior":
        """
        Parse the `--sim.limit` argument and return a `SimLimitBehavior` instance.

        If `pattern`:
        - Is "collectonly", enable collection mode without filtering.
        - Starts with "collectonly:", enable collection mode and use the rest as a regex pattern.
        - Starts with "id:", treat the rest as a literal test ID and escape special regex chars.
        - Starts with "collectonly:id:", enable collection mode with a literal test ID.
        """
        if pattern == "collectonly":
            return cls(pattern=".*", collectonly=True)

        if pattern.startswith("collectonly:id:"):
            literal_id = pattern[len("collectonly:id:") :]
            if not literal_id:
                raise ValueError("Empty literal ID provided.")
            return cls(pattern=cls._escape_id(literal_id), collectonly=True)

        if pattern.startswith("collectonly:"):
            return cls(pattern=pattern[len("collectonly:") :], collectonly=True)

        if pattern.startswith("id:"):
            literal_id = pattern[len("id:") :]
            if not literal_id:
                raise ValueError("Empty literal ID provided.")
            return cls(pattern=cls._escape_id(literal_id))

        return cls(pattern=pattern)


def pytest_addoption(parser):  # noqa: D103
    consume_group = parser.getgroup(
        "consume", "Arguments related to consuming fixtures via a client"
    )
    consume_group.addoption(
        "--input",
        action="store",
        dest="fixtures_source",
        default=None,
        help=(
            "Specify the JSON test fixtures source. Can be a local directory, a URL pointing to a "
            " fixtures.tar.gz archive, a release name and version in the form of `NAME@v1.2.3` "
            "(`stable` and `develop` are valid release names, and `latest` is a valid version), "
            "or the special keyword 'stdin'. "
            f"Defaults to the following local directory: '{default_input()}'."
        ),
    )
    consume_group.addoption(
        "--cache-folder",
        action="store",
        dest="fixture_cache_folder",
        default=CACHED_DOWNLOADS_DIRECTORY,
        help=(
            "Specify the path where the downloaded fixtures are cached. "
            f"Defaults to the following directory: '{CACHED_DOWNLOADS_DIRECTORY}'."
        ),
    )
    if "cache" in sys.argv:
        return
    consume_group.addoption(
        "--no-html",
        action="store_true",
        dest="disable_html",
        default=False,
        help=(
            "Don't generate an HTML test report (in the output directory). "
            "The --html flag can be used to specify a different path."
        ),
    )
    consume_group.addoption(
        "--sim.limit",
        action="store",
        dest="sim_limit",
        type=SimLimitBehavior.from_string,
        default=SimLimitBehavior(".*"),
        help=(
            "Filter tests by either a regex pattern or a literal test case ID. To match a "
            "test case by its exact ID, prefix the ID with `id:`. The string following `id:` "
            "will be automatically escaped so that all special regex characters are treated as "
            "literals. Without the `id:` prefix, the argument is interpreted as a Python regex "
            "pattern. To see which test cases are matched, without executing them, prefix with "
            '`collectonly:`, e.g. `--sim.limit "collectonly:.*eip4788.*fork_Prague.*"`. '
            "To list all available test case IDs, set the value to `collectonly`."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):  # noqa: D103
    """
    Pytest hook called after command line options have been parsed and before
    test collection begins.

    `@pytest.hookimpl(tryfirst=True)` is applied to ensure that this hook is
    called before the pytest-html plugin's pytest_configure to ensure that
    it uses the modified `htmlpath` option.
    """
    if config.option.fixtures_source is None:
        # NOTE: Setting the default value here is necessary for correct stdin/piping behavior.
        config.fixtures_source = FixturesSource(
            input_option=default_input(), path=Path(default_input())
        )
    else:
        # NOTE: Setting `type=FixturesSource.from_input` in pytest_addoption() causes the option to
        # be evaluated twice which breaks the result of `was_cached`; the work-around is to call it
        # manually here.
        config.fixtures_source = FixturesSource.from_input(config.option.fixtures_source)
    config.fixture_source_flags = ["--input", config.fixtures_source.input_option]

    if "cache" in sys.argv and not config.fixtures_source:
        pytest.exit("The --input flag is required when using the cache command.")

    if "cache" in sys.argv:
        reason = ""
        if config.fixtures_source.was_cached:
            reason += "Fixtures already cached."
        elif not config.fixtures_source.is_local:
            reason += "Fixtures downloaded and cached."
        reason += (
            f"\nPath: {config.fixtures_source.path}\n"
            f"Input: {config.fixtures_source.url or config.fixtures_source.path}\n"
            f"Release page: {config.fixtures_source.release_page or 'None'}"
        )
        pytest.exit(
            returncode=0,
            reason=reason,
        )

    if config.fixtures_source.is_stdin:
        config.test_cases = TestCases.from_stream(sys.stdin)
        return
    index_file = config.fixtures_source.path / ".meta" / "index.json"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    if not index_file.exists():
        rich.print(f"Generating index file [bold cyan]{index_file}[/]...")
        generate_fixtures_index(
            config.fixtures_source.path,
            quiet_mode=False,
            force_flag=False,
            disable_infer_format=False,
        )
    config.test_cases = TestCases.from_index_file(index_file)

    all_forks_with_transitions = {  # type: ignore
        fork for fork in set(get_forks()) | get_transition_forks() if not fork.ignore()
    }
    for fixture_format in BaseFixture.formats.values():
        config.addinivalue_line(
            "markers",
            f"{fixture_format.format_name}: Tests in `{fixture_format.format_name}` format ",
        )
    for fork in all_forks_with_transitions:
        config.addinivalue_line("markers", f"{fork}: Tests for the {fork} fork")

    if config.option.sim_limit:
        if config.option.dest_regex != ".*":
            pytest.exit(
                "Both the --sim.limit (via env var?) and the --regex flags are set. "
                "Please only set one of them."
            )
        config.option.dest_regex = config.option.sim_limit.pattern
        if config.option.sim_limit.collectonly:
            config.option.collectonly = True
            config.option.verbose = -1  # equivalent to -q; only print test ids

    if config.option.collectonly or config.option.markers:
        return
    if not config.getoption("disable_html") and config.getoption("htmlpath") is None:
        # generate an html report by default, unless explicitly disabled
        config.option.htmlpath = Path(default_html_report_file_path())


def pytest_html_report_title(report):
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Consume Test Report"


def pytest_report_header(config):
    """Add the consume version and fixtures source to the report header."""
    source = config.fixtures_source
    lines = [
        f"consume ref: {get_current_commit_hash_or_tag()}",
        f"fixtures: {source.path}",
    ]
    if not source.is_local and not source.is_stdin:
        lines.append(f"fixtures url: {source.url}")
        lines.append(f"fixtures release: {source.release_page}")
    return lines


@pytest.fixture(scope="session")
def fixture_source_flags(request) -> List[str]:
    """Return the input flags used to specify the JSON test fixtures source."""
    return request.config.fixture_source_flags


@pytest.fixture(scope="session")
def fixtures_source(request) -> FixturesSource:  # noqa: D103
    return request.config.fixtures_source


def pytest_generate_tests(metafunc):
    """
    Generate test cases for every test fixture in all the JSON fixture files
    within the specified fixtures directory, or read from stdin if the directory is 'stdin'.
    """
    if "cache" in sys.argv:
        return

    test_cases = metafunc.config.test_cases
    param_list = []
    for test_case in test_cases:
        fork_markers = get_relative_fork_markers(test_case.fork)
        param = pytest.param(
            test_case,
            test_case.format,
            id=test_case.id,
            marks=[getattr(pytest.mark, m) for m in fork_markers]
            + [getattr(pytest.mark, test_case.format.format_name)],
        )
        param_list.append(param)

    metafunc.parametrize("test_case,fixture_format", param_list)

    if "client_type" in metafunc.fixturenames:
        client_ids = [client.name for client in metafunc.config.hive_execution_clients]
        metafunc.parametrize("client_type", metafunc.config.hive_execution_clients, ids=client_ids)


def pytest_collection_modifyitems(items):
    """Modify collected item names to remove the test runner function from the name."""
    for item in items:
        original_name = item.originalname
        remove = f"{original_name}["
        if item.name.startswith(remove):
            item.name = item.name[len(remove) : -1]
