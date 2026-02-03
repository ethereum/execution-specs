"""
Top-level pytest configuration file providing:
- Command-line options,
- Test-fixtures that can be used by all test cases,
and that modifies pytest hooks in order to fill test specs for all tests
and writes the generated fixtures to file.
"""

import atexit
import configparser
import datetime
import json
import os
import signal
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Self, Set, Type

import pytest
import xdist
from _pytest.compat import NotSetType
from _pytest.terminal import TerminalReporter
from filelock import FileLock
from pytest_metadata.plugin import metadata_key

from execution_testing.base_types import (
    Account,
    Address,
    Alloc,
    ReferenceSpec,
)
from execution_testing.cli.gen_index import (
    merge_partial_indexes,
)
from execution_testing.client_clis import TransitionTool
from execution_testing.client_clis.clis.geth import FixtureConsumerTool
from execution_testing.fixtures import (
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainFixture,
    FixtureCollector,
    FixtureConsumer,
    FixtureFillingPhase,
    LabeledFixtureFormat,
    PreAllocGroup,
    PreAllocGroupBuilder,
    PreAllocGroupBuilders,
    PreAllocGroups,
    StateFixture,
    TestInfo,
    merge_partial_fixture_files,
)
from execution_testing.forks import (
    Fork,
    get_transition_fork_predecessor,
    get_transition_forks,
)
from execution_testing.specs import BaseTest
from execution_testing.specs.base import OpMode
from execution_testing.test_types import EnvironmentDefaults
from execution_testing.tools.utility.versioning import (
    generate_github_url,
    get_current_commit_hash_or_tag,
)

from ..shared.execute_fill import ALL_FIXTURE_PARAMETERS
from ..shared.helpers import (
    get_spec_format_for_item,
    is_help_or_collectonly_mode,
    labeled_format_parameter_set,
)
from ..spec_version_checker.spec_version_checker import (
    get_ref_spec_from_module,
)
from .fixture_output import FixtureOutput

# Fixture output dir for keyboard interrupt cleanup (set in pytest_configure).
# Used by _merge_on_exit to merge partial JSONL files on Ctrl+C or SIGTERM.
_fixture_output_dir: Path | None = None
_atexit_registered: bool = False
_interrupt_count: int = 0
_original_sigint_handler: Any = None
_original_sigterm_handler: Any = None


def _termination_handler(signum: int, frame: Any) -> None:
    """Handle SIGINT/SIGTERM gracefully during test filling."""
    del frame
    global _interrupt_count
    global _original_sigint_handler, _original_sigterm_handler
    _interrupt_count += 1

    if _interrupt_count == 1:
        # First interrupt: restore original handlers and re-raise
        if _original_sigint_handler is not None:
            signal.signal(signal.SIGINT, _original_sigint_handler)
        if _original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, _original_sigterm_handler)
        if signum == signal.SIGTERM:
            raise SystemExit(128 + signum)
        raise KeyboardInterrupt
    # Subsequent interrupts: ignore and print message
    print("\nMerging fixtures, please wait...", flush=True)


def _merge_on_exit() -> None:
    """Atexit handler to merge partial JSONL files. Ignores signals."""
    global _fixture_output_dir
    if _fixture_output_dir is not None:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        merge_partial_fixture_files(_fixture_output_dir)
        # Also merge index if partial indexes exist
        meta_dir = _fixture_output_dir / ".meta"
        if meta_dir.exists() and any(meta_dir.glob("partial_index*.jsonl")):
            merge_partial_indexes(_fixture_output_dir, quiet_mode=True)


@dataclass(kw_only=True)
class PhaseManager:
    """
    Manages the execution phase for fixture generation.

    The filler plugin supports two-phase execution for pre-allocation group
    generation:
    - Phase 1: Generate pre-allocation groups (pytest run with
        --generate-pre-alloc-groups).

    - Phase 2: Fill fixtures using pre-allocation
        groups (pytest run with --use-pre-alloc-groups).

    Note: These are separate pytest runs orchestrated by the CLI wrapper. Each
    run gets a fresh PhaseManager instance (no persistence between phases).
    """

    current_phase: FixtureFillingPhase
    previous_phases: Set[FixtureFillingPhase] = field(default_factory=set)

    @classmethod
    def from_config(cls, config: pytest.Config) -> "Self":
        """
        Create a PhaseManager from pytest configuration.

        Flag logic:
        - use_pre_alloc_groups: We're in phase 2 (FILL) after phase
                                1 (PRE_ALLOC_GENERATION).
        - generate_pre_alloc_groups or generate_all_formats:
                                We're in phase 1 (PRE_ALLOC_GENERATION). -
        Otherwise: Normal single-phase filling (FILL).

        Note: generate_all_formats triggers PRE_ALLOC_GENERATION because the
        CLI passes it to phase 1 to ensure all formats are considered for
        grouping.
        """
        generate_pre_alloc = config.getoption(
            "generate_pre_alloc_groups", False
        )
        use_pre_alloc = config.getoption("use_pre_alloc_groups", False)
        generate_all = config.getoption("generate_all_formats", False)

        if use_pre_alloc:
            # Phase 2: Using pre-generated groups
            return cls(
                current_phase=FixtureFillingPhase.FILL,
                previous_phases={FixtureFillingPhase.PRE_ALLOC_GENERATION},
            )
        elif generate_pre_alloc or generate_all:
            # Phase 1: Generating pre-allocation groups
            return cls(current_phase=FixtureFillingPhase.PRE_ALLOC_GENERATION)
        else:
            # Normal single-phase filling
            return cls(current_phase=FixtureFillingPhase.FILL)

    @property
    def is_pre_alloc_generation(self) -> bool:
        """Check if we're in the pre-allocation generation phase."""
        return self.current_phase == FixtureFillingPhase.PRE_ALLOC_GENERATION

    @property
    def is_fill_after_pre_alloc(self) -> bool:
        """Check if we're filling after pre-allocation generation."""
        return (
            self.current_phase == FixtureFillingPhase.FILL
            and FixtureFillingPhase.PRE_ALLOC_GENERATION
            in self.previous_phases
        )

    @property
    def is_single_phase_fill(self) -> bool:
        """Check if we're in single-phase fill mode (no pre-allocation)."""
        return (
            self.current_phase == FixtureFillingPhase.FILL
            and FixtureFillingPhase.PRE_ALLOC_GENERATION
            not in self.previous_phases
        )


