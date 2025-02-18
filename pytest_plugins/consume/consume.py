"""A pytest plugin providing common functionality for consuming test fixtures."""

import sys
import tarfile
from io import BytesIO
from pathlib import Path
from typing import List, Literal, Union
from urllib.parse import urlparse

import platformdirs
import pytest
import requests
import rich

from cli.gen_index import generate_fixtures_index
from ethereum_test_fixtures.consume import TestCases
from ethereum_test_tools.utility.versioning import get_current_commit_hash_or_tag

from .releases import ReleaseTag, get_release_url

CACHED_DOWNLOADS_DIRECTORY = (
    Path(platformdirs.user_cache_dir("ethereum-execution-spec-tests")) / "cached_downloads"
)

FixturesSource = Union[Path, Literal["stdin"]]


def default_input_directory() -> str:
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


def is_url(string: str) -> bool:
    """Check if a string is a remote URL."""
    result = urlparse(string)
    return all([result.scheme, result.netloc])


def download_and_extract(url: str, base_directory: Path) -> Path:
    """Download the URL and extract it locally if it hasn't already been downloaded."""
    parsed_url = urlparse(url)
    filename = Path(parsed_url.path).name
    version = Path(parsed_url.path).parts[-2]
    extract_to = base_directory / version / filename.removesuffix(".tar.gz")

    if extract_to.exists():
        # skip download if the archive has already been downloaded
        return extract_to / "fixtures"

    extract_to.mkdir(parents=True, exist_ok=False)
    response = requests.get(url)
    response.raise_for_status()

    with tarfile.open(fileobj=BytesIO(response.content), mode="r:gz") as tar:  # noqa: SC200
        tar.extractall(path=extract_to)

    return extract_to / "fixtures"


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
            f"Defaults to the following local directory: '{default_input_directory()}'."
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
        "--fork",
        action="store",
        dest="single_fork",
        default=None,
        help="Only consume tests for the specified fork.",
    )
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


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):  # noqa: D103
    """
    Pytest hook called after command line options have been parsed and before
    test collection begins.

    `@pytest.hookimpl(tryfirst=True)` is applied to ensure that this hook is
    called before the pytest-html plugin's pytest_configure to ensure that
    it uses the modified `htmlpath` option.
    """
    fixtures_source = config.getoption("fixtures_source")
    if "cache" in sys.argv and not config.getoption("fixtures_source"):
        pytest.exit("The --input flag is required when using the cache command.")
    config.fixture_source_flags = ["--input", fixtures_source]

    if fixtures_source is None:
        config.fixture_source_flags = []
        fixtures_source = default_input_directory()
    elif fixtures_source == "stdin":
        config.test_cases = TestCases.from_stream(sys.stdin)
        config.fixtures_real_source = "stdin"
        config.fixtures_source = "stdin"
        return
    elif ReleaseTag.is_release_string(fixtures_source):
        fixtures_source = get_release_url(fixtures_source)

    config.fixtures_real_source = fixtures_source
    if is_url(fixtures_source):
        cached_downloads_directory = Path(config.getoption("fixture_cache_folder"))
        cached_downloads_directory.mkdir(parents=True, exist_ok=True)
        fixtures_source = download_and_extract(fixtures_source, cached_downloads_directory)

    fixtures_source = Path(fixtures_source)
    config.fixtures_source = fixtures_source
    if not fixtures_source.exists():
        pytest.exit(f"Specified fixture directory '{fixtures_source}' does not exist.")
    if not any(fixtures_source.glob("**/*.json")):
        pytest.exit(
            f"Specified fixture directory '{fixtures_source}' does not contain any JSON files."
        )

    index_file = fixtures_source / ".meta" / "index.json"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    if not index_file.exists():
        rich.print(f"Generating index file [bold cyan]{index_file}[/]...")
        generate_fixtures_index(
            fixtures_source, quiet_mode=False, force_flag=False, disable_infer_format=False
        )
    config.test_cases = TestCases.from_index_file(index_file)

    if config.option.collectonly or "cache" in sys.argv:
        return
    if not config.getoption("disable_html") and config.getoption("htmlpath") is None:
        # generate an html report by default, unless explicitly disabled
        config.option.htmlpath = Path(default_html_report_file_path())


def pytest_html_report_title(report):
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Consume Test Report"


def pytest_report_header(config):  # noqa: D103
    consume_version = f"consume commit: {get_current_commit_hash_or_tag()}"
    fixtures_real_source = f"fixtures: {config.fixtures_real_source}"
    return [consume_version, fixtures_real_source]


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

    fork = metafunc.config.getoption("single_fork")
    metafunc.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in metafunc.config.test_cases
            if test_case.format in metafunc.function.fixture_format
            and (not fork or test_case.fork == fork)
        ),
    )
    metafunc.parametrize(
        "fixture_format",
        (
            pytest.param(fixture_format, id=fixture_format.format_name)
            for fixture_format in metafunc.function.fixture_format
        ),
    )

    if "client_type" in metafunc.fixturenames:
        client_ids = [client.name for client in metafunc.config.hive_execution_clients]
        metafunc.parametrize("client_type", metafunc.config.hive_execution_clients, ids=client_ids)


def pytest_collection_modifyitems(session, config, items):
    """Modify collected item names to remove the test runner function from the name."""
    for item in items:
        original_name = item.originalname
        remove = f"{original_name}["
        if item.name.startswith(remove):
            item.name = item.name[len(remove) : -1]
