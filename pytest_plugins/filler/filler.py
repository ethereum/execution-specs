"""
Top-level pytest configuration file providing:
- Command-line options,
- Test-fixtures that can be used by all test cases,
and that modifies pytest hooks in order to fill test specs for all tests and
writes the generated fixtures to file.
"""

import configparser
import datetime
import os
import tarfile
import warnings
from pathlib import Path
from typing import Any, Dict, Generator, List, Type

import pytest
from _pytest.terminal import TerminalReporter
from filelock import FileLock
from pytest_metadata.plugin import metadata_key  # type: ignore

from cli.gen_index import generate_fixtures_index
from config import AppConfig
from ethereum_clis import TransitionTool
from ethereum_test_base_types import Alloc, ReferenceSpec
from ethereum_test_fixtures import BaseFixture, FixtureCollector, TestInfo
from ethereum_test_forks import Fork
from ethereum_test_specs import SPEC_TYPES, BaseTest
from ethereum_test_tools.utility.versioning import (
    generate_github_url,
    get_current_commit_hash_or_tag,
)
from pytest_plugins.spec_version_checker.spec_version_checker import EIPSpecTestItem


def default_output_directory() -> str:
    """
    Directory (default) to store the generated test fixtures. Defined as a
    function to allow for easier testing.
    """
    return "./fixtures"


def default_html_report_file_path() -> str:
    """
    File path (default) to store the generated HTML test report. Defined as a
    function to allow for easier testing.
    """
    return ".meta/report_fill.html"


def strip_output_tarball_suffix(output: Path) -> Path:
    """Strip the '.tar.gz' suffix from the output path."""
    if str(output).endswith(".tar.gz"):
        return output.with_suffix("").with_suffix("")
    return output


def is_output_stdout(output: Path) -> bool:
    """Return True if the fixture output is configured to be stdout."""
    return strip_output_tarball_suffix(output).name == "stdout"


