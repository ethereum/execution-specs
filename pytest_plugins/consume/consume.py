"""
A pytest plugin providing common functionality for consuming test fixtures.
"""

import os
import sys
import tarfile
from pathlib import Path
from typing import Literal, Union
from urllib.parse import urlparse

import pytest
import requests
import rich

from cli.gen_index import generate_fixtures_index
from ethereum_test_fixtures.consume import TestCases
from ethereum_test_tools.utility.versioning import get_current_commit_hash_or_tag

cached_downloads_directory = Path("./cached_downloads")

JsonSource = Union[Path, Literal["stdin"]]


def default_input_directory() -> str:
    """
    The default directory to consume generated test fixtures from. Defined as a
    function to allow for easier testing.
    """
    return "./fixtures"


def default_html_report_file_path() -> str:
    """
    The default filepath to store the generated HTML test report. Defined as a
    function to allow for easier testing.
    """
    return ".meta/report_consume.html"


def is_url(string: str) -> bool:
    """
    Check if a string is a remote URL.
    """
    result = urlparse(string)
    return all([result.scheme, result.netloc])


def download_and_extract(url: str, base_directory: Path) -> Path:
    """
    Download the URL and extract it locally if it hasn't already been downloaded.
    """
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

    archive_path = extract_to / filename
    with open(archive_path, "wb") as file:
        file.write(response.content)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=extract_to)

    return extract_to / "fixtures"


def pytest_addoption(parser):  # noqa: D103
    consume_group = parser.getgroup(
        "consume", "Arguments related to consuming fixtures via a client"
    )
    consume_group.addoption(
        "--input",
        action="store",
        dest="fixture_source",
        default=default_input_directory(),
        help=(
            "A URL or local directory specifying the JSON test fixtures. Default: "
            f"'{default_input_directory()}'."
        ),
    )
    consume_group.addoption(
        "--latest",
        action="store_true",
        dest="latest_source",
        default=False,
        help=(
            "The latest EEST development JSON test fixtures. Cannot be used alongside `--input`."
        ),
    )
    consume_group.addoption(
        "--fork",
        action="store",
        dest="single_fork",
        default=None,
        help="Only consume tests for the specified fork.",
    )
    consume_group.addoption(
        "--timing-data",
        action="store_true",
        dest="timing_data",
        default=False,
        help="Log the timing data for each test case execution.",
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
    input_flag = any(arg.startswith("--input") for arg in config.invocation_params.args)
    latest_flag = config.getoption("latest_source")

    if input_flag and latest_flag:
        pytest.exit("Cannot use both `--input` and `--latest`, please select one input flag.")

    input_source = config.getoption("fixture_source")

    if input_flag and input_source == "stdin":
        config.test_cases = TestCases.from_stream(sys.stdin)
        return

    if latest_flag:
        release_base_url = "https://github.com/ethereum/execution-spec-tests/releases"
        input_source = f"{release_base_url}/latest/download/fixtures_develop.tar.gz"

    if is_url(input_source):
        cached_downloads_directory.mkdir(parents=True, exist_ok=True)
        input_source = download_and_extract(input_source, cached_downloads_directory)
        config.option.fixture_source = input_source

    input_source = Path(input_source)
    if not input_source.exists():
        pytest.exit(f"Specified fixture directory '{input_source}' does not exist.")
    if not any(input_source.glob("**/*.json")):
        pytest.exit(
            f"Specified fixture directory '{input_source}' does not contain any JSON files."
        )

    index_file = input_source / ".meta" / "index.json"
    if not index_file.exists():
        rich.print(f"Generating index file [bold cyan]{index_file}[/]...")
        generate_fixtures_index(
            input_source, quiet_mode=False, force_flag=False, disable_infer_format=False
        )
    config.test_cases = TestCases.from_index_file(index_file)

    if config.option.collectonly:
        return
    if not config.getoption("disable_html") and config.getoption("htmlpath") is None:
        # generate an html report by default, unless explicitly disabled
        config.option.htmlpath = os.path.join(
            config.getoption("fixture_source"), default_html_report_file_path()
        )


def pytest_html_report_title(report):
    """
    Set the HTML report title (pytest-html plugin).
    """
    report.title = "Consume Test Report"


def pytest_report_header(config):  # noqa: D103
    consume_version = f"consume commit: {get_current_commit_hash_or_tag()}"
    input_source = f"fixtures: {config.getoption('fixture_source')}"
    return [consume_version, input_source]


@pytest.fixture(scope="function")
def fixture_source(request) -> JsonSource:  # noqa: D103
    return request.config.getoption("fixture_source")


def pytest_generate_tests(metafunc):
    """
    Generate test cases for every test fixture in all the JSON fixture files
    within the specified fixtures directory, or read from stdin if the directory is 'stdin'.
    """
    fork = metafunc.config.getoption("single_fork")
    metafunc.parametrize(
        "test_case",
        (
            pytest.param(test_case, id=test_case.id)
            for test_case in metafunc.config.test_cases
            if test_case.format in metafunc.function.fixture_formats
            and (not fork or test_case.fork == fork)
        ),
    )

    if "client_type" in metafunc.fixturenames:
        client_ids = [client.name for client in metafunc.config.hive_execution_clients]
        metafunc.parametrize("client_type", metafunc.config.hive_execution_clients, ids=client_ids)


def pytest_collection_modifyitems(session, config, items):
    """
    Modify collected item names to remove the test runner function from the name.
    """
    for item in items:
        original_name = item.originalname
        remove = f"{original_name}["
        if item.name.startswith(remove):
            item.name = item.name[len(remove) : -1]
