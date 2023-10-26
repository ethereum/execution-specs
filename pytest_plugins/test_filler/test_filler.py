"""
Top-level pytest configuration file providing:
- Command-line options,
- Test-fixtures that can be used by all test cases,
and that modifies pytest hooks in order to fill test specs for all tests and
writes the generated fixtures to file.
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Literal, Optional, Tuple, Type, Union

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    BaseTest,
    BaseTestConfig,
    BlockchainTest,
    BlockchainTestFiller,
    Fixture,
    HiveFixture,
    StateTest,
    StateTestFiller,
    Yul,
    fill_test,
)
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
    test_group.addoption(
        "--enable-hive",
        action="store_true",
        dest="enable_hive",
        default=False,
        help="Output test fixtures with the hive-specific properties.",
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
    config.addinivalue_line(
        "markers",
        "state_test: a test case that implement a single state transition test.",
    )
    config.addinivalue_line(
        "markers",
        "blockchain_test: a test case that implements a block transition test.",
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
    if do_fixture_verification and request.config.getoption("enable_hive"):
        pytest.exit(
            "Hive fixtures can not be verify using geth's evm tool: "
            "Remove --enable-hive to verify test fixtures.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
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


@pytest.fixture(autouse=True, scope="session")
def base_test_config(request) -> BaseTestConfig:
    """
    Returns the base test configuration that all tests must use.
    """
    config = BaseTestConfig()
    config.enable_hive = request.config.getoption("enable_hive")
    return config


def strip_test_prefix(name: str) -> str:
    """
    Removes the test prefix from a test case name.
    """
    TEST_PREFIX = "test_"
    if name.startswith(TEST_PREFIX):
        return name[len(TEST_PREFIX) :]
    return name


def convert_test_id_to_test_name_and_parameters(name: str) -> Tuple[str, str]:
    """
    Converts a test name to a tuple containing the test name and test parameters.

    Example:
    test_push0_key_sstore[fork=Shanghai] -> test_push0_key_sstore, fork_Shanghai
    """
    test_name, parameters = name.split("[")
    return test_name, re.sub(r"[\[=\-]", "_", parameters).replace("]", "")


def get_module_relative_output_dir(test_module: Path, filler_path: Path) -> Path:
    """
    Return a directory name for the provided test_module (relative to the
    base ./tests directory) that can be used for output (within the
    configured fixtures output path or the base_dump_dir directory).

    Example:
    tests/shanghai/eip3855_push0/test_push0.py -> shanghai/eip3855_push0/test_push0
    """
    basename = test_module.with_suffix("").absolute()
    basename_relative = basename.relative_to(filler_path.absolute())
    module_path = basename_relative.parent / basename_relative.stem
    return module_path


def get_dump_dir_path(
    base_dump_dir: Path,
    filler_path: Path,
    node: pytest.Item,
    level: Literal["test_module", "test_function", "test_parameter"] = "test_parameter",
) -> Optional[Path]:
    """
    The path to dump the debug output as defined by the level to dump at.
    """
    if not base_dump_dir:
        return None
    test_module_relative_dir = get_module_relative_output_dir(Path(node.path), filler_path)
    if level == "test_module":
        return Path(base_dump_dir) / Path(str(test_module_relative_dir).replace(os.sep, "__"))
    test_name, test_parameter_string = convert_test_id_to_test_name_and_parameters(node.name)
    flat_path = f"{str(test_module_relative_dir).replace(os.sep, '__')}__{test_name}"
    if level == "test_function":
        return Path(base_dump_dir) / flat_path
    elif level == "test_parameter":
        return Path(base_dump_dir) / flat_path / test_parameter_string
    raise Exception("Unexpected level.")


@pytest.fixture(scope="session")
def base_dump_dir(request) -> Path:
    """
    The base directory to dump the evm debug output.
    """
    return request.config.getoption("base_dump_dir")


@pytest.fixture(scope="function")
def dump_dir_parameter_level(request, base_dump_dir: Path, filler_path: Path) -> Optional[Path]:
    """
    The directory to dump evm transition tool debug output on a test parameter
    level.

    Example with --evm-dump-dir=/tmp/evm:
    -> /tmp/evm/shanghai__eip3855_push0__test_push0__test_push0_key_sstore/fork_shanghai/
    """
    return get_dump_dir_path(base_dump_dir, filler_path, request.node, level="test_parameter")


def get_fixture_collection_scope(fixture_name, config):
    """
    Return the appropriate scope to write fixture JSON files.

    See: https://docs.pytest.org/en/stable/how-to/fixtures.html#dynamic-scope
    """
    if config.getoption("single_fixture_per_file"):
        return "function"
    return "module"


class FixtureCollector:
    """
    Collects all fixtures generated by the test cases.
    """

    all_fixtures: Dict[Path, List[Tuple[str, Any]]]
    output_dir: str
    flat_output: bool
    json_path_to_fixture_type: Dict[Path, FixtureFormats]
    json_path_to_test_item: Dict[Path, pytest.Item]

    def __init__(
        self,
        output_dir: str,
        flat_output: bool,
    ) -> None:
        self.all_fixtures = {}
        self.output_dir = output_dir
        self.flat_output = flat_output
        self.json_path_to_fixture_type = {}
        self.json_path_to_test_item = {}

    def add_fixture(
        self, item, fixture: Optional[Union[Fixture, HiveFixture]], fixture_format: FixtureFormats
    ) -> None:
        """
        Adds a fixture to the list of fixtures of a given test case.
        """
        # TODO: remove this logic. if hive enabled set --from to Merge
        if fixture is None:
            return

        def get_single_test_name(item):
            test_name, test_parameters = convert_test_id_to_test_name_and_parameters(item.name)
            return f"{test_name}__{test_parameters}"

        def get_fixture_basename_for_flat_output(self, item):
            if item.config.getoption("single_fixture_per_file"):
                return Path(strip_test_prefix(get_single_test_name(item)))
            return Path(strip_test_prefix(item.originalname))

        def get_fixture_basename_for_nested_output(self, item):
            relative_fixture_output_dir = Path(item.path).parent / strip_test_prefix(
                Path(item.path).stem
            )
            module_relative_output_dir = get_module_relative_output_dir(
                relative_fixture_output_dir, item.config.getoption("filler_path")
            )

            if item.config.getoption("single_fixture_per_file"):
                return module_relative_output_dir / strip_test_prefix(get_single_test_name(item))
            return module_relative_output_dir / strip_test_prefix(item.originalname)

        fixture_basename: Path
        if self.flat_output:
            fixture_basename = get_fixture_basename_for_flat_output(self, item)
        else:
            fixture_basename = get_fixture_basename_for_nested_output(self, item)

        fixture_path = self.output_dir / fixture_basename.with_suffix(".json")
        if fixture_path not in self.all_fixtures:  # relevant when we group by test function
            self.all_fixtures[fixture_path] = []
            self.json_path_to_fixture_type[fixture_path] = fixture_format
            self.json_path_to_test_item[fixture_path] = item

        m = re.match(r".*?\[(.*)\]", item.name)
        if not m:
            raise Exception("Could not parse test name: " + item.name)
        name = m.group(1)
        if fixture.name:
            name += "-" + fixture.name
        jsonFixture = fixture.to_json()
        self.all_fixtures[fixture_path].append((name, jsonFixture))

    def dump_fixtures(self) -> None:
        """
        Dumps all collected fixtures to their respective files.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        for fixture_path, fixtures in self.all_fixtures.items():
            output_json = {}
            for index, fixture_props in enumerate(fixtures):
                name, fixture = fixture_props
                name = str(index).zfill(3) + "-" + name
                output_json[name] = fixture
            if not self.flat_output:
                os.makedirs(fixture_path.parent, exist_ok=True)
            with open(fixture_path, "w") as f:
                json.dump(output_json, f, indent=4)

    def verify_fixture_files(self, evm_fixture_verification: TransitionTool) -> None:
        """
        Runs `evm [state|block]test` on each fixture.
        """
        for fixture_path, fixture_format in self.json_path_to_fixture_type.items():
            item = self.json_path_to_test_item[fixture_path]
            verify_fixtures_dump_dir = self._get_verify_fixtures_dump_dir(item)
            evm_fixture_verification.verify_fixture(
                fixture_format, fixture_path, verify_fixtures_dump_dir
            )

    def _get_verify_fixtures_dump_dir(
        self,
        item: pytest.Item,
    ):
        """
        The directory to dump the current test function's fixture.json and fixture
        verification debug output.
        """
        base_dump_dir = item.config.getoption("base_dump_dir")
        if not base_dump_dir:
            return None
        filler_path = item.config.getoption("filler_path")
        if item.config.getoption("single_fixture_per_file"):
            return get_dump_dir_path(base_dump_dir, filler_path, item, level="test_parameter")
        else:
            return get_dump_dir_path(base_dump_dir, filler_path, item, level="test_function")