def pytest_addoption(parser: pytest.Parser):
    """Add command-line options to pytest."""
    evm_group = parser.getgroup("evm", "Arguments defining evm executable behavior")
    evm_group.addoption(
        "--evm-bin",
        action="store",
        dest="evm_bin",
        type=Path,
        default="ethereum-spec-evm-resolver",
        help=(
            "Path to an evm executable (or name of an executable in the PATH) that provides `t8n`."
            " Default: `ethereum-spec-evm-resolver`."
        ),
    )
    evm_group.addoption(
        "--traces",
        action="store_true",
        dest="evm_collect_traces",
        default=None,
        help="Collect traces of the execution information from the transition tool.",
    )
    evm_group.addoption(
        "--verify-fixtures",
        action="store_true",
        dest="verify_fixtures",
        default=False,
        help=(
            "Verify generated fixture JSON files using geth's evm blocktest command. "
            "By default, the same evm binary as for the t8n tool is used. A different (geth) evm "
            "binary may be specified via --verify-fixtures-bin, this must be specified if filling "
            "with a non-geth t8n tool that does not support blocktest."
        ),
    )
    evm_group.addoption(
        "--verify-fixtures-bin",
        action="store",
        dest="verify_fixtures_bin",
        type=Path,
        default=None,
        help=(
            "Path to an evm executable that provides the `blocktest` command. "
            "Default: The first (geth) 'evm' entry in PATH."
        ),
    )

    test_group = parser.getgroup("tests", "Arguments defining filler location and output")
    test_group.addoption(
        "--filler-path",
        action="store",
        dest="filler_path",
        default="./tests/",
        type=Path,
        help="Path to filler directives",
    )
    test_group.addoption(
        "--output",
        action="store",
        dest="output",
        type=Path,
        default=Path(default_output_directory()),
        help=(
            "Directory path to store the generated test fixtures. "
            "If the specified path ends in '.tar.gz', then the specified tarball is additionally "
            "created (the fixtures are still written to the specified path without the '.tar.gz' "
            f"suffix). Can be deleted. Default: '{default_output_directory()}'."
        ),
    )
    test_group.addoption(
        "--flat-output",
        action="store_true",
        dest="flat_output",
        default=False,
        help="Output each test case in the directory without the folder structure.",
    )
    test_group.addoption(
        "--single-fixture-per-file",
        action="store_true",
        dest="single_fixture_per_file",
        default=False,
        help=(
            "Don't group fixtures in JSON files by test function; write each fixture to its own "
            "file. This can be used to increase the granularity of --verify-fixtures."
        ),
    )
    test_group.addoption(
        "--no-html",
        action="store_true",
        dest="disable_html",
        default=False,
        help=(
            "Don't generate an HTML test report (in the output directory). "
            "The --html flag can be used to specify a different path."
        ),
    )
    test_group.addoption(
        "--build-name",
        action="store",
        dest="build_name",
        default=None,
        type=str,
        help="Specify a build name for the fixtures.ini file, e.g., 'stable'.",
    )
    test_group.addoption(
        "--index",
        action="store_true",
        dest="generate_index",
        default=False,
        help="Generate an index file for all produced fixtures.",
    )

    debug_group = parser.getgroup("debug", "Arguments defining debug behavior")
    debug_group.addoption(
        "--evm-dump-dir",
        "--t8n-dump-dir",
        action="store",
        dest="base_dump_dir",
        default=AppConfig().DEFAULT_EVM_LOGS_DIR,
        help=(
            "Path to dump the transition tool debug output. "
            f"(Default: {AppConfig().DEFAULT_EVM_LOGS_DIR})"
        ),
    )
    debug_group.addoption(
        "--skip-evm-dump",
        "--skip-t8n-dump",
        action="store_true",
        dest="skip_dump_dir",
        default=False,
        help=("Skip dumping the the transition tool debug output."),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Pytest hook called after command line options have been parsed and before
    test collection begins.

    Couple of notes:
    1. Register the plugin's custom markers and process command-line options.

        Custom marker registration:
        https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers

    2. `@pytest.hookimpl(tryfirst=True)` is applied to ensure that this hook is
        called before the pytest-html plugin's pytest_configure to ensure that
        it uses the modified `htmlpath` option.
    """
    if config.option.collectonly:
        return
    if not config.getoption("disable_html") and config.getoption("htmlpath") is None:
        # generate an html report by default, unless explicitly disabled
        config.option.htmlpath = (
            strip_output_tarball_suffix(config.getoption("output"))
            / default_html_report_file_path()
        )
    # Instantiate the transition tool here to check that the binary path/trace option is valid.
    # This ensures we only raise an error once, if appropriate, instead of for every test.
    t8n = TransitionTool.from_binary_path(
        binary_path=config.getoption("evm_bin"), trace=config.getoption("evm_collect_traces")
    )
    if (
        isinstance(config.getoption("numprocesses"), int)
        and config.getoption("numprocesses") > 0
        and "Besu" in str(t8n.detect_binary_pattern)
    ):
        pytest.exit(
            "The Besu t8n tool does not work well with the xdist plugin; use -n=0.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    if "Tools" not in config.stash[metadata_key]:
        config.stash[metadata_key]["Tools"] = {
            "t8n": t8n.version(),
        }
    else:
        config.stash[metadata_key]["Tools"]["t8n"] = t8n.version()

    args = ["fill"] + [str(arg) for arg in config.invocation_params.args]
    for i in range(len(args)):
        if " " in args[i]:
            args[i] = f'"{args[i]}"'
    command_line_args = " ".join(args)
    config.stash[metadata_key]["Command-line args"] = f"<code>{command_line_args}</code>"


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: pytest.Config):
    """Add lines to pytest's console output header."""
    if config.option.collectonly:
        return
    t8n_version = config.stash[metadata_key]["Tools"]["t8n"]
    return [(f"{t8n_version}")]


def pytest_report_teststatus(report, config: pytest.Config):
    """
    Modify test results in pytest's terminal output.

    We use this:

    1. To disable test session progress report if we're writing the JSON
        fixtures to stdout to be read by a consume command on stdin. I.e.,
        don't write this type of output to the console:
    ```text
    ...x...
    ```
    """
    if is_output_stdout(config.getoption("output")):
        return report.outcome, "", report.outcome.upper()


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter, exitstatus: int, config: pytest.Config
):
    """
    Modify pytest's terminal summary to emphasize that no tests were ran.

    Emphasize that fixtures have only been filled; they must now be executed to
    actually run the tests.
    """
    yield
    stats = terminalreporter.stats
    if "passed" in stats and stats["passed"]:
        # append / to indicate this is a directory
        output_dir = str(strip_output_tarball_suffix(config.getoption("output"))) + "/"
        terminalreporter.write_sep(
            "=",
            (
                f' No tests executed - the test fixtures in "{output_dir}" may now be executed '
                "against a client "
            ),
            bold=True,
            yellow=True,
        )


