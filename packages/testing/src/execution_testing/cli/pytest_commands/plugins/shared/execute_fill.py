"""
Shared pytest fixtures and hooks for EEST generation modes (fill and execute).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple

import pytest
from pytest import StashKey

from execution_testing.base_types import Account, Number
from execution_testing.base_types import Alloc as BaseAlloc
from execution_testing.execution import (
    BaseExecute,
    LabeledExecuteFormat,
)
from execution_testing.fixtures import BaseFixture, LabeledFixtureFormat

if TYPE_CHECKING:
    from execution_testing.forks import Fork, TransitionFork
import sys

from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.specs import BaseTest
from execution_testing.specs.base import OpMode
from execution_testing.test_types import (
    EOA,
    Alloc,
    ChainConfig,
)

from ..shared.address_stubs import AddressStubs, StubEOA
from ..shared.helpers import get_rpc_endpoint
from ..shared.pre_alloc import AllocFlags
from ..spec_version_checker.spec_version_checker import EIPSpecTestItem

logger = get_logger(__name__)

stub_accounts_key: StashKey[Dict[str, Account]] = StashKey()
stub_eoas_key: StashKey[Dict[str, EOA]] = StashKey()

ALL_FIXTURE_PARAMETERS = {
    "gas_benchmark_value",
    "fixed_opcode_count",
    "genesis_environment",
    "env",
}
"""
List of test parameters that have a default fixture value which can be
retrieved and used for the test instance if it was not explicitly specified
when calling from the test function.

