"""
Test execution plugin for pytest, to run Ethereum tests using in live networks.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Type

import pytest
from pytest_metadata.plugin import metadata_key

from ethereum_test_execution import BaseExecute
from ethereum_test_forks import Fork
from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_tools import BaseTest
from ethereum_test_types import (
    ChainConfigDefaults,
    EnvironmentDefaults,
    TransactionDefaults,
)

from ..shared.execute_fill import ALL_FIXTURE_PARAMETERS
from ..shared.helpers import (
    get_spec_format_for_item,
    is_help_or_collectonly_mode,
    labeled_format_parameter_set,
)
from ..spec_version_checker.spec_version_checker import EIPSpecTestItem
from .pre_alloc import Alloc


def print_migration_warning(terminalreporter: Any = None) -> None:
    """Print migration warning about repository merge."""
    lines = [
        "",
        "=" * 80,
        "⚠️  IMPORTANT: Repository Migration in Progress - 'The Weld' ⚠️",
        "=" * 80,
        "",
        "This repository is being merged into ethereum/execution-specs (EELS) during the",
        "week of October 20-24, 2025.",
        "",
        "📅 Timeline:",
        "  • Week of Oct 13-17: Closing PRs, porting issues to EELS",
        "  • Week of Oct 20-24: Migration week - fixing CI and fixture building",
        "  • Oct 24 (ETA): Weld finalized - all development moves to EELS",
        "",
        "👉 What This Means:",
        "  • Test Contributors: After Oct 24, reopen draft PRs in ethereum/execution-specs",
        "  • All future test development happens in EELS after completion",
        "  • Fixture releases continue as usual during transition",
        "",
        "For details: https://steel.ethereum.foundation/blog/blog_posts/2025-09-11_weld-announcement/",
        "=" * 80,
        "",
    ]

    if terminalreporter:
        for line in lines:
            if "⚠️" in line or "IMPORTANT" in line:
                terminalreporter.write_line(line, bold=True, yellow=True)
            elif line.startswith("="):
                terminalreporter.write_line(line, yellow=True)
            else:
                terminalreporter.write_line(line)
    else:
        for line in lines:
            print(line)


def default_html_report_file_path() -> str:
    """
    File (default) to store the generated HTML test report. Defined as a
    function to allow for easier testing.
    """
    return "./execution_results/report_execute.html"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    execute_group = parser.getgroup(
        "execute", "Arguments defining test execution behavior"
    )
    execute_group.addoption(
        "--default-gas-price",
        action="store",
        dest="default_gas_price",
        type=int,
        default=10**9,
        help=(
            "Default gas price used for transactions, unless overridden by the test."
        ),
    )
    execute_group.addoption(
        "--default-max-fee-per-gas",
        action="store",
        dest="default_max_fee_per_gas",
        type=int,
        default=10**9,
        help=(
            "Default max fee per gas used for transactions, unless overridden by the test."
        ),
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
    execute_group.addoption(
        "--transaction-gas-limit",
        action="store",
        dest="transaction_gas_limit",
        default=EnvironmentDefaults.gas_limit // 4,
        type=int,
        help=(
            "Maximum gas used to execute a single transaction. "
            "Will be used as ceiling for tests that attempt to consume the entire block gas limit."
            f"(Default: {EnvironmentDefaults.gas_limit // 4})"
        ),
    )
    execute_group.addoption(
        "--transactions-per-block",
        action="store",
        dest="transactions_per_block",
        type=int,
        default=None,
        help=(
            "Number of transactions to send before producing the next block."
        ),
    )
    execute_group.addoption(
        "--get-payload-wait-time",
        action="store",
        dest="get_payload_wait_time",
        type=float,
        default=0.3,
        help=(
            "Time to wait after sending a forkchoice_updated before getting the payload."
        ),
    )
    execute_group.addoption(
        "--chain-id",
        action="store",
        dest="chain_id",
        required=False,
        type=int,
        default=None,
        help="ID of the chain where the tests will be executed.",
    )

    report_group = parser.getgroup(
        "tests", "Arguments defining html report behavior"
    )
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
def pytest_configure(config: pytest.Config) -> None:
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
    print_migration_warning()
    # Modify the block gas limit if specified.
    if config.getoption("transaction_gas_limit"):
        EnvironmentDefaults.gas_limit = config.getoption(
            "transaction_gas_limit"
        )
    if is_help_or_collectonly_mode(config):
        return

    config.engine_rpc_supported = False  # type: ignore[attr-defined]
    if (
        config.getoption("disable_html")
        and config.getoption("htmlpath") is None
    ):
        # generate an html report by default, unless explicitly disabled
        config.option.htmlpath = Path(default_html_report_file_path())

    command_line_args = "execute " + " ".join(config.invocation_params.args)
    config.stash[metadata_key]["Command-line args"] = (
        f"<code>{command_line_args}</code>"
    )

    # Configuration for the forks pytest plugin
    config.skip_transition_forks = True  # type: ignore[attr-defined]
    config.single_fork_mode = True  # type: ignore[attr-defined]

    # Configure the chain ID for the tests.
    rpc_chain_id = config.getoption("rpc_chain_id", None)
    chain_id = config.getoption("chain_id")
    if rpc_chain_id is not None or chain_id is not None:
        if rpc_chain_id is not None and chain_id is not None:
            if chain_id != rpc_chain_id:
                pytest.exit(
                    "Conflicting chain ID configuration. "
                    "The --rpc-chain-id flag is deprecated and will be removed in a future "
                    "release. Use --chain-id instead."
                )
        if rpc_chain_id is not None:
            ChainConfigDefaults.chain_id = rpc_chain_id
        if chain_id is not None:
            ChainConfigDefaults.chain_id = chain_id


def pytest_metadata(metadata: dict[str, Any]) -> None:
    """Add or remove metadata to/from the pytest report."""
    metadata.pop("JAVA_HOME", None)


def pytest_html_results_table_header(cells: list[str]) -> None:
    """Customize the table headers of the HTML report table."""
    cells.insert(
        3, '<th class="sortable" data-column-type="sender">Sender</th>'
    )
    cells.insert(
        4,
        '<th class="sortable" data-column-type="fundedAccounts">Funded Accounts</th>',
    )
    cells.insert(
        5,
        '<th class="sortable" data-column-type="fundedAccounts">Deployed Contracts</th>',
    )
    del cells[-1]  # Remove the "Links" column


def pytest_html_results_table_row(report: Any, cells: list[str]) -> None:
    """Customize the table rows of the HTML report table."""
    if hasattr(report, "user_properties"):
        user_props = dict(report.user_properties)
        if (
            "sender_address" in user_props
            and user_props["sender_address"] is not None
        ):
            sender_address = user_props["sender_address"]
            cells.insert(3, f"<td>{sender_address}</td>")
        else:
            cells.insert(3, "<td>Not available</td>")

        if (
            "funded_accounts" in user_props
            and user_props["funded_accounts"] is not None
        ):
            funded_accounts = user_props["funded_accounts"]
            cells.insert(4, f"<td>{funded_accounts}</td>")
        else:
            cells.insert(4, "<td>Not available</td>")

    del cells[-1]  # Remove the "Links" column


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
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
                report.user_properties.append(
                    (property_name, getattr(item.config, property_name))
                )


def pytest_html_report_title(report: Any) -> None:
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Execute Test Report"


@pytest.fixture(scope="session")
def transactions_per_block(
    request: pytest.FixtureRequest,
) -> int:
    """
    Return the number of transactions to send before producing the next block.
    """
    if transactions_per_block := request.config.getoption(
        "transactions_per_block"
    ):
        return transactions_per_block

    # Get the number of workers for the test
    worker_count_env = os.environ.get("PYTEST_XDIST_WORKER_COUNT")
    if not worker_count_env:
        return 1
    return max(int(worker_count_env), 1)


@pytest.fixture(scope="session")
def default_gas_price(request: pytest.FixtureRequest) -> int:
    """Return default gas price used for transactions."""
    gas_price = request.config.getoption("default_gas_price")
    assert gas_price > 0, "Gas price must be greater than 0"
    return gas_price


@pytest.fixture(scope="session")
def default_max_fee_per_gas(
    request: pytest.FixtureRequest,
) -> int:
    """Return default max fee per gas used for transactions."""
    return request.config.getoption("default_max_fee_per_gas")


@pytest.fixture(scope="session")
def default_max_priority_fee_per_gas(
    request: pytest.FixtureRequest,
) -> int:
    """Return default max priority fee per gas used for transactions."""
    return request.config.getoption("default_max_priority_fee_per_gas")


@pytest.fixture(autouse=True, scope="session")
def modify_transaction_defaults(
    default_gas_price: int,
    default_max_fee_per_gas: int,
    default_max_priority_fee_per_gas: int,
) -> None:
    """
    Modify transaction defaults to values better suited for live networks.
    """
    TransactionDefaults.gas_price = default_gas_price
    TransactionDefaults.max_fee_per_gas = default_max_fee_per_gas
    TransactionDefaults.max_priority_fee_per_gas = (
        default_max_priority_fee_per_gas
    )


@dataclass(kw_only=True)
class Collector:
    """
    A class that collects transactions and post-allocations for every test
    case.
    """

    eth_rpc: EthRPC
    collected_tests: Dict[str, BaseExecute] = field(default_factory=dict)

    def collect(self, test_name: str, execute_format: BaseExecute) -> None:
        """Collect transactions and post-allocations for the test case."""
        self.collected_tests[test_name] = execute_format


@pytest.fixture(scope="session")
def collector(
    request: pytest.FixtureRequest,
    eth_rpc: EthRPC,
) -> Generator[Collector, None, None]:
    """
    Return configured fixture collector instance used for all tests in one test
    module.
    """
    del request

    collector = Collector(eth_rpc=eth_rpc)
    yield collector


def base_test_parametrizer(cls: Type[BaseTest]) -> Any:
    """
    Generate pytest.fixture for a given BaseTest subclass.

    Implementation detail: All spec fixtures must be scoped on test function
    level to avoid leakage between tests.
    """
    cls_fixture_parameters = [
        p for p in ALL_FIXTURE_PARAMETERS if p in cls.model_fields
    ]

    @pytest.fixture(
        scope="function",
        name=cls.pytest_parameter_name(),
    )
    def base_test_parametrizer_func(
        request: Any,
        fork: Fork,
        pre: Alloc,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        collector: Collector,
    ) -> Type[BaseTest]:
        """
        Fixture used to instantiate an auto-fillable BaseTest object from
        within a test function.

        Every test that defines a test filler must explicitly specify its
        parameter name (see `pytest_parameter_name` in each implementation of
        BaseTest) in its function arguments.

        When parametrize, indirect must be used along with the fixture format
        as value.
        """
        execute_format = request.param
        assert execute_format in BaseExecute.formats.values()
        assert issubclass(execute_format, BaseExecute)

        if execute_format.requires_engine_rpc:
            assert engine_rpc is not None, (
                "Engine RPC is required for this format."
            )

        class BaseTestWrapper(cls):  # type: ignore
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                kwargs["t8n_dump_dir"] = None
                if "pre" not in kwargs:
                    kwargs["pre"] = pre
                elif kwargs["pre"] != pre:
                    raise ValueError(
                        "The pre-alloc object was modified by the test."
                    )
                # Set default for expected_benchmark_gas_used
                if "expected_benchmark_gas_used" not in kwargs:
                    kwargs["expected_benchmark_gas_used"] = (
                        request.getfixturevalue("gas_benchmark_value")
                    )
                kwargs |= {
                    p: request.getfixturevalue(p)
                    for p in cls_fixture_parameters
                    if p not in kwargs
                }

                request.node.config.sender_address = str(pre._sender)

                super(BaseTestWrapper, self).__init__(*args, **kwargs)
                self._request = request

                # wait for pre-requisite transactions to be included in blocks
                pre.wait_for_transactions()
                for (
                    deployed_contract,
                    expected_code,
                ) in pre._deployed_contracts:
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

                execute = self.execute(
                    fork=fork, execute_format=execute_format
                )
                execute.execute(
                    fork=fork,
                    eth_rpc=eth_rpc,
                    engine_rpc=engine_rpc,
                    request=request,
                )
                collector.collect(request.node.nodeid, execute)

        return BaseTestWrapper

    return base_test_parametrizer_func


# Dynamically generate a pytest fixture for each test spec type.
for cls in BaseTest.spec_types.values():
    # Fixture needs to be defined in the global scope so pytest can detect it.
    globals()[cls.pytest_parameter_name()] = base_test_parametrizer(cls)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Pytest hook used to dynamically generate test cases for each fixture format
    a given test spec supports.
    """
    engine_rpc_supported = metafunc.config.engine_rpc_supported  # type: ignore
    for test_type in BaseTest.spec_types.values():
        if test_type.pytest_parameter_name() in metafunc.fixturenames:
            parameter_set = []
            for (
                format_with_or_without_label
            ) in test_type.supported_execute_formats:
                param = labeled_format_parameter_set(
                    format_with_or_without_label
                )
                if (
                    format_with_or_without_label.requires_engine_rpc
                    and not engine_rpc_supported
                ):
                    param.marks.append(  # type: ignore
                        pytest.mark.skip(reason="Engine RPC is not supported")
                    )
                parameter_set.append(param)
            metafunc.parametrize(
                [test_type.pytest_parameter_name()],
                parameter_set,
                scope="function",
                indirect=True,
            )


