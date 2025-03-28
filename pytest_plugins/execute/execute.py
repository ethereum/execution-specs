"""Test execution plugin for pytest, to run Ethereum tests using in live networks."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Type

import pytest
from pytest_metadata.plugin import metadata_key  # type: ignore

from ethereum_test_execution import BaseExecute
from ethereum_test_forks import Fork
from ethereum_test_rpc import EthRPC
from ethereum_test_tools import SPEC_TYPES, BaseTest
from ethereum_test_types import TransactionDefaults
from pytest_plugins.spec_version_checker.spec_version_checker import EIPSpecTestItem

from ..shared.helpers import get_spec_format_for_item, labeled_format_parameter_set
from .pre_alloc import Alloc


def default_html_report_file_path() -> str:
    """
    File (default) to store the generated HTML test report. Defined as a
    function to allow for easier testing.
    """
    return "./execution_results/report_execute.html"


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    execute_group = parser.getgroup("execute", "Arguments defining test execution behavior")
    execute_group.addoption(
        "--default-gas-price",
        action="store",
        dest="default_gas_price",
        type=int,
        default=10**9,
        help=("Default gas price used for transactions, unless overridden by the test."),
    )
    execute_group.addoption(
        "--default-max-fee-per-gas",
        action="store",
        dest="default_max_fee_per_gas",
        type=int,
        default=10**9,
        help=("Default max fee per gas used for transactions, unless overridden by the test."),
    )
    execute_group.addoption(
        "--default-max-priority-fee-per-gas",
        action="store",
        dest="default_max_priority_fee_per_gas",
        type=int,
        default=10**9,
        help=(
            "Default max priority fee per gas used for transactions, "
            "unless overridden by the test."
        ),
    )

    report_group = parser.getgroup("tests", "Arguments defining html report behavior")
    report_group.addoption(
        "--no-html",
        action="store_true",
        dest="disable_html",
        default=False,
        help=(
            "Don't generate an HTML test report. "
            "The --html flag can be used to specify a different path."
        ),
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
    if config.getoption("disable_html") and config.getoption("htmlpath") is None:
        # generate an html report by default, unless explicitly disabled
        config.option.htmlpath = Path(default_html_report_file_path())

    command_line_args = "fill " + " ".join(config.invocation_params.args)
    config.stash[metadata_key]["Command-line args"] = f"<code>{command_line_args}</code>"

    selected_fork_set = config.selected_fork_set

    # remove the transition forks from the selected forks
    for fork in set(selected_fork_set):
        if hasattr(fork, "transitions_to"):
            selected_fork_set.remove(fork)

    if len(selected_fork_set) != 1:
        pytest.exit(
            f"""
            Expected exactly one fork to be specified, got {len(selected_fork_set)}
            ({selected_fork_set}).
            Make sure to specify exactly one fork using the --fork command line argument.
            """,
            returncode=pytest.ExitCode.USAGE_ERROR,
        )


def pytest_metadata(metadata):
    """Add or remove metadata to/from the pytest report."""
    metadata.pop("JAVA_HOME", None)


def pytest_html_results_table_header(cells):
    """Customize the table headers of the HTML report table."""
    cells.insert(3, '<th class="sortable" data-column-type="sender">Sender</th>')
    cells.insert(4, '<th class="sortable" data-column-type="fundedAccounts">Funded Accounts</th>')
    cells.insert(
        5, '<th class="sortable" data-column-type="fundedAccounts">Deployed Contracts</th>'
    )
    del cells[-1]  # Remove the "Links" column


def pytest_html_results_table_row(report, cells):
    """Customize the table rows of the HTML report table."""
    if hasattr(report, "user_properties"):
        user_props = dict(report.user_properties)
        if "sender_address" in user_props and user_props["sender_address"] is not None:
            sender_address = user_props["sender_address"]
            cells.insert(3, f"<td>{sender_address}</td>")
        else:
            cells.insert(3, "<td>Not available</td>")

        if "funded_accounts" in user_props and user_props["funded_accounts"] is not None:
            funded_accounts = user_props["funded_accounts"]
            cells.insert(4, f"<td>{funded_accounts}</td>")
        else:
            cells.insert(4, "<td>Not available</td>")

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
        for property_name in ["sender_address", "funded_accounts"]:
            if hasattr(item.config, property_name):
                report.user_properties.append((property_name, getattr(item.config, property_name)))


def pytest_html_report_title(report):
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Execute Test Report"


@pytest.fixture(scope="session")
def default_gas_price(request) -> int:
    """Return default gas price used for transactions."""
    gas_price = request.config.getoption("default_gas_price")
    assert gas_price > 0, "Gas price must be greater than 0"
    return gas_price


@pytest.fixture(scope="session")
def default_max_fee_per_gas(request) -> int:
    """Return default max fee per gas used for transactions."""
    return request.config.getoption("default_max_fee_per_gas")


@pytest.fixture(scope="session")
def default_max_priority_fee_per_gas(request) -> int:
    """Return default max priority fee per gas used for transactions."""
    return request.config.getoption("default_max_priority_fee_per_gas")


@pytest.fixture(autouse=True, scope="session")
def modify_transaction_defaults(
    default_gas_price: int, default_max_fee_per_gas: int, default_max_priority_fee_per_gas: int
):
    """Modify transaction defaults to values better suited for live networks."""
    TransactionDefaults.gas_price = default_gas_price
    TransactionDefaults.max_fee_per_gas = default_max_fee_per_gas
    TransactionDefaults.max_priority_fee_per_gas = default_max_priority_fee_per_gas


@dataclass(kw_only=True)
class Collector:
    """A class that collects transactions and post-allocations for every test case."""

    eth_rpc: EthRPC
    collected_tests: Dict[str, BaseExecute] = field(default_factory=dict)

    def collect(self, test_name: str, execute_format: BaseExecute):
        """Collect transactions and post-allocations for the test case."""
        self.collected_tests[test_name] = execute_format


@pytest.fixture(scope="session")
def collector(
    request,
    eth_rpc: EthRPC,
) -> Generator[Collector, None, None]:
    """
    Return configured fixture collector instance used for all tests
    in one test module.
    """
    collector = Collector(eth_rpc=eth_rpc)
    yield collector


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
        request: Any,
        fork: Fork,
        pre: Alloc,
        eips: List[int],
        eth_rpc: EthRPC,
        collector: Collector,
    ):
        """
        Fixture used to instantiate an auto-fillable BaseTest object from within
        a test function.

        Every test that defines a test filler must explicitly specify its parameter name
        (see `pytest_parameter_name` in each implementation of BaseTest) in its function
        arguments.

        When parametrize, indirect must be used along with the fixture format as value.
        """
        execute_format = request.param
        assert execute_format in BaseExecute.formats.values()

        class BaseTestWrapper(cls):  # type: ignore
            def __init__(self, *args, **kwargs):
                kwargs["t8n_dump_dir"] = None
                if "pre" not in kwargs:
                    kwargs["pre"] = pre
                elif kwargs["pre"] != pre:
                    raise ValueError("The pre-alloc object was modified by the test.")

                request.node.config.sender_address = str(pre._sender)

                super(BaseTestWrapper, self).__init__(*args, **kwargs)

                # wait for pre-requisite transactions to be included in blocks
                pre.wait_for_transactions()
                for deployed_contract, expected_code in pre._deployed_contracts:
                    actual_code = eth_rpc.get_code(deployed_contract)
                    if actual_code != expected_code:
                        raise Exception(
                            f"Deployed test contract didn't match expected code at address "
                            f"{deployed_contract} (not enough gas_limit?).\n"
                            f"Expected: {expected_code}\n"
                            f"Actual: {actual_code}"
                        )
                request.node.config.funded_accounts = ", ".join(
                    [str(eoa) for eoa in pre._funded_eoa]
                )

                execute = self.execute(fork=fork, execute_format=execute_format, eips=eips)
                execute.execute(eth_rpc)
                collector.collect(request.node.nodeid, execute)

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
                    labeled_format_parameter_set(format_with_or_without_label)
                    for format_with_or_without_label in test_type.supported_execute_formats
                ],
                scope="function",
                indirect=True,
            )


def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]):
    """Remove transition tests and add the appropriate execute markers to the test."""
    for item in items[:]:  # use a copy of the list, as we'll be modifying it
        if isinstance(item, EIPSpecTestItem):
            continue
        params: Dict[str, Any] = item.callspec.params  # type: ignore
        if "fork" not in params or params["fork"] is None:
            items.remove(item)
            continue
        fork: Fork = params["fork"]
        spec_type, execute_format = get_spec_format_for_item(params)
        assert issubclass(execute_format, BaseExecute)
        markers = list(item.iter_markers())
        if spec_type.discard_execute_format_by_marks(execute_format, fork, markers):
            items.remove(item)
            continue
        for marker in markers:
            if marker.name == "execute":
                for mark in marker.args:
                    item.add_marker(mark)
            elif marker.name == "valid_at_transition_to":
                items.remove(item)
        if "yul" in item.fixturenames:  # type: ignore
            item.add_marker(pytest.mark.yul_test)