All parameter names included in this list must define a fixture in one of the
plugins.
"""


def _validate_and_cache_address_stubs(
    address_stubs: AddressStubs, rpc_endpoint: str
) -> Tuple[Dict[str, Account], Dict[str, EOA]]:
    """
    Validate stub addresses on-chain and return caches.

    For stubs without a private key (contract stubs), validate that
    the address has deployed code.  For stubs with a private key
    (EOA stubs), create an ``EOA`` with the on-chain nonce.
    Exit the session if any contract stub has no deployed code.

    Return ``(accounts, eoas)`` where *accounts* maps contract stub
    labels to their on-chain ``Account`` and *eoas* maps EOA stub
    labels to ``EOA`` instances with on-chain nonces.
    """
    eth_rpc = EthRPC(rpc_endpoint)
    labels = list(address_stubs.root.keys())
    addresses = [address_stubs.root[k].addr for k in labels]
    query = BaseAlloc(root={addr: Account() for addr in addresses})
    alloc = eth_rpc.get_alloc(query)
    empty: list[str] = []
    accounts: Dict[str, Account] = {}
    eoas: Dict[str, EOA] = {}
    for label, addr in zip(labels, addresses, strict=True):
        entry = address_stubs.get_entry(label)
        account = alloc.root.get(addr) or Account()
        if isinstance(entry, StubEOA):
            eoa = EOA(key=entry.pkey)
            eoa.nonce = Number(account.nonce)
            eoas[label] = eoa
            accounts[label] = account
        elif not account.code:
            empty.append(f"  '{label}' at {addr}")
        else:
            accounts[label] = account
    if empty:
        pytest.exit(
            "The following address stubs have no code on-chain:\n"
            + "\n".join(empty)
            + "\nPlease verify the addresses in --address-stubs."
        )
    logger.info(
        f"Validated {len(accounts) + len(eoas)} address stubs: "
        f"{len(accounts)} contracts, {len(eoas)} EOAs"
    )
    return accounts, eoas


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Pytest hook called after command line options have been parsed and before
    test collection begins.

    A couple of notes:
    1. Register the plugin's custom markers and process command-line options.

       Custom marker registration:
       https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers

    2. `@pytest.hookimpl(tryfirst=True)` is applied to ensure that this hook is
       called before the pytest-html plugin's pytest_configure to ensure that
       it uses the modified `htmlpath` option.
    """
    address_stubs = config.getoption("address_stubs", None)
    rpc_endpoint = get_rpc_endpoint(config)
    if address_stubs is not None and rpc_endpoint is None:
        pytest.exit(
            "--address-stubs requires --rpc-endpoint to fetch "
            "contract code from the network."
        )
    if (
        address_stubs is not None
        and rpc_endpoint is not None
        and not config.getoption("collectonly", default=False)
    ):
        accounts, eoas = _validate_and_cache_address_stubs(
            address_stubs, rpc_endpoint
        )
        config.stash[stub_accounts_key] = accounts
        config.stash[stub_eoas_key] = eoas
    if config.pluginmanager.has_plugin(
        "execution_testing.cli.pytest_commands.plugins.filler.filler"
    ):
        for fixture_format in BaseFixture.formats.values():
            name = fixture_format.format_name.lower()
            desc = fixture_format.description
            config.addinivalue_line("markers", f"{name}: {desc}")
        for (
            label,
            labeled_fixture_format,
        ) in LabeledFixtureFormat.registered_labels.items():
            config.addinivalue_line(
                "markers",
                (f"{label}: {labeled_fixture_format.description}"),
            )
    elif config.pluginmanager.has_plugin(
        "execution_testing.cli.pytest_commands.plugins.execute.execute"
    ):
        for execute_format in BaseExecute.formats.values():
            name = execute_format.format_name.lower()
            desc = execute_format.description
            config.addinivalue_line("markers", f"{name}: {desc}")
        for (
            label,
            labeled_execute_format,
        ) in LabeledExecuteFormat.registered_labels.items():
            config.addinivalue_line(
                "markers",
                (f"{label}: {labeled_execute_format.description}"),
            )
    else:
        raise Exception("Neither the filler nor the execute plugin is loaded.")

    for spec_type in BaseTest.spec_types.values():
        for marker, description in spec_type.supported_markers.items():
            config.addinivalue_line(
                "markers",
                (f"{marker}: {description}"),
            )

    if not hasattr(config, "op_mode"):
        config.op_mode = OpMode.CONSENSUS  # type: ignore[attr-defined]

    config.addinivalue_line(
        "markers",
        "yul_test: a test case that compiles Yul code.",
    )
    config.addinivalue_line(
        "markers",
        "compile_yul_with(fork): Always compile Yul source using the "
        "corresponding evm version.",
    )
    config.addinivalue_line(
        "markers",
        "fill: Markers to be added in fill mode only.",
    )
    config.addinivalue_line(
        "markers",
        "execute: Markers to be added in execute mode only.",
    )
    config.addinivalue_line(
        "markers",
        "exception_test: Negative tests that include an invalid block or "
        "transaction.",
    )
    config.addinivalue_line(
        "markers",
        "eip_checklist(item_id, eip=None): Mark a test as implementing a "
        "specific checklist item. The first positional parameter is the "
        "checklist item ID. The optional 'eip' keyword parameter specifies "
        "additional EIPs covered by the test.",
    )
    config.addinivalue_line(
        "markers",
        "derived_test: Mark a test as a derived test (E.g. a BlockchainTest "
        "that is derived from a StateTest).",
    )
    config.addinivalue_line(
        "markers",
        "tagged: Marks a static test as tagged. Tags are used to generate "
        "dynamic addresses for static tests at fill time. All tagged tests "
        "are compatible with dynamic address generation.",
    )
    config.addinivalue_line(
        "markers",
        "untagged: Marks a static test as untagged. Tags are used to generate "
        "dynamic addresses for static tests at fill time. Untagged tests are "
        "incompatible with dynamic address generation.",
    )
    config.addinivalue_line(
        "markers",
        "verify_sync: Marks a test to be run with `consume sync`, verifying "
        "blockchain engine tests and having hive clients sync after payload "
        "execution.",
    )
    config.addinivalue_line(
        "markers",
        "pre_alloc_group: Control shared pre-allocation grouping (use "
        '"separate" for isolated group or custom string for named groups)',
    )
    config.addinivalue_line(
        "markers",
        "slow: Marks a test as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "ported_from: Marks a test as ported from ethereum/tests",
    )
    config.addinivalue_line(
        "markers",
        "valid_for_bpo_forks: Marks a test as valid for BPO forks",
    )
    config.addinivalue_line(
        "markers",
        "mainnet: Tests crafted for running on mainnet and sanity checking.",
    )
    config.addinivalue_line(
        "markers",
        "fully_tagged: Marks a static test as fully tagged with all metadata.",
    )
    config.addinivalue_line(
        "markers",
        "pre_alloc_mutable: Marks a test to allow impossible mutations in the "
        "pre-state.",
    )
    config.addinivalue_line(
        "markers",
        "fixture_format_id: ID used to describe the fixture format.",
    )
    config.addinivalue_line(
        "markers",
        "transition_tool_cache_key: Key used to match the transition tool "
        "cache for the test during fill.",
    )
    config.addinivalue_line(
        "markers",
        "fixture_subfolder(level, prefix): "
        "Signal that fixtures should be placed in a subfolder",
    )
    config.addinivalue_line(
        "markers",
        "eels_base_coverage: Minimized subset selected to preserve high "
        "EELS line-coverage parity.",
    )


@pytest.fixture(scope="function")
def test_case_description(request: pytest.FixtureRequest) -> str:
    """
    Fixture to extract and combine docstrings from the test class and the test
    function.
    """
    description_unavailable = (
        "No description available - add a docstring to the python test "
        "class or function."
    )
    test_class_doc = ""
    test_function_doc = ""
    if hasattr(request.node, "cls"):
        test_class_doc = (
            f"Test class documentation:\n{request.cls.__doc__}"
            if request.cls
            else ""
        )
    if hasattr(request.node, "function"):
        test_function_doc = (
            f"{request.function.__doc__}" if request.function.__doc__ else ""
        )
    if not test_class_doc and not test_function_doc:
        return description_unavailable
    combined_docstring = f"{test_class_doc}\n\n{test_function_doc}".strip()
    return combined_docstring