@dataclass(kw_only=True)
class FormatSelector:
    """
    Handles fixture format selection based on the current phase and format
    capabilities.

    This class encapsulates the complex logic for determining which fixture
    formats should be generated in each phase of the two-phase execution model.
    """

    phase_manager: PhaseManager
    generate_all_formats: bool

    def should_generate(
        self, fixture_format: Type[BaseFixture] | LabeledFixtureFormat
    ) -> bool:
        """
        Determine if a fixture format should be generated in the current phase.

        Args:
            fixture_format: The fixture format to check (may be wrapped in
                LabeledFixtureFormat).

        Returns:
            True if the format should be generated in the current phase.

        """
        format_phases = fixture_format.format_phases

        if self.phase_manager.is_pre_alloc_generation:
            return self._should_generate_pre_alloc(format_phases)
        else:  # FILL phase
            return self._should_generate_fill(format_phases)

    def _should_generate_pre_alloc(
        self, format_phases: Set[FixtureFillingPhase]
    ) -> bool:
        """
        Determine if format should be generated during pre-alloc generation
        phase.
        """
        # Only generate formats that need pre-allocation groups
        return FixtureFillingPhase.PRE_ALLOC_GENERATION in format_phases

    def _should_generate_fill(
        self, format_phases: Set[FixtureFillingPhase]
    ) -> bool:
        """Determine if format should be generated during fill phase."""
        if (
            FixtureFillingPhase.PRE_ALLOC_GENERATION
            in self.phase_manager.previous_phases
        ):
            # Phase 2: After pre-alloc generation
            if self.generate_all_formats:
                # Generate all formats, including those that don't need pre-
                # alloc
                return True
            else:
                # Only generate formats that needed pre-alloc groups
                return (
                    FixtureFillingPhase.PRE_ALLOC_GENERATION in format_phases
                )
        else:
            # Single phase: Only generate fill-only formats
            return format_phases == {FixtureFillingPhase.FILL}


@dataclass(kw_only=True)
class FillingSession:
    """
    Manages all state for a single pytest fill session.

    This class serves as the single source of truth for all filler state
    management, including phase management, format selection, and
    pre-allocation groups.

    Important: Each pytest run gets a fresh FillingSession instance. There is
    no persistence between phase 1 (generate pre-alloc) and phase 2 (use
    pre-alloc) except through file I/O.
    """

    fixture_output: FixtureOutput
    phase_manager: PhaseManager
    format_selector: FormatSelector
    pre_alloc_groups: PreAllocGroups | None = None
    pre_alloc_group_builders: PreAllocGroupBuilders | None = None

    @classmethod
    def from_config(cls, config: pytest.Config) -> "Self":
        """
        Initialize a filling session from pytest configuration.

        Args:
            config: The pytest configuration object.

        """
        phase_manager = PhaseManager.from_config(config)
        instance = cls(
            fixture_output=FixtureOutput.from_config(config),
            phase_manager=phase_manager,
            format_selector=FormatSelector(
                phase_manager=phase_manager,
                generate_all_formats=config.getoption(
                    "generate_all_formats", False
                ),
            ),
            pre_alloc_groups=None,
        )

        # Initialize pre-alloc groups based on phase
        instance._initialize_pre_alloc_groups()
        return instance

    def _initialize_pre_alloc_groups(self) -> None:
        """Initialize pre-allocation groups based on the current phase."""
        if self.phase_manager.is_pre_alloc_generation:
            # Phase 1: Create empty container for collecting groups
            self.pre_alloc_group_builders = PreAllocGroupBuilders(root={})
        elif self.phase_manager.is_fill_after_pre_alloc:
            # Phase 2: Load pre-alloc groups from disk
            self._load_pre_alloc_groups_from_folder()

    def _load_pre_alloc_groups_from_folder(self) -> None:
        """Load pre-allocation groups from the output folder."""
        pre_alloc_folder = self.fixture_output.pre_alloc_groups_folder_path
        if pre_alloc_folder.exists():
            self.pre_alloc_groups = PreAllocGroups.from_folder(
                pre_alloc_folder, lazy_load=True
            )
        else:
            raise FileNotFoundError(
                f"Pre-allocation groups folder not found: {pre_alloc_folder}. "
                "Run phase 1 with --generate-pre-alloc-groups first."
            )

    def should_generate_format(
        self, fixture_format: Type[BaseFixture] | LabeledFixtureFormat
    ) -> bool:
        """
        Determine if a fixture format should be generated in the current
        session.

        Args:
            fixture_format: The fixture format to check.

        Returns:
            True if the format should be generated.

        """
        return self.format_selector.should_generate(fixture_format)

    def get_pre_alloc_group(self, hash_key: str) -> PreAllocGroup:
        """
        Get a pre-allocation group by hash.

        Args:
            hash_key: The hash of the pre-alloc group.

        Returns:
            The pre-allocation group.

        Raises:
            ValueError: If pre-alloc groups not initialized or hash not found.

        """
        if self.pre_alloc_groups is None:
            raise ValueError("Pre-allocation groups not initialized")

        if hash_key not in self.pre_alloc_groups:
            pre_alloc_path = (
                self.fixture_output.pre_alloc_groups_folder_path / hash_key
            )
            raise ValueError(
                f"Pre-allocation hash {hash_key} not found in "
                f"pre-allocation groups. Please check the file at: "
                f"{pre_alloc_path}. Make sure phase 1 "
                "(--generate-pre-alloc-groups) was run before phase 2."
            )

        return self.pre_alloc_groups[hash_key]

    def update_pre_alloc_group_builder(
        self, hash_key: str, group_builder: PreAllocGroupBuilder
    ) -> None:
        """
        Update or add a pre-allocation group.

        Args:
            hash_key: The hash of the pre-alloc group.
            group_builder: The pre-allocation group builder.

        Raises:
            ValueError: If not in pre-alloc generation phase.

        """
        if not self.phase_manager.is_pre_alloc_generation:
            raise ValueError(
                "Can only update pre-alloc groups in generation phase"
            )

        if self.pre_alloc_group_builders is None:
            self.pre_alloc_group_builders = PreAllocGroupBuilders(root={})

        self.pre_alloc_group_builders.root[hash_key] = group_builder

    def save_pre_alloc_groups(self) -> None:
        """Save pre-allocation groups to disk."""
        if self.pre_alloc_group_builders is None:
            return

        pre_alloc_folder = self.fixture_output.pre_alloc_groups_folder_path
        pre_alloc_folder.mkdir(parents=True, exist_ok=True)
        self.pre_alloc_group_builders.to_folder(pre_alloc_folder)