def pytest_collection_modifyitems(
    items: List[pytest.Item],
) -> None:
    """
    Remove transition tests and add the appropriate execute markers to the
    test.
    """
    items_for_removal = []
    for i, item in enumerate(items):
        if isinstance(item, EIPSpecTestItem):
            continue
        params: Dict[str, Any] = item.callspec.params  # type: ignore
        if "fork" not in params or params["fork"] is None:
            items_for_removal.append(i)
            continue
        fork: Fork = params["fork"]
        spec_type, execute_format = get_spec_format_for_item(params)
        assert issubclass(execute_format, BaseExecute)
        markers = list(item.iter_markers())
        if spec_type.discard_execute_format_by_marks(
            execute_format, fork, markers
        ):
            items_for_removal.append(i)
            continue
        for marker in markers:
            if marker.name == "execute":
                for mark in marker.args:
                    item.add_marker(mark)
            elif marker.name == "valid_at_transition_to":
                items_for_removal.append(i)
                continue
            elif marker.name == "pre_alloc_modify":
                item.add_marker(
                    pytest.mark.skip(
                        reason="Pre-alloc modification not supported"
                    )
                )

        if "yul" in item.fixturenames:  # type: ignore
            item.add_marker(pytest.mark.yul_test)

    for i in reversed(items_for_removal):
        items.pop(i)