def pytest_make_parametrize_id(
    config: pytest.Config, val: str, argname: str
) -> str:
    """
    Pytest hook called when generating test ids. We use this to generate more
    readable test ids for the generated tests.
    """
    del config
    if argname == "parametrized_fork":
        return f"fork_{val}"
    return f"{argname}_{val}"


@pytest.fixture(scope="function")
def fork(
    parametrized_fork: Fork | TransitionFork,
    monkeypatch: pytest.MonkeyPatch,
    env_gas_limit: int,
) -> Fork | TransitionFork:
    """
    Return a per-test fork variant whose ``_env_gas_limit`` tracks the
    ``Environment.gas_limit`` used by the test.
    """
    fork_variant = parametrized_fork.with_env_gas_limit(env_gas_limit)

    # Now we monkey-patch the `Environment` class with one that is aware of
    # the fork that the test is using, and will update its `_env_gas_limit`
    # automatically.
    # TODO: This should not be necessary, we should treat the `env` object the
    #  same way we do `pre` and force it to be a singleton in the test's
    #  context.
    from execution_testing.test_types.block_types import (
        Environment as OriginalEnvironment,
    )

    class _ForkAwareEnvironment(OriginalEnvironment):
        """Transparently syncs ``gas_limit`` back to the fork variant."""

        def model_post_init(self, __context: object) -> None:
            super().model_post_init(__context)
            fork_variant._env_gas_limit = int(self.gas_limit)

        def __setattr__(self, name: str, value: object) -> None:
            super().__setattr__(name, value)
            if name == "gas_limit":
                fork_variant._env_gas_limit = int(self.gas_limit)

    # Replace Environment in every module that imported the original class
    # so that both `Environment(...)` in test code and in conftest fixtures
    # create _ForkAwareEnvironment instances.
    for mod in list(sys.modules.values()):
        try:
            if getattr(mod, "Environment", None) is OriginalEnvironment:
                monkeypatch.setattr(mod, "Environment", _ForkAwareEnvironment)
        except Exception:
            continue

    return fork_variant


SPEC_TYPES_PARAMETERS: List[str] = list(BaseTest.spec_types.keys())


def pytest_runtest_call(item: pytest.Item) -> None:
    """Pytest hook called in the context of test execution."""
    if isinstance(item, EIPSpecTestItem):
        return

    class InvalidFillerError(Exception):
        def __init__(self, message: str):
            super().__init__(message)

    if not isinstance(item, pytest.Function):
        return

    if (
        "state_test" in item.fixturenames
        and "blockchain_test" in item.fixturenames
    ):
        raise InvalidFillerError(
            "A filler should only implement either a state test or a "
            "blockchain test; not both."
        )

    # Check that the test defines either test type as parameter.
    if not any(i for i in item.funcargs if i in SPEC_TYPES_PARAMETERS):
        pytest.fail(
            "Test must define either one of the following parameters to "
            + "properly generate a test: "
            + ", ".join(SPEC_TYPES_PARAMETERS)
        )


# Global `sender` fixture that can be overridden by tests.
@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Fund an EOA from pre-alloc."""
    return pre.fund_eoa()


@pytest.fixture(scope="session")
def chain_config() -> ChainConfig:
    """Return chain configuration."""
    return ChainConfig()


@pytest.fixture(scope="function")
def alloc_flags_from_test_markers(
    request: pytest.FixtureRequest,
) -> AllocFlags:
    """Return allocation mode for a given test based on its markers."""
    flags = AllocFlags.NONE
    if request.node.get_closest_marker("pre_alloc_mutable"):
        flags |= AllocFlags.MUTABLE
    return flags


@pytest.fixture(scope="function")
def alloc_flags(
    alloc_flags_from_test_markers: AllocFlags,
) -> AllocFlags:
    """
    Return allocation mode for the test.

    By default, this is based on markers tests only, but plugins can
    override this behavior.
    """
    return alloc_flags_from_test_markers


@pytest.fixture(scope="function")
def is_tx_gas_heavy_test(request: pytest.FixtureRequest) -> bool:
    """
    Check, given the test node properties, whether the test is gas-heavy
    for transaction execution.
    """
    has_slow_marker = request.node.get_closest_marker("slow") is not None
    benchmark_dir = Path(request.config.rootpath) / "tests" / "benchmark"
    is_benchmark = benchmark_dir in Path(request.node.fspath).parents
    return has_slow_marker or is_benchmark


@pytest.fixture(scope="function")
def is_exception_test(request: pytest.FixtureRequest) -> bool:
    """
    Check, given the test node properties, whether the test is an exception
    test (invalid block, invalid transaction).
    """
    return request.node.get_closest_marker("exception_test") is not None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    static_filler_group = parser.getgroup(
        "static", "Arguments defining static filler behavior"
    )
    static_filler_group.addoption(
        "--fill-static-tests",
        action="store_true",
        dest="fill_static_tests_enabled",
        default=None,
        help=("Enable reading and filling from static test files."),
    )