def calculate_post_state_diff(
    post_state: Alloc, genesis_state: Alloc
) -> Alloc:
    """
    Calculate the state difference between post_state and genesis_state.

    This function enables significant space savings in Engine X fixtures by
    storing only the accounts that changed during test execution, rather than
    the full post-state which may contain thousands of unchanged accounts.

    Returns an Alloc containing only the accounts that:
    - Changed between genesis and post state (balance, nonce, storage, code)
    - Were created during test execution (new accounts)
    - Were deleted during test execution (represented as None)

    Args:
        post_state: Final state after test execution
        genesis_state: Genesis pre-allocation state

    Returns:
        Alloc containing only the state differences for efficient storage

    """
    diff: Dict[Address, Account | None] = {}

    # Find all addresses that exist in either state
    all_addresses = set(post_state.root.keys()) | set(
        genesis_state.root.keys()
    )

    for address in all_addresses:
        genesis_account = genesis_state.root.get(address)
        post_account = post_state.root.get(address)

        # Account was deleted (exists in genesis but not in post)
        if genesis_account is not None and post_account is None:
            diff[address] = None

        # Account was created (doesn't exist in genesis but exists in post)
        elif genesis_account is None and post_account is not None:
            diff[address] = post_account

        # Account was modified (exists in both but different)
        elif genesis_account != post_account:
            diff[address] = post_account

        # Account unchanged - don't include in diff

    return Alloc(diff)


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


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    evm_group = parser.getgroup(
        "evm", "Arguments defining evm executable behavior"
    )
    evm_group.addoption(
        "--evm-bin",
        action="store",
        dest="evm_bin",
        type=Path,
        default=None,
        help=(
            "Path to an evm executable (or name of an executable in the "
            "PATH) that provides `t8n`. Default: `ethereum-spec-evm-resolver`."
        ),
    )
    evm_group.addoption(
        "--t8n-server-url",
        action="store",
        dest="t8n_server_url",
        type=str,
        default=None,
        help=(
            "[INTERNAL USE ONLY] URL of the t8n server to use. Used by "
            "framework tests/ci; not intended for regular CLI use."
        ),
    )
    evm_group.addoption(
        "--traces",
        action="store_true",
        dest="evm_collect_traces",
        default=None,
        help="Collect traces of execution info from the transition tool.",
    )
    evm_group.addoption(
        "--verify-fixtures",
        action="store_true",
        dest="verify_fixtures",
        default=False,
        help=(
            "Verify generated fixture JSON files using geth's evm "
            "blocktest command. By default, the same evm binary as for "
            "the t8n tool is used. A different (geth) evm binary may be "
            "specified via --verify-fixtures-bin, this must be specified "
            "if filling with a non-geth t8n tool that does not support "
            "blocktest."
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

    test_group = parser.getgroup(
        "tests", "Arguments defining filler location and output"
    )
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
            "Must be empty if it exists. If the specified path ends in "
            "'.tar.gz', then the specified tarball is additionally "
            "created (the fixtures are still written to the specified "
            "path without the '.tar.gz' suffix). Tarball output "
            "automatically enables --generate-all-formats. Can be "
            f"deleted. Default: '{default_output_directory()}'."
        ),
    )
    test_group.addoption(
        "--clean",
        action="store_true",
        dest="clean",
        default=False,
        help="Clean (remove) the output directory before filling fixtures.",
    )
    test_group.addoption(
        "--single-fixture-per-file",
        action="store_true",
        dest="single_fixture_per_file",
        default=False,
        help=(
            "Don't group fixtures in JSON files by test function; write "
            "each fixture to its own file. This can be used to increase "
            "the granularity of --verify-fixtures."
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
        "--skip-index",
        action="store_false",
        dest="generate_index",
        default=True,
        help="Skip generating an index file for all produced fixtures.",
    )
    test_group.addoption(
        "--block-gas-limit",
        action="store",
        dest="block_gas_limit",
        default=EnvironmentDefaults.gas_limit,
        type=int,
        help=(
            "Default gas limit ceiling for blocks and tests that attempt "
            f"to consume an entire block's gas. "
            f"(Default: {EnvironmentDefaults.gas_limit})"
        ),
    )
    test_group.addoption(
        "--generate-pre-alloc-groups",
        action="store_true",
        dest="generate_pre_alloc_groups",
        default=False,
        help="Generate pre-allocation groups (phase 1 only).",
    )
    test_group.addoption(
        "--use-pre-alloc-groups",
        action="store_true",
        dest="use_pre_alloc_groups",
        default=False,
        help="Fill tests using existing pre-allocation groups (phase 2 only).",
    )
    test_group.addoption(
        "--generate-all-formats",
        action="store_true",
        dest="generate_all_formats",
        default=False,
        help=(
            "Generate all fixture formats including BlockchainEngineX. "
            "Enables two-phase execution: Phase 1 generates pre-allocation "
            "groups, phase 2 generates all supported fixture formats."
        ),
    )

    optimize_gas_group = parser.getgroup(
        "optimize gas",
        "Arguments defining test gas optimization behavior.",
    )
    optimize_gas_group.addoption(
        "--optimize-gas",
        action="store_true",
        dest="optimize_gas",
        default=False,
        help=(
            "Attempt to optimize gas used in every transaction for filled "
            "tests, then print the minimum gas at which the test still "
            "produces a correct post state and the exact same trace."
        ),
    )
    optimize_gas_group.addoption(
        "--optimize-gas-output",
        action="store",
        dest="optimize_gas_output",
        default=Path("optimize-gas-output.json"),
        type=Path,
        help=(
            "Path to the JSON file that is output to the gas optimization. "
            "Requires `--optimize-gas`."
        ),
    )
    optimize_gas_group.addoption(
        "--optimize-gas-max-gas-limit",
        action="store",
        dest="optimize_gas_max_gas_limit",
        default=None,
        type=int,
        help=(
            "Maximum gas limit for gas optimization, if reached the search "
            "will stop and fail for that test. Requires `--optimize-gas`."
        ),
    )
    optimize_gas_group.addoption(
        "--optimize-gas-post-processing",
        action="store_true",
        dest="optimize_gas_post_processing",
        default=False,
        help=(
            "Post process traces during gas optimization to account for "
            "opcodes that put the current gas in the stack, in order to "
            "remove remaining-gas from the comparison."
        ),
    )

    debug_group = parser.getgroup("debug", "Arguments defining debug behavior")
    debug_group.addoption(
        "--evm-dump-dir",
        "--t8n-dump-dir",
        action="store",
        dest="base_dump_dir",
        default=None,
        help=(
            "Path to dump the transition tool debug output. "
            "Only creates debug output when explicitly specified."
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
    # Register custom markers
    # Modify the block gas limit if specified.
    if config.getoption("block_gas_limit"):
        EnvironmentDefaults.gas_limit = config.getoption("block_gas_limit")

    # Initialize fixture output configuration
    config.fixture_output = FixtureOutput.from_config(  # type: ignore[attr-defined]
        config
    )

    # Initialize filling session
    config.filling_session = FillingSession.from_config(  # type: ignore[attr-defined]
        config
    )

    if is_help_or_collectonly_mode(config):
        return

    try:
        # Check whether the directory exists and is not empty; if --clean is
        # set, it will delete it
        config.fixture_output.create_directories(  # type: ignore[attr-defined]
            is_master=not hasattr(config, "workerinput")
        )
    except ValueError as e:
        pytest.exit(str(e), returncode=pytest.ExitCode.USAGE_ERROR)

    # Register atexit/signal handlers for cleanup (master only, not workers).
    global _fixture_output_dir, _atexit_registered
    global _original_sigint_handler, _original_sigterm_handler
    is_xdist_worker = hasattr(config, "workerinput")
    if not config.fixture_output.is_stdout:  # type: ignore[attr-defined]
        _fixture_output_dir = config.fixture_output.directory  # type: ignore[attr-defined]
        if not _atexit_registered and not is_xdist_worker:
            atexit.register(_merge_on_exit)
            _original_sigint_handler = signal.signal(
                signal.SIGINT, _termination_handler
            )
            _original_sigterm_handler = signal.signal(
                signal.SIGTERM, _termination_handler
            )
            _atexit_registered = True

    if (
        not config.getoption("disable_html")
        and config.getoption("htmlpath") is None
        and config.filling_session.phase_manager.current_phase  # type: ignore[attr-defined]
        != FixtureFillingPhase.PRE_ALLOC_GENERATION
    ):
        config.option.htmlpath = (
            config.fixture_output.directory  # type: ignore[attr-defined]
            / default_html_report_file_path()
        )

    config.gas_optimized_tests = {}  # type: ignore[attr-defined]
    if config.getoption("optimize_gas", False):
        if config.getoption("optimize_gas_post_processing"):
            config.op_mode = (  # type: ignore[attr-defined]
                OpMode.OPTIMIZE_GAS_POST_PROCESSING
            )
        else:
            config.op_mode = OpMode.OPTIMIZE_GAS  # type: ignore[attr-defined]

    config.collect_traces = (  # type: ignore[attr-defined]
        config.getoption("evm_collect_traces")
        or config.getoption("optimize_gas", False)
    )

    # set default for --evm-dump-dir
    if (
        config.collect_traces  # type: ignore[attr-defined]
        and config.getoption("base_dump_dir")
    ) is None:
        config.option.base_dump_dir = "traces"

    # Instantiate the transition tool here to check that the binary path/trace
    # option is valid. This ensures we only raise an error once, if
    # appropriate, instead of for every test.
    evm_bin = config.getoption("evm_bin")
    trace = config.getoption("evm_collect_traces")
    t8n_server_url = config.getoption("t8n_server_url")
    kwargs = {
        "trace": trace,
    }
    if t8n_server_url is not None:
        kwargs["server_url"] = t8n_server_url
    if evm_bin is None:
        assert TransitionTool.default_tool is not None, (
            "No default transition tool found"
        )
        t8n = TransitionTool.default_tool(**kwargs)
    else:
        t8n = TransitionTool.from_binary_path(binary_path=evm_bin, **kwargs)

    if (
        isinstance(config.getoption("numprocesses"), int)
        and config.getoption("numprocesses") > 0
        and not t8n.supports_xdist
    ):
        pytest.exit(
            f"The {t8n.__class__.__name__} t8n tool does not work well "
            "with the xdist plugin; use -n=0.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    config.t8n = t8n  # type: ignore[attr-defined]

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
    config.stash[metadata_key]["Command-line args"] = (
        f"<code>{command_line_args}</code>"
    )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: pytest.Config) -> List[str]:
    """Add lines to pytest's console output header."""
    if is_help_or_collectonly_mode(config):
        return []
    t8n_version = config.stash[metadata_key]["Tools"]["t8n"]
    return [(f"{t8n_version}")]


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(
    report: Any, config: pytest.Config
) -> tuple[str, str, str] | None:
    """
    Modify test results in pytest's terminal output.

    We use this:

    1. To disable test session progress report if we're writing the JSON
    fixtures to stdout to be read by a consume command on stdin. I.e., don't
    write this type of output to the console:
    ```text
    ...x...
    ```
    """
    if config.fixture_output.is_stdout:  # type: ignore[attr-defined]
        return report.outcome, "", report.outcome.upper()
    return None


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> Generator[None, None, None]:
    """
    Modify pytest's terminal summary to emphasize that no tests were ran.

    Emphasize that fixtures have only been filled; they must now be executed to
    actually run the tests.
    """
    del exitstatus

    yield
    if config.fixture_output.is_stdout or hasattr(config, "workerinput"):  # type: ignore[attr-defined]
        return
    stats = terminalreporter.stats
    if "passed" in stats and stats["passed"]:
        # Custom message for Phase 1 (pre-allocation group generation)
        session_instance: FillingSession = config.filling_session  # type: ignore[attr-defined]
        if session_instance.phase_manager.is_pre_alloc_generation:
            # Generate summary stats
            pre_alloc_groups: PreAllocGroups
            if config.pluginmanager.hasplugin("xdist"):
                # Load pre-allocation groups from disk
                pre_alloc_groups = PreAllocGroups.from_folder(
                    config.fixture_output.pre_alloc_groups_folder_path,  # type: ignore[attr-defined]
                    lazy_load=False,
                )
            else:
                assert session_instance.pre_alloc_groups is not None
                pre_alloc_groups = session_instance.pre_alloc_groups

            total_groups = len(pre_alloc_groups.root)
            total_accounts = sum(
                group.pre_account_count for group in pre_alloc_groups.values()
            )

            terminalreporter.write_sep(
                "=",
                f" Phase 1 Complete: Generated {total_groups} pre-alloc "
                f"groups ({total_accounts} total accounts) ",
                bold=True,
                green=True,
            )

        else:
            # Normal message for fixture generation
            # append / to indicate this is a directory
            output_dir = str(config.fixture_output.directory) + "/"  # type: ignore[attr-defined]
            terminalreporter.write_sep(
                "=",
                (
                    f" No tests executed - the test fixtures in "
                    f'"{output_dir}" may now be executed against a client '
                ),
                bold=True,
                yellow=True,
            )


def pytest_metadata(metadata: Any) -> None:
    """Add or remove metadata to/from the pytest report."""
    metadata.pop("JAVA_HOME", None)


def pytest_html_results_table_header(cells: Any) -> None:
    """Customize the table headers of the HTML report table."""
    cells.insert(
        3,
        '<th class="sortable" data-column-type="fixturePath">'
        "JSON Fixture File</th>",
    )
    cells.insert(
        4,
        '<th class="sortable" data-column-type="evmDumpDir">EVM Dump Dir</th>',
    )
    del cells[-1]  # Remove the "Links" column


def pytest_html_results_table_row(report: Any, cells: Any) -> None:
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
                f'<a href="{fixture_path_absolute}" target="_blank">'
                f"{fixture_path_relative}</a>"
            )
            cells.insert(3, f"<td>{fixture_path_link}</td>")
        elif report.failed:
            cells.insert(3, "<td>Fixture unavailable</td>")
        if "evm_dump_dir" in user_props:
            if user_props["evm_dump_dir"] is None:
                cells.insert(
                    4,
                    "<td>For t8n debug info use "
                    "<code>--evm-dump-dir=path --traces</code></td>",
                )
            else:
                evm_dump_dir = user_props.get("evm_dump_dir")
                if evm_dump_dir == "N/A":
                    evm_dump_entry = "N/A"
                else:
                    evm_dump_entry = (
                        f'<a href="{evm_dump_dir}" target="_blank">'
                        f"{evm_dump_dir}</a>"
                    )
                cells.insert(4, f"<td>{evm_dump_entry}</td>")
    del cells[-1]  # Remove the "Links" column


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: Any, call: Any
) -> Generator[None, None, None]:
    """
    Make each test's fixture json path available to the test report via
    user_properties.

    This hook is called when each test is run and a report is being made.
    """
    outcome = yield
    report = outcome.get_result()  # type: ignore[attr-defined]

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
        if hasattr(item.config, "evm_dump_dir") and hasattr(
            item.config, "fixture_format"
        ):
            if item.config.fixture_format in [
                "state_test",
                "blockchain_test",
                "blockchain_test_engine",
                "blockchain_test_sync",
            ]:
                report.user_properties.append(
                    ("evm_dump_dir", item.config.evm_dump_dir)
                )
            else:
                report.user_properties.append(("evm_dump_dir", "N/A"))


def pytest_html_report_title(report: Any) -> None:
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Fill Test Report"


@pytest.fixture(autouse=True, scope="session")
def evm_bin(request: pytest.FixtureRequest) -> Path | None:
    """Return configured evm tool binary path used to run t8n."""
    return request.config.getoption("evm_bin")


@pytest.fixture(autouse=True, scope="session")
def verify_fixtures_bin(request: pytest.FixtureRequest) -> Path | None:
    """
    Return configured evm tool binary path used to run statetest or blocktest.
    """
    return request.config.getoption("verify_fixtures_bin")


@pytest.fixture(autouse=True, scope="session")
def t8n(
    request: pytest.FixtureRequest,
) -> Generator[TransitionTool, None, None]:
    """Return configured transition tool."""
    t8n: TransitionTool = request.config.t8n  # type: ignore
    if not t8n.exception_mapper.reliable:
        t8n_name = t8n.__class__.__name__
        warnings.warn(
            f"The t8n tool being used to fill tests ({t8n_name}) "
            "does not provide reliable exception messages. This may lead to "
            "false positives when writing tests and extra care should be "
            "taken when writing tests that produce exceptions.",
            stacklevel=2,
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
    request: pytest.FixtureRequest,
    do_fixture_verification: bool,
    evm_bin: Path | None,
    verify_fixtures_bin: Path | None,
) -> Generator[FixtureConsumer | None, None, None]:
    """
    Return configured evm binary for executing statetest and blocktest commands
    used to verify generated JSON fixtures.
    """
    if not do_fixture_verification:
        yield None
        return
    reused_evm_bin = False
    if not verify_fixtures_bin and evm_bin:
        verify_fixtures_bin = evm_bin
        reused_evm_bin = True
    if not verify_fixtures_bin:
        pytest.exit(
            "--verify-fixtures requires --evm-bin or --verify-fixtures-bin "
            "to be specified.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    try:
        evm_fixture_verification = FixtureConsumerTool.from_binary_path(
            binary_path=Path(verify_fixtures_bin),
            trace=request.config.collect_traces,  # type: ignore[attr-defined]
        )
    except Exception:
        if reused_evm_bin:
            pytest.exit(
                "The binary specified in --evm-bin could not be recognized "
                "as a known FixtureConsumerTool. Either remove "
                "--verify-fixtures or set --verify-fixtures-bin to a known "
                "fixture consumer binary.",
                returncode=pytest.ExitCode.USAGE_ERROR,
            )
        else:
            pytest.exit(
                "Specified binary in --verify-fixtures-bin could not be "
                "recognized as a known FixtureConsumerTool. Please see "
                "`GethFixtureConsumer` for an example of how a new fixture "
                "consumer can be defined.",
                returncode=pytest.ExitCode.USAGE_ERROR,
            )
    yield evm_fixture_verification


@pytest.fixture(scope="session")
def base_dump_dir(request: pytest.FixtureRequest) -> Path | None:
    """Path to base directory to dump the evm debug output."""
    base_dump_dir_str = request.config.getoption("base_dump_dir")
    if base_dump_dir_str:
        return Path(base_dump_dir_str)
    return None


@pytest.fixture(scope="session")
def fixture_output(request: pytest.FixtureRequest) -> FixtureOutput:
    """Return the fixture output configuration."""
    return request.config.fixture_output  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def is_output_tarball(fixture_output: FixtureOutput) -> bool:
    """Return True if the output directory is a tarball."""
    return fixture_output.is_tarball


@pytest.fixture(scope="session")
def output_dir(fixture_output: FixtureOutput) -> Path:
    """Return directory to store the generated test fixtures."""
    return fixture_output.directory


@pytest.fixture(scope="session", autouse=True)
def create_properties_file(
    request: pytest.FixtureRequest, fixture_output: FixtureOutput
) -> None:
    """
    Create ini file with fixture build properties in the fixture output
    directory.
    """
    if fixture_output.is_stdout:
        return

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
    command_line_args = command_line_args.replace("<code>", "").replace(
        "</code>", ""
    )
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
                f"Fixtures ini file: Skipping metadata key {key} "
                f"with value {val}.",
                stacklevel=2,
            )
    config["environment"] = environment_properties

    ini_filename = fixture_output.metadata_dir / "fixtures.ini"
    with open(ini_filename, "w") as f:
        f.write("; This file describes fixture build properties\n\n")
        config.write(f)


@pytest.fixture(scope="function")
def dump_dir_parameter_level(
    request: pytest.FixtureRequest,
    base_dump_dir: Path | None,
    filler_path: Path,
) -> Path | None:
    """
    Directory to dump evm transition tool debug output on a test parameter
    level.

    Example with --evm-dump-dir=/tmp/evm: ->
    /tmp/evm/shanghai__eip3855_push0__test_push0__test_push0_key_sstore/fork_shangh
    ai/
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


def get_fixture_collection_scope(
    fixture_name: str, config: pytest.Config
) -> str:
    """
    Return the appropriate scope to write fixture JSON files.

    See: https://docs.pytest.org/en/stable/how-to/fixtures.html#dynamic-scope
    """
    del fixture_name

    if config.fixture_output.is_stdout:  # type: ignore[attr-defined]
        return "session"
    if (
        config.fixture_output.single_fixture_per_file  # type: ignore
    ):
        return "function"
    return "module"


@pytest.fixture(autouse=True, scope="module")
def reference_spec(request: pytest.FixtureRequest) -> None | ReferenceSpec:
    """
    Pytest fixture that returns the reference spec defined in a module.

    See `get_ref_spec_from_module`.
    """
    if hasattr(request, "module"):
        return get_ref_spec_from_module(request.module)
    return None


@pytest.fixture(scope=get_fixture_collection_scope)  # type: ignore[arg-type]
def fixture_collector(
    request: pytest.FixtureRequest,
    do_fixture_verification: bool,
    evm_fixture_verification: FixtureConsumer,
    filler_path: Path,
    base_dump_dir: Path | None,
    fixture_output: FixtureOutput,
) -> Generator[FixtureCollector, None, None]:
    """
    Return configured fixture collector instance used for all tests in one test
    module.
    """
    # Dynamically load the 'static_filler' and 'solc' plugins if needed
    if request.config.getoption("fill_static_tests_enabled"):
        request.config.pluginmanager.import_plugin(
            "execution_testing.cli.pytest_commands.plugins.filler.static_filler"
        )
        request.config.pluginmanager.import_plugin(
            "execution_testing.cli.pytest_commands.plugins.solc.solc"
        )

    fixture_collector = FixtureCollector(
        output_dir=fixture_output.directory,
        fill_static_tests=request.config.getoption(
            "fill_static_tests_enabled"
        ),
        single_fixture_per_file=fixture_output.single_fixture_per_file,
        filler_path=filler_path,
        base_dump_dir=base_dump_dir,
        generate_index=request.config.getoption("generate_index"),
    )
    yield fixture_collector
    try:
        # dump_fixtures() only needed for stdout mode
        fixture_collector.dump_fixtures()
        # Verify fixtures for stdout mode only (files are in memory).
        # For file mode, verification happens at session finish after merge.
        if do_fixture_verification and fixture_output.is_stdout:
            fixture_collector.verify_fixture_files(evm_fixture_verification)
    finally:
        # Always close streaming file handles, even on error
        fixture_collector.close_streaming_files()


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
        module_path=Path(node.path),
    )


@pytest.fixture(scope="session")
def commit_hash_or_tag() -> str:
    """Cache the git commit hash or tag for the entire test session."""
    return get_current_commit_hash_or_tag()


@pytest.fixture(scope="function")
def fixture_source_url(
    request: pytest.FixtureRequest,
    commit_hash_or_tag: str,
) -> str:
    """Return URL to the fixture source."""
    if hasattr(request.node, "github_url"):
        return request.node.github_url
    function_line_number = request.function.__code__.co_firstlineno
    module_relative_path = os.path.relpath(
        request.function.__code__.co_filename
    )

    github_url = generate_github_url(
        module_relative_path,
        branch_or_commit_or_tag=commit_hash_or_tag,
        line_number=function_line_number,
    )
    test_module_relative_path = os.path.relpath(request.module.__file__)
    if module_relative_path != test_module_relative_path:
        # This can be the case when the test function's body only contains pass
        # and the entire test logic is implemented as a test generator from the
        # framework.
        test_module_github_url = generate_github_url(
            test_module_relative_path,
            branch_or_commit_or_tag=commit_hash_or_tag,
        )
        github_url += (
            f" called via `{request.node.originalname}()` "
            f"in {test_module_github_url}"
        )
    return github_url


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
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        reference_spec: ReferenceSpec,
        pre: Alloc,
        output_dir: Path,
        dump_dir_parameter_level: Path | None,
        fixture_collector: FixtureCollector,
        test_case_description: str,
        fixture_source_url: str,
        gas_benchmark_value: int,
        fixed_opcode_count: int | None,
        witness_generator: Any,
    ) -> Any:
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
        if hasattr(request.node, "fixture_format"):
            fixture_format = request.node.fixture_format
        else:
            fixture_format = request.param
        assert issubclass(fixture_format, BaseFixture)
        if fork is None:
            assert hasattr(request.node, "fork")
            fork = request.node.fork

        class BaseTestWrapper(cls):  # type: ignore
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                kwargs["t8n_dump_dir"] = dump_dir_parameter_level
                if "pre" not in kwargs:
                    kwargs["pre"] = pre
                if "expected_benchmark_gas_used" not in kwargs:
                    kwargs["expected_benchmark_gas_used"] = gas_benchmark_value
                kwargs["fork"] = fork
                kwargs |= {
                    p: request.getfixturevalue(p)
                    for p in cls_fixture_parameters
                    if p not in kwargs
                }

                super(BaseTestWrapper, self).__init__(*args, **kwargs)
                self._request = request
                self._operation_mode = (
                    request.config.op_mode  # type: ignore[attr-defined]
                )
                if (
                    self._operation_mode == OpMode.OPTIMIZE_GAS
                    or self._operation_mode
                    == OpMode.OPTIMIZE_GAS_POST_PROCESSING
                ):
                    self._gas_optimization_max_gas_limit = (
                        request.config.getoption(
                            "optimize_gas_max_gas_limit", None
                        )
                    )

                # Get the filling session from config
                session: FillingSession = request.config.filling_session  # type: ignore

                # Phase 1: Generate pre-allocation groups
                if session.phase_manager.is_pre_alloc_generation:
                    # Use the original update_pre_alloc_groups method which
                    # returns the groups
                    self.update_pre_alloc_groups(
                        session.pre_alloc_group_builders, request.node.nodeid
                    )
                    return  # Skip fixture generation in phase 1

                # Phase 2: Use pre-allocation groups (only for
                # BlockchainEngineXFixture)
                pre_alloc_hash = None
                if (
                    FixtureFillingPhase.PRE_ALLOC_GENERATION
                    in fixture_format.format_phases
                ):
                    pre_alloc_hash = self.compute_pre_alloc_group_hash()
                    group = session.get_pre_alloc_group(pre_alloc_hash)
                    self.pre = group.pre
                try:
                    fixture = self.generate(
                        t8n=t8n,
                        fixture_format=fixture_format,
                    )
                finally:
                    if (
                        request.config.op_mode  # type: ignore[attr-defined]
                        == OpMode.OPTIMIZE_GAS
                        or request.config.op_mode  # type: ignore[attr-defined]
                        == OpMode.OPTIMIZE_GAS_POST_PROCESSING
                    ):
                        gas_optimized_tests = (
                            request.config.gas_optimized_tests  # type: ignore
                        )
                        assert gas_optimized_tests is not None
                        # Force adding something to the list, even if it's
                        # None, to keep track of failed tests in the output
                        # file.
                        gas_optimized_tests[request.node.nodeid] = (
                            self._gas_optimization
                        )

                # Post-process for Engine X format (add pre_hash and state
                # diff)
                if (
                    FixtureFillingPhase.PRE_ALLOC_GENERATION
                    in fixture_format.format_phases
                    and pre_alloc_hash is not None
                ):
                    fixture.pre_hash = pre_alloc_hash

                    # Calculate state diff for efficiency
                    if (
                        hasattr(fixture, "post_state")
                        and fixture.post_state is not None
                    ):
                        group = session.get_pre_alloc_group(pre_alloc_hash)
                        fixture.post_state_diff = calculate_post_state_diff(
                            fixture.post_state, group.pre
                        )

                fixture.fill_info(
                    t8n.version(),
                    test_case_description,
                    fixture_source_url=fixture_source_url,
                    ref_spec=reference_spec,
                    _info_metadata=t8n._info_metadata,
                )

                # Generate witness data if witness functionality is enabled via
                # the witness plugin
                if witness_generator is not None:
                    witness_generator(fixture)

                fixture_path = fixture_collector.add_fixture(
                    node_to_test_info(request.node),
                    fixture,
                )

                # NOTE: Use str for compatibility with pytest-dist
                request.node.config.fixture_path_absolute = str(
                    fixture_path.absolute()
                )
                request.node.config.fixture_path_relative = str(
                    fixture_path.relative_to(output_dir)
                )
                request.node.config.fixture_format = fixture_format.format_name

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

    NOTE: The static test filler does NOT use this hook. See
    FillerFile.collect() in ./static_filler.py for more details.
    """
    session: FillingSession = metafunc.config.filling_session  # type: ignore[attr-defined]
    for test_type in BaseTest.spec_types.values():
        if test_type.pytest_parameter_name() in metafunc.fixturenames:
            parameters = []
            for i, format_with_or_without_label in enumerate(
                test_type.supported_fixture_formats
            ):
                if not session.should_generate_format(
                    format_with_or_without_label
                ):
                    continue
                parameter = labeled_format_parameter_set(
                    format_with_or_without_label
                )
                if i > 0:
                    parameter.marks.append(pytest.mark.derived_test)  # type: ignore
                parameters.append(parameter)
            metafunc.parametrize(
                [test_type.pytest_parameter_name()],
                parameters,
                scope="function",
                indirect=True,
            )


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item | pytest.Function]
) -> None:
    """
    Remove pre-Paris tests parametrized to generate hive type fixtures; these
    can't be used in the Hive Pyspec Simulator.

    Replaces the test ID for state tests that use a transition fork with the
    base fork.

    These can't be handled in this plugins pytest_generate_tests() as the fork
    parametrization occurs in the forks plugin.
    """
    del config

    items_for_removal = []
    for i, item in enumerate(items):
        item.name = item.name.strip().replace(" ", "-")
        params: Dict[str, Any] | None = None
        if isinstance(item, pytest.Function):
            params = item.callspec.params
        elif hasattr(item, "params"):
            params = item.params
        if not params or "fork" not in params or params["fork"] is None:
            items_for_removal.append(i)
            continue
        fork: Fork = params["fork"]
        spec_type, fixture_format = get_spec_format_for_item(params)
        if isinstance(fixture_format, NotSetType):
            items_for_removal.append(i)
            continue
        assert issubclass(fixture_format, BaseFixture)
        if not fixture_format.supports_fork(fork):
            items_for_removal.append(i)
            continue

        markers = list(item.iter_markers())

        # Both the fixture format itself and the spec filling it have a chance
        # to veto the filling of a specific format.
        if fixture_format.discard_fixture_format_by_marks(fork, markers):
            items_for_removal.append(i)
            continue
        if spec_type.discard_fixture_format_by_marks(
            fixture_format, fork, markers
        ):
            items_for_removal.append(i)
            continue
        for marker in markers:
            if marker.name == "fill":
                for mark in marker.args:
                    item.add_marker(mark)
        if "yul" in item.fixturenames:  # type: ignore
            item.add_marker(pytest.mark.yul_test)

        # Update test ID for state tests that use a transition fork
        if fork in get_transition_forks():
            has_state_test = any(
                marker.name == "state_test" for marker in markers
            )
            has_valid_transition = any(
                marker.name == "valid_at_transition_to" for marker in markers
            )
            if has_state_test and has_valid_transition:
                base_fork = get_transition_fork_predecessor(fork)
                item._nodeid = item._nodeid.replace(
                    f"fork_{fork.name()}",
                    f"fork_{base_fork.name()}",
                )

    for i in reversed(items_for_removal):
        items.pop(i)

    # Schedule slow-marked tests first (Longest Processing Time First).
    # Workers each grab the next test from the queue, so slow tests get
    # distributed across workers and finish before the fast-test tail.
    slow_items = []
    normal_items = []
    for item in items:
        if item.get_closest_marker("slow") is not None:
            slow_items.append(item)
        else:
            normal_items.append(item)
    if slow_items:
        items[:] = slow_items + normal_items