@pytest.fixture(scope=get_fixture_collection_scope)
def fixture_collector(
    request,
    do_fixture_verification: bool,
    evm_fixture_verification: TransitionTool,
):
    """
    Returns the configured fixture collector instance used for all tests
    in one test module.
    """
    fixture_collector = FixtureCollector(
        output_dir=request.config.getoption("output"),
        flat_output=request.config.getoption("flat_output"),
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


SPEC_TYPES: List[Type[BaseTest]] = [StateTest, BlockchainTest]
SPEC_TYPES_PARAMETERS: List[str] = [s.pytest_parameter_name() for s in SPEC_TYPES]


@pytest.fixture(scope="function")
def fixture_format(request) -> FixtureFormats:
    """
    Returns the test format of the current test case.
    """
    enable_hive = request.config.getoption("enable_hive")
    has_blockchain_test_format = set(["state_test", "blockchain_test"]) & set(request.fixturenames)
    if has_blockchain_test_format and enable_hive:
        return FixtureFormats.BLOCKCHAIN_TEST_HIVE
    elif has_blockchain_test_format and not enable_hive:
        return FixtureFormats.BLOCKCHAIN_TEST
    raise Exception("Unknown fixture format.")


@pytest.fixture(scope="function")
def state_test(
    request,
    t8n,
    fork,
    reference_spec,
    eips,
    dump_dir_parameter_level,
    fixture_collector,
    fixture_format,
    base_test_config,
) -> StateTestFiller:
    """
    Fixture used to instantiate an auto-fillable StateTest object from within
    a test function.

    Every test that defines a StateTest filler must explicitly specify this
    fixture in its function arguments.

    Implementation detail: It must be scoped on test function level to avoid
    leakage between tests.
    """

    class StateTestWrapper(StateTest):
        def __init__(self, *args, **kwargs):
            kwargs["base_test_config"] = base_test_config
            kwargs["t8n_dump_dir"] = dump_dir_parameter_level
            super(StateTestWrapper, self).__init__(*args, **kwargs)
            fixture_collector.add_fixture(
                request.node,
                fill_test(
                    t8n,
                    self,
                    fork,
                    reference_spec,
                    eips=eips,
                ),
                fixture_format,
            )

    return StateTestWrapper


@pytest.fixture(scope="function")
def blockchain_test(
    request,
    t8n,
    fork,
    reference_spec,
    eips,
    dump_dir_parameter_level,
    fixture_collector,
    fixture_format,
    base_test_config,
) -> BlockchainTestFiller:
    """
    Fixture used to define an auto-fillable BlockchainTest analogous to the
    state_test fixture for StateTests.
    See the state_test fixture docstring for details.
    """

    class BlockchainTestWrapper(BlockchainTest):
        def __init__(self, *args, **kwargs):
            kwargs["base_test_config"] = base_test_config
            kwargs["t8n_dump_dir"] = dump_dir_parameter_level
            super(BlockchainTestWrapper, self).__init__(*args, **kwargs)
            fixture_collector.add_fixture(
                request.node,
                fill_test(
                    t8n,
                    self,
                    fork,
                    reference_spec,
                    eips=eips,
                ),
                fixture_format,
            )

    return BlockchainTestWrapper


def pytest_collection_modifyitems(items, config):
    """
    A pytest hook called during collection, after all items have been
    collected.

    Here we dynamically apply "state_test" or "blockchain_test" markers
    to a test if the test function uses the corresponding fixture.
    """
    for item in items:
        if isinstance(item, EIPSpecTestItem):
            continue
        if "state_test" in item.fixturenames:
            marker = pytest.mark.state_test()
            item.add_marker(marker)
        elif "blockchain_test" in item.fixturenames:
            marker = pytest.mark.blockchain_test()
            item.add_marker(marker)
        if "yul" in item.fixturenames:
            marker = pytest.mark.yul_test()
            item.add_marker(marker)


def pytest_make_parametrize_id(config, val, argname):
    """
    Pytest hook called when generating test ids. We use this to generate
    more readable test ids for the generated tests.
    """
    return f"{argname}={val}"


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
