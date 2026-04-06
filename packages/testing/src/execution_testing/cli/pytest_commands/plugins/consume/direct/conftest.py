"""
A pytest plugin that configures the consume command to act as a test runner for
"direct" client fixture consumer interfaces.

For example, via go-ethereum's `evm blocktest` or `evm statetest` commands.
"""

import json
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Generator

import pytest

from execution_testing.base_types import to_json
from execution_testing.cli.pytest_commands.plugins.consume.consume import (
    FixturesSource,
)
from execution_testing.client_clis.ethereum_cli import EthereumCLI
from execution_testing.client_clis.fixture_consumer_tool import (
    FixtureConsumerTool,
)
from execution_testing.fixtures import (
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainFixture,
    StateFixture,
)
from execution_testing.fixtures.consume import (
    TestCaseIndexFile,
    TestCaseStream,
)
from execution_testing.fixtures.file import Fixtures


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

    def consume_fixture(self, *args: Any, **kwargs: Any) -> None:  # noqa: D102
        pass


def pytest_addoption(parser: pytest.Parser) -> None:  # noqa: D103
    consume_group = parser.getgroup(
        "consume_direct",
        "Arguments related to consuming fixtures via a client",
    )

    consume_group.addoption(
        "--bin",
        action="append",
        dest="fixture_consumer_bin",
        type=Path,
        default=[],
        help=(
            "Path to a client binary. Can be used multiple times. "
            "Mutually exclusive with --client."
        ),
    )
    consume_group.addoption(
        "--client",
        action="append",
        dest="client_names",
        default=[],
        help=(
            "Client name (e.g. geth, besu, nethermind). Resolves binary "
            "path from consume-direct.toml. Can be used multiple times."
        ),
    )
    consume_group.addoption(
        "--traces",
        action="store_true",
        dest="consumer_collect_traces",
        default=False,
        help=(
            "Collect traces of the execution information from the fixture "
            "consumer tool."
        ),
    )
    consume_group.addoption(
        "--type",
        action="store",
        dest="fixture_type",
        type=str,
        default=None,
        choices=["state", "block", "engine", "all"],
        help=(
            "Fixture type to run. Required for `consume direct`. "
            "One of: state, block, engine, all."
        ),
    )
    consume_group.addoption(
        "--bin-workers",
        action="store",
        dest="num_workers",
        type=int,
        default=1,
        help="Number of parallel workers passed to the client binary's --workers flag.",
    )
    debug_group = parser.getgroup("debug", "Arguments defining debug behavior")
    debug_group.addoption(
        "--dump-dir",
        action="store",
        dest="base_dump_dir",
        type=Path,
        default=None,
        help="Path to dump the fixture consumer tool debug output.",
    )


