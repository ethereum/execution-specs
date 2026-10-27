"""
Shared pytest plugin that sets up the transition tool.

Provides the command-line options that select and configure the transition
tool, and the `session_t8n` and `t8n` fixtures, for every command that runs
tests through a transition tool.

Plugins that load this one must define a function-scoped
`dump_dir_parameter_level` fixture, which gives the directory for the
transition tool's debug output of the current test (or `None`).
"""

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, Set

import pytest
from pytest_metadata.plugin import metadata_key

from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures import strip_fixture_format_from_node
from execution_testing.specs.base import OpMode

from .helpers import is_benchmark_test


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
            "PATH) that provides `t8n`. Defaults to the in-repo EELS "
            "Python spec (`src/ethereum/`)."
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


def configure_transition_tool(config: pytest.Config) -> TransitionTool:
    """
    Instantiate the transition tool selected on the command line and store
    it in `config.t8n`.

    Called from the `pytest_configure` hook of the command's main plugin, so
    that an invalid binary path or trace option is reported once, instead of
    for every test.
    """
    evm_bin = config.getoption("evm_bin")
    # `--traces` belongs to the commands that offer it (not `evaluate`,
    # where a run asks for its own traces).
    trace = config.getoption("evm_collect_traces", default=False)
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
        isinstance(config.getoption("numprocesses", None), int)
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
    return t8n


@dataclass(kw_only=True)
class TransitionToolCacheStats:
    """Stats for caching of the transition tool requests."""

    key_test_hits: int = 0
    key_test_miss: int = 0
    subkey_test_hits: int = 0
    subkey_test_miss: int = 0
    unique_keys: int = 0
    _seen_keys: Set[str] = field(default_factory=set, repr=False)

    def record_key(self, key: str) -> None:
        """Record a cache key and update unique_keys count."""
        self._seen_keys.add(key)
        self.unique_keys = len(self._seen_keys)

    @property
    def expected_hits(self) -> int:
        """Number of tests expected to hit the cache."""
        total_cacheable = self.key_test_hits + self.key_test_miss
        return total_cacheable - self.unique_keys

    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dict for xdist worker transfer."""
        return {
            "key_test_hits": self.key_test_hits,
            "key_test_miss": self.key_test_miss,
            "subkey_test_hits": self.subkey_test_hits,
            "subkey_test_miss": self.subkey_test_miss,
            "unique_keys": self.unique_keys,
        }

    def add(self, other: "TransitionToolCacheStats") -> None:
        """Add another stats object to this one."""
        self.key_test_hits += other.key_test_hits
        self.key_test_miss += other.key_test_miss
        self.subkey_test_hits += other.subkey_test_hits
        self.subkey_test_miss += other.subkey_test_miss
        self.unique_keys += other.unique_keys

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "TransitionToolCacheStats":
        """Create stats from dict (xdist worker transfer)."""
        return cls(
            key_test_hits=data.get("key_test_hits", 0),
            key_test_miss=data.get("key_test_miss", 0),
            subkey_test_hits=data.get("subkey_test_hits", 0),
            subkey_test_miss=data.get("subkey_test_miss", 0),
            unique_keys=data.get("unique_keys", 0),
        )


@pytest.fixture(autouse=True, scope="session")
def evm_bin(request: pytest.FixtureRequest) -> Path | None:
    """Return configured evm tool binary path used to run t8n."""
    return request.config.getoption("evm_bin")


@pytest.fixture(scope="session")
def base_dump_dir(request: pytest.FixtureRequest) -> Path | None:
    """Path to base directory to dump the evm debug output."""
    base_dump_dir_str = request.config.getoption("base_dump_dir")
    if base_dump_dir_str:
        return Path(base_dump_dir_str)
    return None


@pytest.fixture(autouse=True, scope="session")
def session_t8n(
    request: pytest.FixtureRequest,
) -> Generator[TransitionTool, None, None]:
    """Return configured transition tool for the session."""
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


def get_t8n_cache_key(request: pytest.FixtureRequest) -> str | None:
    """Get the cache key to be used for the current test, if any."""
    mark: pytest.Mark = request.node.get_closest_marker(
        "transition_tool_cache_key"
    )
    if mark is not None and len(mark.args) == 1:
        return f"{strip_fixture_format_from_node(request.node)}-{mark.args[0]}"
    return None


@pytest.fixture(autouse=True, scope="session")
def transition_tool_cache_stats(
    request: pytest.FixtureRequest,
) -> Generator[TransitionToolCacheStats, None, None]:
    """Get the transition tool cache stats."""
    stats = TransitionToolCacheStats()
    yield stats
    # Store stats for later access
    request.config.transition_tool_cache_stats = stats  # type: ignore[attr-defined]
    # For xdist workers, send stats to controller via workeroutput
    if hasattr(request.config, "workeroutput"):
        request.config.workeroutput["t8n_cache_stats"] = stats.to_dict()


@pytest.fixture(autouse=True, scope="function")
def t8n(
    request: pytest.FixtureRequest,
    session_t8n: TransitionTool,
    dump_dir_parameter_level: Path | None,
    transition_tool_cache_stats: TransitionToolCacheStats,
) -> Generator[TransitionTool, None, None]:
    """Set the transition tool up for the current test."""
    if transition_tool_cache_key := get_t8n_cache_key(request):
        # This test is allowed to cache results
        transition_tool_cache_stats.record_key(transition_tool_cache_key)
        if session_t8n.set_cache(key=transition_tool_cache_key):
            transition_tool_cache_stats.key_test_hits += 1
        else:
            transition_tool_cache_stats.key_test_miss += 1
    else:
        # Test cannot use output cache, remove it
        session_t8n.remove_cache()
    # Reset the traces
    session_t8n.reset_traces()
    session_t8n.call_counter = 0
    session_t8n.debug_dump_dir = dump_dir_parameter_level
    # Only benchmark tests report opcode counts, unless asked for all.
    session_t8n.count_opcodes = (
        request.config.getoption("count_opcodes", False)
        or getattr(request.config, "op_mode", None) == OpMode.BENCHMARKING
        or "benchmark_test" in request.fixturenames
        or is_benchmark_test(request)
    )
    session_t8n.reset_opcode_count()
    yield session_t8n
    # Only collect subkey stats for cacheable tests (non-cacheable tests
    # still interact with the OutputCache after remove_cache, producing
    # phantom misses that would skew the hit rate).
    if transition_tool_cache_key and session_t8n.output_cache is not None:
        transition_tool_cache_stats.subkey_test_hits += (
            session_t8n.output_cache.hits
        )
        transition_tool_cache_stats.subkey_test_miss += (
            session_t8n.output_cache.misses
        )
        # Reset counters to avoid double-counting (cache persists across tests)
        session_t8n.output_cache.hits = 0
        session_t8n.output_cache.misses = 0
