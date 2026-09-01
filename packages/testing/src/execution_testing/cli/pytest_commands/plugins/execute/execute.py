"""
Test execution plugin for pytest, to run Ethereum tests on live networks.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Type

import pytest
from pytest_metadata.plugin import metadata_key

from execution_testing.base_types import Account
from execution_testing.base_types.base_types import HexNumber
from execution_testing.execution import BaseExecute, LabeledExecuteFormat
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.rpc import EngineRPC, EthRPC
from execution_testing.specs import BaseTest
from execution_testing.test_types import Alloc as BaseAlloc
from execution_testing.test_types import (
    Environment,
    EnvironmentDefaults,
)

from ..shared.execute_fill import ALL_FIXTURE_PARAMETERS
from ..shared.helpers import (
    get_spec_format_for_item,
    is_help_or_collectonly_mode,
    option_was_explicitly_set,
)
from ..spec_version_checker.spec_version_checker import EIPSpecTestItem
from .pre_alloc import Alloc

logger = get_logger(__name__)


def default_html_report_file_path() -> str:
    """
    File (default) to store the generated HTML test report. Defined as a
    function to allow for easier testing.
    """
    return "./execution_results/report_execute.html"


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add execute-specific command-line options.

    The live-client flag set (``--default-gas-price``, ``--get-payload-
    wait-time``, ``--dry-run``, ...) now lives in
    :mod:`plugins.shared.live_client_flags`, which this plugin requires.
    Both ``pytest-execute*.ini`` and ``pytest-fill-stateful.ini`` load the
    shared plugin ahead of this one.
    """
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
    # Keep execute-mode overrides working, but avoid rewriting the global
    # default when this plugin is merely imported into nested pytest sessions.
    if option_was_explicitly_set(config, "--transaction-gas-limit"):
        EnvironmentDefaults.gas_limit = config.getoption(
            "transaction_gas_limit"
        )

    config.engine_rpc_supported = False  # type: ignore[attr-defined]

    if is_help_or_collectonly_mode(config):
        return

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
        '<th class="sortable" data-column-type="fundedAccounts">'
        "Funded Accounts</th>",
    )
    cells.insert(
        5,
        '<th class="sortable" data-column-type="fundedAccounts">'
        "Deployed Contracts</th>",
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


# NOTE: ``transactions_per_block``, ``default_gas_price``, ``dry_run``,
# ``max_batch_size``, ``use_testing_build_block``,
# ``default_max_fee_per_gas``, ``default_max_priority_fee_per_gas``,
# ``default_max_fee_per_blob_gas``, ``max_priority_fee_per_gas``,
# ``max_fee_per_gas``, ``max_fee_per_blob_gas``, ``gas_price``, and
# ``max_gas_limit_per_test`` now live in
# :mod:`plugins.shared.live_client_flags` so fill-stateful can reuse them
# without loading this plugin's parametrizer/hooks.


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


@dataclass(kw_only=True)
class GasInfo:
    """A class that contains gas limit and minimum balance for a test."""

    gas_limit: int
    minimum_balance: int


@dataclass(kw_only=True)
class GasInfoAccumulator:
    """A class that accumulates gas limit for all tests."""

    test_gas_info: Dict[str, GasInfo] = field(default_factory=dict)

    def add(
        self, test_name: str, gas_limit: int, minimum_balance: int
    ) -> None:
        """Add gas limit and minimum balance for a test."""
        self.test_gas_info[test_name] = GasInfo(
            gas_limit=gas_limit, minimum_balance=minimum_balance
        )

    def total_gas_limit(self) -> int:
        """Return the total gas limit for all tests."""
        return sum(
            gas_info.gas_limit for gas_info in self.test_gas_info.values()
        )

    def total_minimum_balance(self) -> int:
        """Return the total minimum balance for all tests."""
        return sum(
            gas_info.minimum_balance
            for gas_info in self.test_gas_info.values()
        )


@pytest.fixture(scope="session")
def gas_limit_accumulator() -> Generator[GasInfoAccumulator, None, None]:
    """Return the gas limit accumulator for all tests."""
    gas_limit_accumulator = GasInfoAccumulator()
    yield gas_limit_accumulator
    logger.info(f"Total gas limit: {gas_limit_accumulator.total_gas_limit()}")
    total_min_eth = gas_limit_accumulator.total_minimum_balance() / 10**18
    logger.info(f"Total minimum balance: {total_min_eth:.18f}")


@pytest.fixture(scope="session")
def env_gas_limit(eth_rpc: EthRPC) -> HexNumber:
    """
    Return the environment gas limit derived from the head block before
    tests start running.
    """
    head_block = eth_rpc.get_block_by_number()
    assert head_block is not None, "Unable to obtain head block from RPC"
    return HexNumber(head_block["gasLimit"])


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
        dry_run: bool,
        collector: Collector,
        gas_benchmark_value: int,
        fixed_opcode_count: int | None,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
        max_gas_limit_per_test: int | None,
        gas_limit_accumulator: GasInfoAccumulator,
        env_gas_limit: HexNumber,
        is_tx_gas_heavy_test: bool,
        is_exception_test: bool,
        is_inclusion_test: bool,
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
        del fixed_opcode_count
        execute_format = request.param
        assert execute_format in BaseExecute.formats.values()
        assert isinstance(execute_format, LabeledExecuteFormat) or issubclass(
            execute_format, BaseExecute
        )

        if execute_format.requires_engine_rpc:
            assert engine_rpc is not None, (
                "Engine RPC is required for this format."
            )

        class BaseTestWrapper(cls):  # type: ignore
            __is_base_test_wrapper__ = True

            def __init__(self, *args: Any, **kwargs: Any) -> None:
                if "pre" not in kwargs:
                    kwargs["pre"] = pre
                elif kwargs["pre"] != pre:
                    raise ValueError(
                        "The pre-alloc object was modified by the test."
                    )
                if "expected_benchmark_gas_used" not in kwargs:
                    kwargs["expected_benchmark_gas_used"] = gas_benchmark_value
                kwargs["fork"] = fork
                kwargs["operation_mode"] = request.config.op_mode
                kwargs["is_tx_gas_heavy_test"] = is_tx_gas_heavy_test
                kwargs["is_exception_test"] = is_exception_test
                kwargs["is_inclusion_test"] = is_inclusion_test
                kwargs |= {
                    p: request.getfixturevalue(p)
                    for p in cls_fixture_parameters
                    if p not in kwargs
                }

                request.node.config.sender_address = str(pre._sender)

                super(BaseTestWrapper, self).__init__(*args, **kwargs)
                execute = self.execute(execute_format=execute_format)

                execute.prepare_transactions(
                    env=Environment(gas_limit=env_gas_limit),
                    gas_price=gas_price,
                    max_fee_per_gas=max_fee_per_gas,
                    max_priority_fee_per_gas=max_priority_fee_per_gas,
                    max_fee_per_blob_gas=max_fee_per_blob_gas,
                    fork=fork,
                )

                # get balances of required sender accounts
                required_balances = execute.get_required_sender_balances(
                    fork=fork,
                )

                pre.resolve_deferred_checks()

                minimum_balance, gas_consumption = (
                    pre.minimum_balance_for_pending_transactions(
                        required_balances,
                        gas_price=gas_price,
                        max_fee_per_gas=max_fee_per_gas,
                        max_priority_fee_per_gas=max_priority_fee_per_gas,
                        max_fee_per_blob_gas=max_fee_per_blob_gas,
                    )
                )
                if max_gas_limit_per_test is not None:
                    assert gas_consumption <= max_gas_limit_per_test, (
                        f"Test gas consumption ({gas_consumption}) exceeds "
                        f"the gas limit allowed per test"
                        f"({max_gas_limit_per_test})."
                    )

                gas_limit_accumulator.add(
                    test_name=request.node.nodeid,
                    gas_limit=gas_consumption,
                    minimum_balance=minimum_balance,
                )

                if dry_run:
                    min_eth = minimum_balance / 10**18
                    logger.info(f"Minimum balance required: {min_eth:.18f}")
                    logger.info(f"Gas consumption: {gas_consumption}")
                    return

                # send the funds to the required sender accounts
                pre.send_pending_transactions()

                if pre._deployed_contracts:
                    contract_alloc = BaseAlloc(
                        root={
                            addr: Account()
                            for addr, _ in pre._deployed_contracts
                        }
                    )
                    actual_alloc = eth_rpc.get_alloc(contract_alloc)
                    for (
                        deployed_contract,
                        expected_code,
                    ) in pre._deployed_contracts:
                        actual_account = actual_alloc.root[deployed_contract]
                        assert actual_account is not None
                        actual_code = actual_account.code
                        if actual_code != expected_code:
                            msg = (
                                f"Deployed test contract didn't match "
                                f"expected code at address "
                                f"{deployed_contract} "
                                f"(not enough gas_limit?).\n"
                                f"Expected: {expected_code}\n"
                                f"Actual: {actual_code}"
                            )
                            logger.error(msg)
                            raise Exception(msg)
                request.node.config.funded_accounts = ", ".join(
                    [str(eoa) for eoa in pre._funded_eoa]
                )

                execute_result = execute.execute(
                    fork=fork,
                    eth_rpc=eth_rpc,
                    engine_rpc=engine_rpc,
                    request=request,
                )
                self.validate_benchmark_gas(
                    benchmark_gas_used=execute_result.benchmark_gas_used,
                    gas_benchmark_value=gas_benchmark_value,
                )

                collector.collect(request.node.nodeid, execute)

        return BaseTestWrapper

    return base_test_parametrizer_func


# Dynamically generate a pytest fixture for each test spec type.
for name, cls in BaseTest.spec_types.items():
    if getattr(cls, "__is_base_test_wrapper__", False):
        raise RuntimeError(
            f"Test spec type {name}: {cls.__name__} is already wrapped. "
            f"{BaseTest.spec_types.items()}."
        )
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
                execute_format,
                param,
            ) in test_type.execute_format_parameters():
                if (
                    execute_format.requires_engine_rpc
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


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    items: List[pytest.Item],
) -> None:
    """
    Remove transition tests and add the appropriate execute markers to the
    test.

    Runs tryfirst so that items collected without a fork parametrization
    (tests not valid for the session's fork) are removed before other
    plugins inspect item params, as in the filler plugin.
    """
    items_for_removal = []
    for i, item in enumerate(items):
        if isinstance(item, EIPSpecTestItem):
            continue
        params: Dict[str, Any] = item.callspec.params  # type: ignore
        if "fork" not in params or params["fork"] is None:
            items_for_removal.append(i)
            continue
        fork: Fork | TransitionFork = params["fork"]
        spec_type, execute_format = get_spec_format_for_item(params)
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
            elif marker.name == "pre_alloc_mutable":
                item.add_marker(
                    pytest.mark.skip(
                        reason="Pre-alloc modification not supported"
                    )
                )

    for i in reversed(items_for_removal):
        items.pop(i)
