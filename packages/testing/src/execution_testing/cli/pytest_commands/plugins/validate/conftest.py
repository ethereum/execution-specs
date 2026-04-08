"""
A pytest plugin that configures the validate command to run test fixtures
against client "direct" consumer interfaces.

Reads client configuration from validate.toml (falling back to
consume-direct.toml) and creates fixture consumer instances based on the
--validate-type and --validate-clients options injected by the validate
click subcommands.
"""

import argparse
import json
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Generator, List

import pytest
import rich

from execution_testing.base_types import to_json
from execution_testing.cli.gen_index import (
    generate_fixtures_index,
)
from execution_testing.cli.pytest_commands.plugins.consume.consume import (
    CACHED_DOWNLOADS_DIRECTORY,
    FixturesSource,
    SimLimitBehavior,
    default_html_report_file_path,
    default_input,
)
from execution_testing.client_clis.ethereum_cli import EthereumCLI
from execution_testing.client_clis.fixture_consumer_tool import (
    FixtureConsumerTool,
)
from execution_testing.fixtures import (
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainEngineXFixture,
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)
from execution_testing.fixtures.consume import (
    IndexFile,
    TestCaseIndexFile,
    TestCaseStream,
    TestCases,
)
from execution_testing.fixtures.file import Fixtures
from execution_testing.forks import (
    get_forks,
    get_relative_fork_markers,
    get_transition_forks,
)
from execution_testing.tools.utility.versioning import (
    get_current_commit_hash_or_tag,
)


class CollectOnlyCLI(EthereumCLI):
    """A dummy CLI for use with `--collect-only`."""

    def __init__(self) -> None:  # noqa: D107
        pass


class CollectOnlyFixtureConsumer(
    FixtureConsumerTool,
    CollectOnlyCLI,
    fixture_formats=list(BaseFixture.formats.values()),
):
    """A dummy fixture consumer for use with `--collect-only`."""

    def consume_fixture(
        self, *args: Any, **kwargs: Any
    ) -> None:  # noqa: D102
        pass


NAME_MAP = {
    "GethFixtureConsumer": "geth",
    "ErigonFixtureConsumer": "erigon",
    "BesuFixtureConsumer": "besu",
    "NethtestFixtureConsumer": "nethermind",
    "RethFixtureConsumer": "reth",
    "EthrexFixtureConsumer": "ethrex",
    "NimbusFixtureConsumer": "nimbus",
}

RECOMMENDED_WORKERS: dict[str, int] = {
    "GethFixtureConsumer": 8,
    "ErigonFixtureConsumer": 8,
    "BesuFixtureConsumer": 8,
    "NethtestFixtureConsumer": 4,
    "EthrexFixtureConsumer": 8,
}

RECOMMENDED_N: dict[str, int] = {
    "RethFixtureConsumer": 2,
}


def _build_client_class_map() -> dict[str, type]:
    """Build mapping from client name to consumer class."""
    from execution_testing.client_clis.clis.besu import (
        BesuFixtureConsumer,
    )
    from execution_testing.client_clis.clis.erigon import (
        ErigonFixtureConsumer,
    )
    from execution_testing.client_clis.clis.ethrex import (
        EthrexFixtureConsumer,
    )
    from execution_testing.client_clis.clis.geth import (
        GethFixtureConsumer,
    )
    from execution_testing.client_clis.clis.nethermind import (
        NethtestFixtureConsumer,
    )
    from execution_testing.client_clis.clis.nimbus import (
        NimbusFixtureConsumer,
    )
    from execution_testing.client_clis.clis.reth import (
        RethFixtureConsumer,
    )

    return {
        "geth": GethFixtureConsumer,
        "go-ethereum": GethFixtureConsumer,
        "erigon": ErigonFixtureConsumer,
        "besu": BesuFixtureConsumer,
        "nethermind": NethtestFixtureConsumer,
        "reth": RethFixtureConsumer,
        "ethrex": EthrexFixtureConsumer,
        "nimbus": NimbusFixtureConsumer,
    }