def pytest_configure(config: pytest.Config) -> None:  # noqa: D103
    if "health" in sys.argv:
        return

    # Hint about consume-direct.toml if missing
    config_path = Path.cwd() / "consume-direct.toml"
    if not config_path.exists() and not config.option.collectonly:
        warnings.warn(
            "No consume-direct.toml found. "
            "Run `consume direct health` to set up client binaries.",
            stacklevel=1,
        )

    # Resolve --client names to bin paths from consume-direct.toml
    client_names = config.getoption("client_names", [])
    bin_paths = list(config.getoption("fixture_consumer_bin", []))

    if client_names and bin_paths:
        pytest.exit(
            "Cannot use both --client and --bin. Use one or the other."
        )

    if client_names:
        config_path = Path.cwd() / "consume-direct.toml"
        if not config_path.exists():
            pytest.exit(
                f"consume-direct.toml not found. "
                f"Run `consume direct health` to create it."
            )
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(config_path, "rb") as f:
            client_config = tomllib.load(f)
        for name in client_names:
            entry = client_config.get(name, {})
            bin_str = entry.get("bin", "")
            if not bin_str:
                pytest.exit(
                    f"Client '{name}' not configured in "
                    f"consume-direct.toml."
                )
            bin_paths.append(Path(bin_str).expanduser())

    # Replace the option so downstream code sees the resolved paths
    config.option.fixture_consumer_bin = bin_paths

    # Validate required options
    if not bin_paths and not config.option.collectonly:
        config_path = Path.cwd() / "consume-direct.toml"
        available = ""
        if config_path.exists():
            try:
                import tomllib
            except ModuleNotFoundError:
                import tomli as tomllib  # type: ignore[no-redef]
            with open(config_path, "rb") as f:
                available_clients = list(tomllib.load(f).keys())
            if available_clients:
                available = (
                    f"\nConfigured clients: {', '.join(available_clients)}"
                )
        pytest.exit(
            "No client binary provided. Use --bin <path> or "
            "--client <name> to specify a fixture consumer, "
            "or run `consume direct health` to check available clients."
            + available
        )

    fixture_type = config.getoption("fixture_type", None)
    if fixture_type is None and not config.option.collectonly:
        pytest.exit(
            "No fixture type specified. Use --type <state|block|engine|all>."
        )
    type_to_formats = {
        "state": [StateFixture],
        "block": [BlockchainFixture],
        "engine": [BlockchainEngineFixture],
    }
    if fixture_type and fixture_type != "all":
        config.supported_fixture_formats = type_to_formats[fixture_type]  # type: ignore[attr-defined]
    else:
        config.supported_fixture_formats = [  # type: ignore[attr-defined]
            StateFixture,
            BlockchainFixture,
            BlockchainEngineFixture,
        ]
    num_workers = config.getoption("num_workers", 1)
    fixture_consumers = []
    for fixture_consumer_bin_path in config.getoption("fixture_consumer_bin"):
        bin_path = Path(fixture_consumer_bin_path)
        try:
            consumer = FixtureConsumerTool.from_binary_path(
                binary_path=bin_path,
                trace=config.getoption("consumer_collect_traces"),
            )
        except Exception:
            # Try dotnet project detection for .csproj/.dll paths
            from execution_testing.client_clis.clis.nethermind import (
                NethtestFixtureConsumer,
            )
            try:
                consumer = NethtestFixtureConsumer.from_binary_path(
                    binary_path=bin_path,
                    trace=config.getoption("consumer_collect_traces"),
                )
            except Exception:
                raise Exception(
                    f"Unknown CLI binary: {bin_path}. "
                    f"Could not detect as native binary or dotnet project."
                )
        consumer.workers = num_workers  # type: ignore[attr-defined]
        fixture_consumers.append(consumer)
    if config.option.markers:
        return
    elif not fixture_consumers and config.option.collectonly:
        warnings.warn(
            (
                "No fixture consumer binaries provided; using a dummy "
                "consumer for collect-only; all possible fixture formats "
                "will be collected. Specify fixture consumer(s) via `--bin` "
                "to see actual collection results."
            ),
            stacklevel=1,
        )
        fixture_consumers = [CollectOnlyFixtureConsumer()]
    elif not fixture_consumers:
        pytest.exit(
            "No fixture consumer binaries provided; please specify a binary "
            "path via `--bin`."
        )
    config.fixture_consumers = fixture_consumers  # type: ignore[attr-defined]


def pytest_report_header(
    config: pytest.Config,
) -> list[str]:
    """Add client and worker info to the report header."""
    if "health" in sys.argv:
        return []
    lines = []
    consumers = getattr(config, "fixture_consumers", [])
    num_workers = config.getoption("num_workers", 1)
    # Map class names to friendly client names
    name_map = {
        "GethFixtureConsumer": "geth",
        "BesuFixtureConsumer": "besu",
        "NethtestFixtureConsumer": "nethermind",
    }
    for consumer in consumers:
        cls_name = type(consumer).__name__
        friendly = name_map.get(cls_name, cls_name)
        lines.append(f"client: {friendly}")
    lines.append(f"bin-workers: {num_workers}")
    n_workers = config.getoption("numprocesses", None)
    if n_workers:
        lines.append(f"xdist workers: {n_workers}")
    lines.append(
        "Note: initial binary startup may take a moment "
        "(especially JVM/dotnet clients)"
    )
    return lines


@pytest.fixture(scope="function")
def test_dump_dir(
    request: pytest.FixtureRequest, fixture_path: Path, fixture_name: str
) -> Path | None:
    """The directory to write evm debug output to."""
    base_dump_dir = request.config.getoption("base_dump_dir")
    if not base_dump_dir:
        return None
    if len(fixture_name) > 142:
        # ensure file name is not too long for eCryptFS
        fixture_name = fixture_name[:70] + "..." + fixture_name[-70:]
    return base_dump_dir / fixture_path.stem / fixture_name.replace("/", "-")


@pytest.fixture
def fixture_path(
    test_case: TestCaseIndexFile | TestCaseStream,
    fixtures_source: FixturesSource,
) -> Generator[Path, None, None]:
    """
    Path to the current JSON fixture file.

    If the fixture source is stdin, the fixture is written to a temporary json
    file.
    """
    if fixtures_source.is_stdin:
        assert isinstance(test_case, TestCaseStream)
        temp_dir = tempfile.TemporaryDirectory()
        fixture_path = (
            Path(temp_dir.name) / f"{test_case.id.replace('/', '_')}.json"
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
def fixture_name(test_case: TestCaseIndexFile | TestCaseStream) -> str:
    """Name of the current fixture."""
    return test_case.id


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize test cases for every fixture consumer."""
    metafunc.parametrize(
        "fixture_consumer",
        (
            pytest.param(
                fixture_consumer, id=str(fixture_consumer.__class__.__name__)
            )
            for fixture_consumer in metafunc.config.fixture_consumers  # type: ignore[attr-defined]
        ),
    )