def pytest_metadata(metadata):
    """Add or remove metadata to/from the pytest report."""
    metadata.pop("JAVA_HOME", None)


def pytest_html_results_table_header(cells):
    """Customize the table headers of the HTML report table."""
    cells.insert(3, '<th class="sortable" data-column-type="fixturePath">JSON Fixture File</th>')
    cells.insert(4, '<th class="sortable" data-column-type="evmDumpDir">EVM Dump Dir</th>')
    del cells[-1]  # Remove the "Links" column


def pytest_html_results_table_row(report, cells):
    """Customize the table rows of the HTML report table."""
    if hasattr(report, "user_properties"):
        user_props = dict(report.user_properties)
        if (
            report.passed
            and "fixture_path_absolute" in user_props
            and "fixture_path_relative" in user_props
        ):
            fixture_path_absolute = user_props["fixture_path_absolute"]
            fixture_path_relative = user_props["fixture_path_relative"]
            fixture_path_link = (
                f'<a href="{fixture_path_absolute}" target="_blank">{fixture_path_relative}</a>'
            )
            cells.insert(3, f"<td>{fixture_path_link}</td>")
        elif report.failed:
            cells.insert(3, "<td>Fixture unavailable</td>")
        if "evm_dump_dir" in user_props:
            if user_props["evm_dump_dir"] is None:
                cells.insert(
                    4, "<td>For t8n debug info use <code>--evm-dump-dir=path --traces</code></td>"
                )
            else:
                evm_dump_dir = user_props.get("evm_dump_dir")
                if evm_dump_dir == "N/A":
                    evm_dump_entry = "N/A"
                else:
                    evm_dump_entry = f'<a href="{evm_dump_dir}" target="_blank">{evm_dump_dir}</a>'
                cells.insert(4, f"<td>{evm_dump_entry}</td>")
    del cells[-1]  # Remove the "Links" column


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make each test's fixture json path available to the test report via
    user_properties.

    This hook is called when each test is run and a report is being made.
    """
    outcome = yield
    report = outcome.get_result()

    if call.when == "call":
        if hasattr(item.config, "fixture_path_absolute") and hasattr(
            item.config, "fixture_path_relative"
        ):
            report.user_properties.append(
                ("fixture_path_absolute", item.config.fixture_path_absolute)
            )
            report.user_properties.append(
                ("fixture_path_relative", item.config.fixture_path_relative)
            )
        if hasattr(item.config, "evm_dump_dir") and hasattr(item.config, "fixture_format"):
            if item.config.fixture_format in [
                "state_test",
                "blockchain_test",
                "blockchain_test_engine",
            ]:
                report.user_properties.append(("evm_dump_dir", item.config.evm_dump_dir))
            else:
                report.user_properties.append(("evm_dump_dir", "N/A"))  # not yet for EOF


def pytest_html_report_title(report):
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Fill Test Report"


@pytest.fixture(autouse=True, scope="session")
def evm_bin(request: pytest.FixtureRequest) -> Path:
    """Return configured evm tool binary path used to run t8n."""
    return request.config.getoption("evm_bin")


@pytest.fixture(autouse=True, scope="session")
def verify_fixtures_bin(request: pytest.FixtureRequest) -> Path | None:
    """
    Return configured evm tool binary path used to run statetest or
    blocktest.
    """
    return request.config.getoption("verify_fixtures_bin")


@pytest.fixture(autouse=True, scope="session")
def t8n(request: pytest.FixtureRequest, evm_bin: Path) -> Generator[TransitionTool, None, None]:
    """Return configured transition tool."""
    t8n = TransitionTool.from_binary_path(
        binary_path=evm_bin, trace=request.config.getoption("evm_collect_traces")
    )
    yield t8n
    t8n.shutdown()


@pytest.fixture(scope="session")
def do_fixture_verification(
    request: pytest.FixtureRequest, verify_fixtures_bin: Path | None
) -> bool:
    """
    Return True if evm statetest or evm blocktest should be ran on the
    generated fixture JSON files.
    """
    do_fixture_verification = False
    if verify_fixtures_bin:
        do_fixture_verification = True
    if request.config.getoption("verify_fixtures"):
        do_fixture_verification = True
    return do_fixture_verification


@pytest.fixture(autouse=True, scope="session")
def evm_fixture_verification(
    do_fixture_verification: bool,
    evm_bin: Path,
    verify_fixtures_bin: Path | None,
) -> Generator[TransitionTool | None, None, None]:
    """
    Return configured evm binary for executing statetest and blocktest
    commands used to verify generated JSON fixtures.
    """
    if not do_fixture_verification:
        yield None
        return
    if not verify_fixtures_bin and evm_bin:
        verify_fixtures_bin = evm_bin
    evm_fixture_verification = TransitionTool.from_binary_path(binary_path=verify_fixtures_bin)
    if not evm_fixture_verification.blocktest_subcommand:
        pytest.exit(
            "Only geth's evm tool is supported to verify fixtures: "
            "Either remove --verify-fixtures or set --verify-fixtures-bin to a Geth evm binary.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    yield evm_fixture_verification
    evm_fixture_verification.shutdown()


@pytest.fixture(scope="session")
def base_dump_dir(request: pytest.FixtureRequest) -> Path | None:
    """Path to base directory to dump the evm debug output."""
    if request.config.getoption("skip_dump_dir"):
        return None
    base_dump_dir_str = request.config.getoption("base_dump_dir")
    if base_dump_dir_str:
        return Path(base_dump_dir_str)
    return None


@pytest.fixture(scope="session")
def is_output_tarball(request: pytest.FixtureRequest) -> bool:
    """Return True if the output directory is a tarball."""
    output: Path = request.config.getoption("output")
    if output.suffix == ".gz" and output.with_suffix("").suffix == ".tar":
        return True
    return False


@pytest.fixture(scope="session")
def output_dir(request: pytest.FixtureRequest, is_output_tarball: bool) -> Path:
    """Return directory to store the generated test fixtures."""
    output = request.config.getoption("output")
    if is_output_tarball:
        return strip_output_tarball_suffix(output)
    return output


@pytest.fixture(scope="session")
def output_metadata_dir(output_dir: Path) -> Path:
    """Return metadata directory to store fixture meta files."""
    return output_dir / ".meta"


@pytest.fixture(scope="session", autouse=True)
def create_properties_file(
    request: pytest.FixtureRequest, output_dir: Path, output_metadata_dir: Path
) -> None:
    """
    Create ini file with fixture build properties in the fixture output
    directory.
    """
    if is_output_stdout(request.config.getoption("output")):
        return
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    if not output_metadata_dir.exists():
        output_metadata_dir.mkdir(parents=True)

    fixture_properties = {
        "timestamp": datetime.datetime.now().isoformat(),
    }
    if build_name := request.config.getoption("build_name"):
        fixture_properties["build"] = build_name
    if github_ref := os.getenv("GITHUB_REF"):
        fixture_properties["ref"] = github_ref
    if github_sha := os.getenv("GITHUB_SHA"):
        fixture_properties["commit"] = github_sha
    command_line_args = request.config.stash[metadata_key]["Command-line args"]
    command_line_args = command_line_args.replace("<code>", "").replace("</code>", "")
    fixture_properties["command_line_args"] = command_line_args

    config = configparser.ConfigParser(interpolation=None)
    config["fixtures"] = fixture_properties
    environment_properties = {}
    for key, val in request.config.stash[metadata_key].items():
        if key.lower() == "command-line args":
            continue
        if key.lower() in ["ci", "python", "platform"]:
            environment_properties[key] = val
        elif isinstance(val, dict):
            config[key.lower()] = val
        else:
            warnings.warn(
                f"Fixtures ini file: Skipping metadata key {key} with value {val}.", stacklevel=2
            )
    config["environment"] = environment_properties

    ini_filename = output_metadata_dir / "fixtures.ini"
    with open(ini_filename, "w") as f:
        f.write("; This file describes fixture build properties\n\n")
        config.write(f)


@pytest.fixture(scope="session", autouse=True)
def create_tarball(
    request: pytest.FixtureRequest, output_dir: Path, is_output_tarball: bool
) -> Generator[None, None, None]:
    """
    Create a tarball of json files the output directory if the configured
    output ends with '.tar.gz'.

    Only include .json and .ini files in the archive.
    """
    yield
    if is_output_tarball:
        source_dir = output_dir
        tarball_filename = request.config.getoption("output")
        with tarfile.open(tarball_filename, "w:gz") as tar:
            for file in source_dir.rglob("*"):
                if file.suffix in {".json", ".ini"}:
                    arcname = Path("fixtures") / file.relative_to(source_dir)
                    tar.add(file, arcname=arcname)


@pytest.fixture(scope="function")
def dump_dir_parameter_level(
    request: pytest.FixtureRequest, base_dump_dir: Path | None, filler_path: Path
) -> Path | None:
    """
    Directory to dump evm transition tool debug output on a test parameter
    level.

    Example with --evm-dump-dir=/tmp/evm:
    -> /tmp/evm/shanghai__eip3855_push0__test_push0__test_push0_key_sstore/fork_shanghai/
    """
    evm_dump_dir = node_to_test_info(request.node).get_dump_dir_path(
        base_dump_dir,
        filler_path,
        level="test_parameter",
    )
    # NOTE: Use str for compatibility with pytest-dist
    if evm_dump_dir:
        request.node.config.evm_dump_dir = str(evm_dump_dir)
    else:
        request.node.config.evm_dump_dir = None
    return evm_dump_dir


def get_fixture_collection_scope(fixture_name, config):
    """
    Return the appropriate scope to write fixture JSON files.

    See: https://docs.pytest.org/en/stable/how-to/fixtures.html#dynamic-scope
    """
    if is_output_stdout(config.getoption("output")):
        return "session"
    if config.getoption("single_fixture_per_file"):
        return "function"
    return "module"


@pytest.fixture(scope="session")
def generate_index(request) -> bool:  # noqa: D103
    return request.config.option.generate_index


@pytest.fixture(scope=get_fixture_collection_scope)
def fixture_collector(
    request: pytest.FixtureRequest,
    do_fixture_verification: bool,
    evm_fixture_verification: TransitionTool,
    filler_path: Path,
    base_dump_dir: Path | None,
    output_dir: Path,
    session_temp_folder: Path | None,
    generate_index: bool,
) -> Generator[FixtureCollector, None, None]:
    """
    Return configured fixture collector instance used for all tests
    in one test module.
    """
    if session_temp_folder is not None:
        fixture_collector_count_file_name = "fixture_collector_count"
        fixture_collector_count_file = session_temp_folder / fixture_collector_count_file_name
        fixture_collector_count_file_lock = (
            session_temp_folder / f"{fixture_collector_count_file_name}.lock"
        )
        with FileLock(fixture_collector_count_file_lock):
            if fixture_collector_count_file.exists():
                with open(fixture_collector_count_file, "r") as f:
                    fixture_collector_count = int(f.read())
            else:
                fixture_collector_count = 0
            fixture_collector_count += 1
            with open(fixture_collector_count_file, "w") as f:
                f.write(str(fixture_collector_count))

    fixture_collector = FixtureCollector(
        output_dir=output_dir,
        flat_output=request.config.getoption("flat_output"),
        single_fixture_per_file=request.config.getoption("single_fixture_per_file"),
        filler_path=filler_path,
        base_dump_dir=base_dump_dir,
    )
    yield fixture_collector
    fixture_collector.dump_fixtures()
    if do_fixture_verification:
        fixture_collector.verify_fixture_files(evm_fixture_verification)

    fixture_collector_count = 0
    if session_temp_folder is not None:
        with FileLock(fixture_collector_count_file_lock):
            with open(fixture_collector_count_file, "r") as f:
                fixture_collector_count = int(f.read())
            fixture_collector_count -= 1
            with open(fixture_collector_count_file, "w") as f:
                f.write(str(fixture_collector_count))
    if generate_index and fixture_collector_count == 0:
        generate_fixtures_index(
            output_dir, quiet_mode=True, force_flag=False, disable_infer_format=False
        )


@pytest.fixture(autouse=True, scope="session")
def filler_path(request: pytest.FixtureRequest) -> Path:
    """Return directory containing the tests to execute."""
    return request.config.getoption("filler_path")


def node_to_test_info(node: pytest.Item) -> TestInfo:
    """Return test info of the current node item."""
    return TestInfo(
        name=node.name,
        id=node.nodeid,
        original_name=node.originalname,  # type: ignore
        path=Path(node.path),
    )


@pytest.fixture(scope="function")
def fixture_source_url(request: pytest.FixtureRequest) -> str:
    """Return URL to the fixture source."""
    function_line_number = request.function.__code__.co_firstlineno
    module_relative_path = os.path.relpath(request.module.__file__)
    hash_or_tag = get_current_commit_hash_or_tag()
    github_url = generate_github_url(
        module_relative_path, branch_or_commit_or_tag=hash_or_tag, line_number=function_line_number
    )
    return github_url


def base_test_parametrizer(cls: Type[BaseTest]):
    """
    Generate pytest.fixture for a given BaseTest subclass.

    Implementation detail: All spec fixtures must be scoped on test function level to avoid
    leakage between tests.
    """

    @pytest.fixture(
        scope="function",
        name=cls.pytest_parameter_name(),
    )
    def base_test_parametrizer_func(
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        reference_spec: ReferenceSpec,
        eips: List[int],
        pre: Alloc,
        output_dir: Path,
        dump_dir_parameter_level: Path | None,
        fixture_collector: FixtureCollector,
        test_case_description: str,
        fixture_source_url: str,
    ):
        """
        Fixture used to instantiate an auto-fillable BaseTest object from within
        a test function.

        Every test that defines a test filler must explicitly specify its parameter name
        (see `pytest_parameter_name` in each implementation of BaseTest) in its function
        arguments.

        When parametrize, indirect must be used along with the fixture format as value.
        """
        fixture_format = request.param
        assert issubclass(fixture_format, BaseFixture)

        class BaseTestWrapper(cls):  # type: ignore
            def __init__(self, *args, **kwargs):
                kwargs["t8n_dump_dir"] = dump_dir_parameter_level
                if "pre" not in kwargs:
                    kwargs["pre"] = pre
                super(BaseTestWrapper, self).__init__(*args, **kwargs)
                fixture = self.generate(
                    request=request,
                    t8n=t8n,
                    fork=fork,
                    fixture_format=fixture_format,
                    eips=eips,
                )
                fixture.fill_info(
                    t8n.version(),
                    test_case_description,
                    fixture_source_url=fixture_source_url,
                    ref_spec=reference_spec,
                )

                fixture_path = fixture_collector.add_fixture(
                    node_to_test_info(request.node),
                    fixture,
                )

                # NOTE: Use str for compatibility with pytest-dist
                request.node.config.fixture_path_absolute = str(fixture_path.absolute())
                request.node.config.fixture_path_relative = str(
                    fixture_path.relative_to(output_dir)
                )
                request.node.config.fixture_format = fixture_format.fixture_format_name

        return BaseTestWrapper

    return base_test_parametrizer_func


# Dynamically generate a pytest fixture for each test spec type.
for cls in SPEC_TYPES:
    # Fixture needs to be defined in the global scope so pytest can detect it.
    globals()[cls.pytest_parameter_name()] = base_test_parametrizer(cls)


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    Pytest hook used to dynamically generate test cases for each fixture format a given
    test spec supports.
    """
    for test_type in SPEC_TYPES:
        if test_type.pytest_parameter_name() in metafunc.fixturenames:
            metafunc.parametrize(
                [test_type.pytest_parameter_name()],
                [
                    pytest.param(
                        fixture_format,
                        id=fixture_format.fixture_format_name.lower(),
                        marks=[getattr(pytest.mark, fixture_format.fixture_format_name.lower())],
                    )
                    for fixture_format in test_type.supported_fixture_formats
                ],
                scope="function",
                indirect=True,
            )


def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]):
    """
    Remove pre-Paris tests parametrized to generate hive type fixtures; these
    can't be used in the Hive Pyspec Simulator.

    This can't be handled in this plugins pytest_generate_tests() as the fork
    parametrization occurs in the forks plugin.
    """
    for item in items[:]:  # use a copy of the list, as we'll be modifying it
        if isinstance(item, EIPSpecTestItem):
            continue
        params: Dict[str, Any] = item.callspec.params  # type: ignore
        if "fork" not in params or params["fork"] is None:
            items.remove(item)
            continue
        fork: Fork = params["fork"]
        for spec_name in [spec_type.pytest_parameter_name() for spec_type in SPEC_TYPES]:
            if spec_name in params and not params[spec_name].supports_fork(fork):
                items.remove(item)
                break
        for marker in item.iter_markers():
            if marker.name == "fill":
                for mark in marker.args:
                    item.add_marker(mark)
        if "yul" in item.fixturenames:  # type: ignore
            item.add_marker(pytest.mark.yul_test)