CLIENT_CLASS_MAP: dict[str, type] = _build_client_class_map()


def _resolve_config_path() -> Path | None:
    """Find validate.toml or fall back to consume-direct.toml."""
    for name in ("validate.toml", "consume-direct.toml"):
        path = Path.cwd() / name
        if path.exists():
            return path
    return None


def pytest_addoption(parser: pytest.Parser) -> None:  # noqa: D103
    fixtures_group = parser.getgroup(
        "fixtures",
        "Arguments related to fixture input",
    )
    fixtures_group.addoption(
        "--input",
        action="store",
        dest="fixtures_source",
        default=None,
        help=(
            "Specify the JSON test fixtures source. Can be a "
            "local directory, a URL pointing to a "
            "fixtures.tar.gz archive, a release name and "
            "version in the form of `NAME@v1.2.3` (`stable` "
            "and `develop` are valid release names, and "
            "`latest` is a valid version), or the special "
            "keyword 'stdin'. Defaults to the following local "
            f"directory: '{default_input()}'."
        ),
    )
    fixtures_group.addoption(
        "--cache-folder",
        action="store",
        dest="fixture_cache_folder",
        default=CACHED_DOWNLOADS_DIRECTORY,
        help=(
            "Specify the path where the downloaded fixtures "
            "are cached. Defaults to the following directory: "
            f"'{CACHED_DOWNLOADS_DIRECTORY}'."
        ),
    )
    fixtures_group.addoption(
        "--no-html",
        action="store_true",
        dest="disable_html",
        default=False,
        help=(
            "Don't generate an HTML test report (in the "
            "output directory). The --html flag can be used "
            "to specify a different path."
        ),
    )
    fixtures_group.addoption(
        "--sim.limit",
        action="store",
        dest="sim_limit",
        type=SimLimitBehavior.from_string,
        default=SimLimitBehavior(".*"),
        help=(
            "Filter tests by either a regex pattern or a "
            "literal test case ID. To match a test case by "
            "its exact ID, prefix the ID with `id:`. "
            "Without the `id:` prefix, the argument is "
            "interpreted as a Python regex pattern. To see "
            "which test cases are matched without executing "
            "them, prefix with `collectonly:`."
        ),
    )
    validate_group = parser.getgroup(
        "validate",
        "Arguments related to validating fixtures against a client",
    )
    validate_group.addoption(
        "--client",
        action="append",
        dest="_client_help_only",
        default=[],
        help="Client name (e.g. geth, besu). Required. Can be repeated.",
    )
    validate_group.addoption(
        "--validate-type",
        action="store",
        dest="validate_type",
        type=str,
        default=None,
        choices=["state", "block", "engine"],
        help=argparse.SUPPRESS,
    )
    validate_group.addoption(
        "--validate-clients",
        action="store",
        dest="validate_clients",
        type=str,
        default="",
        help=argparse.SUPPRESS,
    )
    validate_group.addoption(
        "--no-exception-check",
        action="store_true",
        dest="no_exception_check",
        default=False,
        help=(
            "Skip exception matching (useful for clients that "
            "don't report errors)."
        ),
    )
    validate_group.addoption(
        "--bin-workers",
        action="store",
        dest="num_workers",
        type=int,
        default=1,
        help=(
            "Number of parallel workers passed to the client "
            "binary's --workers flag."
        ),
    )
    validate_group.addoption(
        "--traces",
        action="store_true",
        dest="consumer_collect_traces",
        default=False,
        help=(
            "Collect traces of the execution information from "
            "the fixture consumer tool."
        ),
    )
    debug_group = parser.getgroup(
        "debug", "Arguments defining debug behavior"
    )
    debug_group.addoption(
        "--dump-dir",
        action="store",
        dest="base_dump_dir",
        type=Path,
        default=None,
        help="Path to dump the fixture consumer tool debug output.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:  # noqa: D103
    validate_type = config.getoption("validate_type", None)

    # Health subcommand does not need client/fixture setup
    if validate_type is None:
        return

    # --- Fixture source loading ---
    fixtures_source: FixturesSource
    if config.option.fixtures_source is None:
        fixtures_source = FixturesSource(
            input_option=default_input(),
            path=Path(default_input()),
        )
    else:
        fixtures_source = FixturesSource.from_input(
            config.option.fixtures_source,
            Path(config.option.fixture_cache_folder),
        )
    config.fixtures_source = fixtures_source  # type: ignore[attr-defined]
    config.fixture_source_flags = [  # type: ignore[attr-defined]
        "--input",
        fixtures_source.input_option,
    ]

    if fixtures_source.is_stdin:
        config.test_cases = TestCases.from_stream(  # type: ignore[attr-defined]
            sys.stdin
        )
    else:
        index_file = (
            fixtures_source.path / ".meta" / "index.json"
        )
        index_file.parent.mkdir(parents=True, exist_ok=True)
        if not index_file.exists():
            rich.print(
                f"Generating index file "
                f"[bold cyan]{index_file}[/]..."
            )
            generate_fixtures_index(
                fixtures_source.path,
                quiet_mode=False,
                force_flag=False,
            )
        index = IndexFile.model_validate_json(
            index_file.read_text()
        )
        config.test_cases = index.test_cases  # type: ignore[attr-defined]

        for fixture_format in BaseFixture.formats.values():
            config.addinivalue_line(
                "markers",
                f"{fixture_format.format_name}: "
                f"Tests in `{fixture_format.format_name}` "
                f"format ",
            )
        all_forks = {
            fork
            for fork in set(get_forks()) | get_transition_forks()
            if not fork.ignore()
        }
        all_forks.update(getattr(index, "forks", []))
        for fork in all_forks:
            config.addinivalue_line(
                "markers",
                f"{fork}: Tests for the {fork} fork",
            )

    if config.option.sim_limit:
        if config.option.dest_regex != ".*":
            pytest.exit(
                "Both the --sim.limit (via env var?) and the "
                "--regex flags are set. Please only set one "
                "of them."
            )
        config.option.dest_regex = (
            config.option.sim_limit.pattern
        )
        if config.option.sim_limit.collectonly:
            config.option.collectonly = True
            config.option.verbose = -1

    if config.option.collectonly or config.option.markers:
        return
    if (
        not config.getoption("disable_html")
        and config.getoption("htmlpath") is None
    ):
        config.option.htmlpath = (
            config.fixtures_source.path  # type: ignore[attr-defined]
            / default_html_report_file_path()
        )

    # Resolve config file
    config_path = _resolve_config_path()
    if not config_path and not config.option.collectonly:
        warnings.warn(
            "No validate.toml or consume-direct.toml found. "
            "Run `validate health` to check client binaries.",
            stacklevel=1,
        )

    # Parse client names from the hidden option
    clients_str = config.getoption("validate_clients", "")
    CLIENT_ALIASES = {"go-ethereum": "geth"}
    client_names = [
        CLIENT_ALIASES.get(c.strip(), c.strip())
        for c in clients_str.split(",") if c.strip()
    ]

    # Help passthrough — skip client setup
    if "__help__" in client_names:
        return

    if not client_names and not config.option.collectonly:
        pytest.exit(
            "No clients specified. Use --client <name> to "
            "specify a fixture consumer."
        )

    # Load TOML config
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    toml_config: dict[str, dict[str, str]] = {}
    if config_path:
        with open(config_path, "rb") as f:
            toml_config = tomllib.load(f)

    # Resolve client names to binary paths and configs
    bin_paths: list[Path] = []
    client_configs: dict[str, dict[str, str]] = {}

    for name in client_names:
        entry = toml_config.get(name, {})
        bin_str = entry.get("bin", "")
        if not bin_str:
            config_name = (
                config_path.name if config_path else "validate.toml"
            )
            pytest.exit(
                f"Client '{name}' not configured in {config_name}."
            )
        resolved = Path(bin_str).expanduser()
        bin_paths.append(resolved)
        client_configs[str(resolved)] = {
            **entry,
            "_client_name": name,
        }

    # Set supported fixture formats based on validate type
    type_to_formats = {
        "state": [StateFixture],
        "block": [BlockchainFixture],
        "engine": [BlockchainEngineFixture],
    }
    config.supported_fixture_formats = type_to_formats[validate_type]  # type: ignore[attr-defined]

    num_workers = config.getoption("num_workers", 1)

    # Create fixture consumers
    fixture_consumers = []
    for bin_path in bin_paths:
        entry = client_configs.get(str(bin_path), {})

        # Resolve per-type binary overrides from TOML config
        extra_kwargs: dict[str, Any] = {}
        state_bin_str = entry.get("state-bin", "")
        if state_bin_str:
            extra_kwargs["state_binary"] = (
                Path(state_bin_str).expanduser()
            )
        block_bin_str = entry.get("block-bin", "")
        if block_bin_str:
            extra_kwargs["block_binary"] = (
                Path(block_bin_str).expanduser()
            )
        engine_bin_str = entry.get("engine-bin", "")
        if engine_bin_str:
            extra_kwargs["engine_binary"] = (
                Path(engine_bin_str).expanduser()
            )

        client_name = entry.get("_client_name", "")
        consumer = None

        # Directly instantiate the right class to avoid ambiguous
        # auto-detection (e.g. erigon and geth both use `evm`).
        if client_name and client_name in CLIENT_CLASS_MAP:
            cls = CLIENT_CLASS_MAP[client_name]
            try:
                consumer = cls(
                    binary=bin_path,
                    trace=config.getoption(
                        "consumer_collect_traces"
                    ),
                    **extra_kwargs,
                )
            except Exception:
                pass

        if consumer is None:
            try:
                consumer = FixtureConsumerTool.from_binary_path(
                    binary_path=bin_path,
                    trace=config.getoption(
                        "consumer_collect_traces"
                    ),
                    **extra_kwargs,
                )
            except Exception:
                from execution_testing.client_clis.clis.nethermind import (
                    NethtestFixtureConsumer,
                )

                try:
                    consumer = (
                        NethtestFixtureConsumer.from_binary_path(
                            binary_path=bin_path,
                            trace=config.getoption(
                                "consumer_collect_traces"
                            ),
                        )
                    )
                except Exception:
                    raise Exception(
                        f"Unknown CLI binary: {bin_path}. "
                        f"Could not detect as native binary "
                        f"or dotnet project."
                    )

        # Check that consumer supports the requested format(s)
        supported = set(getattr(consumer, "fixture_formats", []))
        requested = set(
            config.supported_fixture_formats  # type: ignore[attr-defined]
        )
        unsupported = requested - supported
        if unsupported:
            friendly = NAME_MAP.get(
                type(consumer).__name__, type(consumer).__name__
            )
            unsupported_names = ", ".join(
                f.format_name for f in unsupported
            )
            supported_names = ", ".join(
                f.format_name for f in supported
            )
            hints = []
            if (
                BlockchainEngineFixture in unsupported
                and BlockchainEngineXFixture in supported
            ):
                hints.append(
                    f"Use --type enginex instead of --type engine "
                    f"({friendly} needs enginex as engine is "
                    f"too slow)."
                )
            if (
                BlockchainEngineXFixture in unsupported
                and BlockchainEngineFixture in supported
            ):
                hints.append(
                    "Use --type engine instead of --type enginex."
                )
            hint_str = (
                " " + " ".join(hints) if hints else ""
            )
            pytest.exit(
                f"{friendly} does not support: "
                f"{unsupported_names}. "
                f"Supported: {supported_names}.{hint_str}"
            )
        fixture_consumers.append(consumer)

    if config.option.markers:
        return
    elif not fixture_consumers and config.option.collectonly:
        warnings.warn(
            (
                "No fixture consumer binaries provided; using a "
                "dummy consumer for collect-only; all possible "
                "fixture formats will be collected."
            ),
            stacklevel=1,
        )
        fixture_consumers = [CollectOnlyFixtureConsumer()]
    elif not fixture_consumers:
        pytest.exit(
            "No fixture consumer binaries provided; use "
            "--client <name> to specify a fixture consumer."
        )

    # Block -n for clients with top-level caching
    no_xdist_reasons: dict[str, tuple[str, str]] = {
        "BesuFixtureConsumer": (
            "JVM startup is expensive per xdist worker",
            "Use --bin-workers instead. "
            "Recommended: --bin-workers 8.",
        ),
        "NethtestFixtureConsumer": (
            "dotnet startup is expensive per xdist worker",
            "Use --bin-workers instead. "
            "Recommended: --bin-workers 4.",
        ),
    }
    n_workers = config.getoption("numprocesses", None)
    if n_workers and n_workers > 0:
        for consumer in fixture_consumers:
            cls_name = type(consumer).__name__
            xdist_entry = no_xdist_reasons.get(cls_name)
            if xdist_entry:
                friendly = NAME_MAP.get(cls_name, cls_name)
                reason, suggestion = xdist_entry
                pytest.exit(
                    f"{friendly} does not support -n (xdist): "
                    f"{reason}. {suggestion}"
                )

    # Reject --bin-workers for clients that don't support it
    no_workers_clients: dict[str, tuple[str, str]] = {
        "RethFixtureConsumer": (
            "parallelism is handled internally by rayon",
            "Use -n instead. Recommended: -n 2.",
        ),
        "NimbusFixtureConsumer": (
            "--workers is not yet implemented",
            "-n doesn't add much. Recommended: keep default (-n 1).",
        ),
    }
    user_set_workers = "--bin-workers" in sys.argv
    if user_set_workers and num_workers != 1:
        for consumer in fixture_consumers:
            cls_name = type(consumer).__name__
            entry = no_workers_clients.get(cls_name)
            if entry:
                reason, suggestion = entry
                friendly = NAME_MAP.get(cls_name, cls_name)
                pytest.exit(
                    f"{friendly} does not support "
                    f"--bin-workers ({reason}). "
                    f"{suggestion}"
                )

    # Auto-set -n for clients that use xdist
    user_set_n = "-n" in sys.argv
    if not user_set_n:
        for consumer in fixture_consumers:
            rec_n = RECOMMENDED_N.get(type(consumer).__name__)
            if rec_n:
                config.option.numprocesses = rec_n
                break

    # Auto-set recommended --bin-workers
    if not user_set_workers and num_workers == 1:
        for consumer in fixture_consumers:
            rec = RECOMMENDED_WORKERS.get(
                type(consumer).__name__
            )
            if rec:
                num_workers = rec
                break

    no_exception_check = config.getoption(
        "no_exception_check", False
    )
    for consumer in fixture_consumers:
        consumer.workers = num_workers  # type: ignore[attr-defined]
        consumer.exception_check = not no_exception_check  # type: ignore[attr-defined]

    config.fixture_consumers = fixture_consumers  # type: ignore[attr-defined]


def pytest_html_report_title(report: Any) -> None:
    """Set the HTML report title (pytest-html plugin)."""
    report.title = "Validate Test Report"


def pytest_report_header(
    config: pytest.Config,
) -> List[str]:
    """Add fixtures source and client info to report header."""
    lines: List[str] = [
        f"validate ref: {get_current_commit_hash_or_tag()}",
    ]
    source = getattr(config, "fixtures_source", None)
    if source is not None:
        lines.append(f"fixtures: {source.path}")
        if not source.is_local and not source.is_stdin:
            lines.append(f"fixtures url: {source.url}")
            if source.release_page:
                lines.append(
                    f"fixtures release: {source.release_page}"
                )

    consumers = getattr(config, "fixture_consumers", [])
    if not consumers:
        return lines

    cli_workers = config.getoption("num_workers", 1)
    tw = config.get_terminal_writer()

    for consumer in consumers:
        cls_name = type(consumer).__name__
        friendly = NAME_MAP.get(cls_name, cls_name)
        actual_workers = getattr(consumer, "workers", cli_workers)
        auto = (
            " (auto)"
            if cli_workers == 1 and actual_workers != 1
            else ""
        )
        tw.write(
            f"client: {friendly} "
            f"(bin-workers: {actual_workers}{auto})\n",
            yellow=True,
        )

    n_workers = config.getoption("numprocesses", None)
    user_set_n = "-n" in sys.argv
    if n_workers:
        auto_n = " (auto)" if not user_set_n else ""
        tw.write(
            f"xdist workers: {n_workers}{auto_n}\n",
            yellow=True,
        )

    tw.write(
        "Note: initial binary startup may take a moment "
        "(especially JVM/dotnet clients)\n",
        yellow=True,
    )
    return lines


@pytest.fixture(scope="function")
def test_dump_dir(
    request: pytest.FixtureRequest,
    fixture_path: Path,
    fixture_name: str,
) -> Path | None:
    """The directory to write evm debug output to."""
    base_dump_dir = request.config.getoption("base_dump_dir")
    if not base_dump_dir:
        return None
    if len(fixture_name) > 142:
        fixture_name = (
            fixture_name[:70] + "..." + fixture_name[-70:]
        )
    return (
        base_dump_dir
        / fixture_path.stem
        / fixture_name.replace("/", "-")
    )


@pytest.fixture
def fixture_path(
    test_case: TestCaseIndexFile | TestCaseStream,
    fixtures_source: FixturesSource,
) -> Generator[Path, None, None]:
    """
    Path to the current JSON fixture file.

    If the fixture source is stdin, the fixture is written to a
    temporary json file.
    """
    if fixtures_source.is_stdin:
        assert isinstance(test_case, TestCaseStream)
        temp_dir = tempfile.TemporaryDirectory()
        fixture_path = (
            Path(temp_dir.name)
            / f"{test_case.id.replace('/', '_')}.json"
        )
        fixtures = Fixtures({test_case.id: test_case.fixture})
        with open(fixture_path, "w") as f:
            json.dump(to_json(fixtures), f, indent=4)
        yield fixture_path
        temp_dir.cleanup()
    else:
        assert isinstance(test_case, TestCaseIndexFile)
        yield fixtures_source.path / test_case.json_path


@pytest.fixture(scope="function")
def fixture_name(
    test_case: TestCaseIndexFile | TestCaseStream,
) -> str:
    """Name of the current fixture."""
    return test_case.id


@pytest.fixture(scope="session")
def fixtures_source(
    request: pytest.FixtureRequest,
) -> FixturesSource:
    """Return the resolved fixtures source."""
    return request.config.fixtures_source  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def fixture_source_flags(
    request: pytest.FixtureRequest,
) -> List[str]:
    """Return the input flags used to specify the fixture source."""
    return request.config.fixture_source_flags  # type: ignore[attr-defined]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize test cases and fixture consumers."""
    # Parametrize test_case from loaded fixtures index
    if "test_case" in metafunc.fixturenames:
        if not hasattr(metafunc.config, "test_cases"):
            return
        test_cases = metafunc.config.test_cases  # type: ignore[attr-defined]
        supported: List[FixtureFormat] = getattr(
            metafunc.config, "supported_fixture_formats", []
        )
        param_list = []
        for test_case in test_cases:
            if test_case.format not in supported:
                continue
            fork_markers = get_relative_fork_markers(
                test_case.fork, strict_mode=False
            )
            marks = [
                getattr(pytest.mark, m) for m in fork_markers
            ] + [
                getattr(
                    pytest.mark, test_case.format.format_name
                )
            ]
            param_list.append(
                pytest.param(
                    test_case, id=test_case.id, marks=marks
                )
            )
        metafunc.parametrize("test_case", param_list)

    # Parametrize fixture_consumer from configured clients
    if "fixture_consumer" in metafunc.fixturenames:
        consumers = getattr(
            metafunc.config, "fixture_consumers", None
        )
        if consumers is None:
            return
        metafunc.parametrize(
            "fixture_consumer",
            (
                pytest.param(
                    fixture_consumer,
                    id=str(
                        fixture_consumer.__class__.__name__
                    ),
                )
                for fixture_consumer in consumers
            ),
        )
