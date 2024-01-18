"""
Top-level pytest configuration file providing:
- Command-line options,
- Test-fixtures that can be used by all test cases,
and that modifies pytest hooks in order to fill test specs for all tests and
writes the generated fixtures to file.
"""
import warnings
from pathlib import Path
from typing import Generator, List, Optional, Type

import pytest

from ethereum_test_forks import Fork, Paris, get_development_forks
from ethereum_test_tools import SPEC_TYPES, BaseTest, FixtureCollector, TestInfo, Yul
from evm_transition_tool import FixtureFormats, TransitionTool
from pytest_plugins.spec_version_checker.spec_version_checker import EIPSpecTestItem


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    evm_group = parser.getgroup("evm", "Arguments defining evm executable behavior")
    evm_group.addoption(
        "--evm-bin",
        action="store",
        dest="evm_bin",
        type=Path,
        default=None,
        help=(
            "Path to an evm executable that provides `t8n`. Default: First 'evm' entry in PATH."
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

    solc_group = parser.getgroup("solc", "Arguments defining the solc executable")
    solc_group.addoption(
        "--solc-bin",
        action="store",
        dest="solc_bin",
        default=None,
        help=(
            "Path to a solc executable (for Yul source compilation). "
            "Default: First 'solc' entry in PATH."
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
        default="./fixtures/",
        help="Directory to store the generated test fixtures. Can be deleted.",
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

    debug_group = parser.getgroup("debug", "Arguments defining debug behavior")
    debug_group.addoption(
        "--evm-dump-dir",
        "--t8n-dump-dir",
        action="store",
        dest="base_dump_dir",
        default="",
        help="Path to dump the transition tool debug output.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Register the plugin's custom markers and process command-line options.

    Custom marker registration:
    https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers
    """
    for fixture_format in FixtureFormats:
        config.addinivalue_line(
            "markers",
            (
                f"{fixture_format.name.lower()}: "
                f"{FixtureFormats.get_format_description(fixture_format)}"
            ),
        )

    config.addinivalue_line(
        "markers",
        "yul_test: a test case that compiles Yul code.",
    )
    config.addinivalue_line(
        "markers",
        "compile_yul_with(fork): Always compile Yul source using the corresponding evm version.",
    )
    if config.option.collectonly:
        return
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


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """Add lines to pytest's console output header"""
    if config.option.collectonly:
        return
    binary_path = config.getoption("evm_bin")
    t8n = TransitionTool.from_binary_path(binary_path=binary_path)
    solc_version_string = Yul("", binary=config.getoption("solc_bin")).version()
    return [f"{t8n.version()}, solc version {solc_version_string}"]


@pytest.fixture(autouse=True, scope="session")
def evm_bin(request) -> Path:
    """
    Returns the configured evm tool binary path used to run t8n.
    """
    return request.config.getoption("evm_bin")


@pytest.fixture(autouse=True, scope="session")
def verify_fixtures_bin(request) -> Path:
    """
    Returns the configured evm tool binary path used to run statetest or
    blocktest.
    """
    return request.config.getoption("verify_fixtures_bin")


@pytest.fixture(autouse=True, scope="session")
def solc_bin(request):
    """
    Returns the configured solc binary path.
    """
    return request.config.getoption("solc_bin")


@pytest.fixture(autouse=True, scope="session")
def t8n(request, evm_bin: Path) -> Generator[TransitionTool, None, None]:
    """
    Returns the configured transition tool.
    """
    t8n = TransitionTool.from_binary_path(
        binary_path=evm_bin, trace=request.config.getoption("evm_collect_traces")
    )
    yield t8n
    t8n.shutdown()


@pytest.fixture(scope="session")
def do_fixture_verification(request, t8n) -> bool:
    """
    Returns True if evm statetest or evm blocktest should be ran on the
    generated fixture JSON files.
    """
    do_fixture_verification = False
    if request.config.getoption("verify_fixtures_bin"):
        do_fixture_verification = True
    if request.config.getoption("verify_fixtures"):
        do_fixture_verification = True
    return do_fixture_verification


@pytest.fixture(autouse=True, scope="session")
def evm_fixture_verification(
    request, do_fixture_verification: bool, evm_bin: Path, verify_fixtures_bin: Path
) -> Optional[Generator[TransitionTool, None, None]]:
    """
    Returns the configured evm binary for executing statetest and blocktest
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
def base_dump_dir(request) -> Optional[Path]:
    """
    The base directory to dump the evm debug output.
    """
    base_dump_dir_str = request.config.getoption("base_dump_dir")
    if base_dump_dir_str:
        return Path(base_dump_dir_str)
    return None


@pytest.fixture(scope="function")
def dump_dir_parameter_level(
    request, base_dump_dir: Optional[Path], filler_path: Path
) -> Optional[Path]:
    """
    The directory to dump evm transition tool debug output on a test parameter
    level.

    Example with --evm-dump-dir=/tmp/evm:
    -> /tmp/evm/shanghai__eip3855_push0__test_push0__test_push0_key_sstore/fork_shanghai/
    """
    return node_to_test_info(request.node).get_dump_dir_path(
        base_dump_dir,
        filler_path,
        level="test_parameter",
    )


def get_fixture_collection_scope(fixture_name, config):
    """
    Return the appropriate scope to write fixture JSON files.

    See: https://docs.pytest.org/en/stable/how-to/fixtures.html#dynamic-scope
    """
    if config.getoption("single_fixture_per_file"):
        return "function"
    return "module"


@pytest.fixture(scope=get_fixture_collection_scope)
def fixture_collector(
    request,
    do_fixture_verification: bool,
    evm_fixture_verification: TransitionTool,
    filler_path: Path,
    base_dump_dir: Optional[Path],
):
    """
    Returns the configured fixture collector instance used for all tests
    in one test module.
    """
    fixture_collector = FixtureCollector(
        output_dir=request.config.getoption("output"),
        flat_output=request.config.getoption("flat_output"),
        single_fixture_per_file=request.config.getoption("single_fixture_per_file"),
        filler_path=filler_path,
        base_dump_dir=base_dump_dir,
    )
    yield fixture_collector
    fixture_collector.dump_fixtures()
    if do_fixture_verification:
        fixture_collector.verify_fixture_files(evm_fixture_verification)


@pytest.fixture(autouse=True, scope="session")
def filler_path(request) -> Path:
    """
    Returns the directory containing the tests to execute.
    """
    return request.config.getoption("filler_path")


@pytest.fixture(autouse=True)
def eips():
    """
    A fixture specifying that, by default, no EIPs should be activated for
    tests.

    This fixture (function) may be redefined in test filler modules in order
    to overwrite this default and return a list of integers specifying which
    EIPs should be activated for the tests in scope.
    """
    return []


@pytest.fixture
def yul(fork: Fork, request):
    """
    A fixture that allows contract code to be defined with Yul code.

    This fixture defines a class that wraps the ::ethereum_test_tools.Yul
    class so that upon instantiation within the test case, it provides the
    test case's current fork parameter. The forks is then available for use
    in solc's arguments for the Yul code compilation.

    Test cases can override the default value by specifying a fixed version
    with the @pytest.mark.compile_yul_with(FORK) marker.
    """
    marker = request.node.get_closest_marker("compile_yul_with")
    if marker:
        if not marker.args[0]:
            pytest.fail(
                f"{request.node.name}: Expected one argument in 'compile_yul_with' marker."
            )
        fork = request.config.fork_map[marker.args[0]]

    class YulWrapper(Yul):
        def __init__(self, *args, **kwargs):
            super(YulWrapper, self).__init__(*args, **kwargs, fork=fork)

    return YulWrapper


SPEC_TYPES_PARAMETERS: List[str] = [s.pytest_parameter_name() for s in SPEC_TYPES]


def node_to_test_info(node) -> TestInfo:
    """
    Returns the test info of the current node item.
    """
    return TestInfo(
        name=node.name,
        id=node.nodeid,
        original_name=node.originalname,
        path=Path(node.path),
    )


def base_test_parametrizer(cls: Type[BaseTest]):
    """
    Generates a pytest.fixture for a given BaseTest subclass.

    Implementation detail: All spec fixtures must be scoped on test function level to avoid
    leakage between tests.
    """

    @pytest.fixture(
        scope="function",
        name=cls.pytest_parameter_name(),
    )
    def base_test_parametrizer_func(
        request,
        t8n,
        fork,
        reference_spec,
        eips,
        dump_dir_parameter_level,
        fixture_collector,
    ):
        """
        Fixture used to instantiate an auto-fillable BaseTest object from within
        a test function.

        Every test that defines a test filler must explicitly specify its parameter name
        (see `pytest_parameter_name` in each implementation of BaseTest) in its function
        arguments.

        When parametrizing, indirect must be used along with the fixture format as value.
        """
        fixture_format = request.param
        assert isinstance(fixture_format, FixtureFormats)

        class BaseTestWrapper(cls):
            def __init__(self, *args, **kwargs):
                kwargs["fixture_format"] = fixture_format
                kwargs["t8n_dump_dir"] = dump_dir_parameter_level
                super(BaseTestWrapper, self).__init__(*args, **kwargs)
                fixture = self.generate(
                    t8n,
                    fork,
                    eips=eips,
                )
                fixture.fill_info(t8n, reference_spec)

                fixture_collector.add_fixture(
                    node_to_test_info(request.node),
                    fixture,
                )

        return BaseTestWrapper

    return base_test_parametrizer_func


# Dynamically generate a pytest fixture for each test spec type.
for cls in SPEC_TYPES:
    # Fixture needs to be defined in the global scope so pytest can detect it.
    globals()[cls.pytest_parameter_name()] = base_test_parametrizer(cls)


def pytest_generate_tests(metafunc):
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
                        id=fixture_format.name.lower(),
                        marks=[getattr(pytest.mark, fixture_format.name.lower())],
                    )
                    for fixture_format in test_type.fixture_formats()
                ],
                scope="function",
                indirect=True,
            )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """
    Remove pre-Paris tests parametrized to generate hive type fixtures; these
    can't be used in the Hive Pyspec Simulator.

    This can't be handled in this plugins pytest_generate_tests() as the fork
    parametrization occurs in the forks plugin.
    """
    for item in items[:]:  # use a copy of the list, as we'll be modifying it
        if isinstance(item, EIPSpecTestItem):
            continue
        if item.callspec.params["fork"] < Paris:
            # Even though the `state_test` test spec does not produce a hive STATE_TEST, it does
            # produce a BLOCKCHAIN_TEST_HIVE, so we need to remove it here.
            # TODO: Ideally, the logic could be contained in the `FixtureFormat` class, we create
            # a `fork_supported` method that returns True if the fork is supported.
            if ("state_test" in item.callspec.params) and item.callspec.params[
                "state_test"
            ].name.endswith("HIVE"):
                items.remove(item)
            if ("blockchain_test" in item.callspec.params) and item.callspec.params[
                "blockchain_test"
            ].name.endswith("HIVE"):
                items.remove(item)


def pytest_runtest_setup(item):
    """
    A pytest hook called before setting up each test item.
    """
    if "yul" in item.fixturenames:
        marker = pytest.mark.yul_test()
        item.add_marker(marker)
        if any([fork.name() in item.name for fork in get_development_forks()]):
            if item.config.getoption("verbose") >= 1:
                warnings.warn("Compiling Yul for with Shanghai, not the target fork.")
            item.add_marker(pytest.mark.compile_yul_with("Shanghai"))


def pytest_make_parametrize_id(config, val, argname):
    """
    Pytest hook called when generating test ids. We use this to generate
    more readable test ids for the generated tests.
    """
    return f"{argname}_{val}"


def pytest_runtest_call(item):
    """
    Pytest hook called in the context of test execution.
    """
    if isinstance(item, EIPSpecTestItem):
        return

    class InvalidFiller(Exception):
        def __init__(self, message):
            super().__init__(message)

    if "state_test" in item.fixturenames and "blockchain_test" in item.fixturenames:
        raise InvalidFiller(
            "A filler should only implement either a state test or " "a blockchain test; not both."
        )

    # Check that the test defines either test type as parameter.
    if not any([i for i in item.funcargs if i in SPEC_TYPES_PARAMETERS]):
        pytest.fail(
            "Test must define either one of the following parameters to "
            + "properly generate a test: "
            + ", ".join(SPEC_TYPES_PARAMETERS)
        )