def _verify_fixtures_post_merge(
    config: pytest.Config, output_dir: Path
) -> None:
    """
    Verify fixtures after merge if verification is enabled.

    Called from pytest_sessionfinish after partial files are merged into
    final JSON fixtures. Runs evm statetest/blocktest on each fixture.
    """
    if not config.getoption("verify_fixtures"):
        return

    # Get the verification binary (same logic as evm_fixture_verification)
    verify_fixtures_bin = config.getoption("verify_fixtures_bin")
    if not verify_fixtures_bin:
        verify_fixtures_bin = config.getoption("evm_bin")
    if not verify_fixtures_bin:
        return

    try:
        evm_verification = FixtureConsumerTool.from_binary_path(
            binary_path=Path(verify_fixtures_bin),
            trace=getattr(config, "collect_traces", False),
        )
    except Exception:
        # Binary not recognized, skip verification (error already shown
        # during fixture setup if --verify-fixtures was used)
        return

    # Map directory names to fixture format classes
    dir_to_format: dict[str, type[BaseFixture]] = {
        StateFixture.output_base_dir_name(): StateFixture,
        BlockchainFixture.output_base_dir_name(): BlockchainFixture,
        BlockchainEngineFixture.output_base_dir_name(): (
            BlockchainEngineFixture
        ),
    }

    # Find all JSON fixture files and verify them
    for json_file in output_dir.rglob("*.json"):
        # Determine fixture format from top-level directory
        relative_path = json_file.relative_to(output_dir)
        if not relative_path.parts:
            continue

        top_dir = relative_path.parts[0]
        fixture_format = dir_to_format.get(top_dir)
        if fixture_format is None:
            continue

        if evm_verification.can_consume(fixture_format):
            evm_verification.consume_fixture(
                fixture_format,
                json_file,
                fixture_name=None,
                debug_output_path=None,
            )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """
    Perform session finish tasks.

    - Save pre-allocation groups (phase 1)
    - Remove any lock files that may have been created.
    - Generate index file for all produced fixtures.
    - Create tarball of the output directory if the output is a tarball.
    """
    del exitstatus

    # Save pre-allocation groups after phase 1
    fixture_output: FixtureOutput = session.config.fixture_output  # type: ignore[attr-defined]
    session_instance: FillingSession = session.config.filling_session  # type: ignore[attr-defined]
    if session_instance.phase_manager.is_pre_alloc_generation:
        session_instance.save_pre_alloc_groups()
        return

    if session.config.getoption("optimize_gas", False):
        output_file = Path(session.config.getoption("optimize_gas_output"))
        lock_file_path = output_file.with_suffix(".lock")
        assert hasattr(session.config, "gas_optimized_tests")
        gas_optimized_tests: Dict[str, int] = (
            session.config.gas_optimized_tests
        )
        with FileLock(lock_file_path):
            if output_file.exists():
                gas_optimized_tests = (
                    json.loads(output_file.read_text()) | gas_optimized_tests
                )
            output_file.write_text(
                json.dumps(gas_optimized_tests, indent=2, sort_keys=True)
            )

    if xdist.is_xdist_worker(session):
        return

    if fixture_output.is_stdout or is_help_or_collectonly_mode(session.config):
        return

    # Merge partial fixture files from all workers into final JSON files
    merge_partial_fixture_files(fixture_output.directory)

    # Remove any lock files that may have been created.
    for file in fixture_output.directory.rglob("*.lock"):
        file.unlink()

    # Verify fixtures after merge if verification is enabled
    _verify_fixtures_post_merge(session.config, fixture_output.directory)

    # Generate index file for all produced fixtures by merging partial indexes.
    # Only merge if partial indexes were actually written (i.e., tests produced
    # fixtures). When no tests are filled (e.g., all skipped), no partial
    # indexes exist and merge_partial_indexes should not be called.
    if (
        session.config.getoption("generate_index")
        and not session_instance.phase_manager.is_pre_alloc_generation
    ):
        meta_dir = fixture_output.directory / ".meta"
        if meta_dir.exists() and any(meta_dir.glob("partial_index*.jsonl")):
            merge_partial_indexes(fixture_output.directory, quiet_mode=True)

    # Create tarball of the output directory if the output is a tarball.
    fixture_output.create_tarball()
