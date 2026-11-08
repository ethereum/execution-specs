"""Tests for the BAL modes of `consume wirex --wirex-bals`."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
from hive.client import ClientType

from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.test_tracker import (  # noqa: E501
    group_variants_key,
)
from execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex import (  # noqa: E501
    conftest as wirex,
)
from execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex.conftest import (  # noqa: E501
    BalMode,
    bal_variants,
    withholds_only,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.forks import (
    Amsterdam,
    BPO2ToAmsterdamAtTime15k,
    Osaka,
    OsakaToBPO1AtTime15k,
)

from .direct_calls import fixture_body
from .variant_generator import PRE_HASH, engine_x_case, generate, groups

# The generator and the requests below carry fork, format and variant
# marks that only a consume session registers.
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnknownMarkWarning"
)


GETH = cast(ClientType, SimpleNamespace(name="go-ethereum_default"))
NETHERMIND = cast(ClientType, SimpleNamespace(name="nethermind_default"))


MODES = {
    "withhold": ("bal_withheld",),
    "serve": ("bal_served",),
    "both": ("bal_withheld", "bal_served"),
}
BAL_FORKS = (Amsterdam, BPO2ToAmsterdamAtTime15k)
EARLIER_FORKS = (Osaka, OsakaToBPO1AtTime15k, None)


def _row(
    fork: Any, client: ClientType, mode: str, expected: tuple[str, ...]
) -> Any:
    """Return a `bal_variants` case with a readable ID."""
    name = "no_fork" if fork is None else fork.name()
    client_id = client.name.split("_")[0]
    return pytest.param(
        fork, client, mode, expected, id=f"{name}-{client_id}-{mode}"
    )


@pytest.mark.parametrize(
    "fork,client,mode,expected",
    [
        *(
            _row(fork, GETH, mode, expected)
            for fork in BAL_FORKS
            for mode, expected in MODES.items()
        ),
        *(
            _row(fork, GETH, mode, ("",))
            for fork in EARLIER_FORKS
            for mode in MODES
        ),
        *(
            _row(fork, NETHERMIND, "both", ("bal_withheld",))
            for fork in BAL_FORKS
        ),
        _row(Amsterdam, NETHERMIND, "withhold", ("bal_withheld",)),
        _row(Amsterdam, NETHERMIND, "serve", ("bal_served",)),
    ],
)
def test_bal_variants(
    fork: Any, client: ClientType, mode: str, expected: tuple[str, ...]
) -> None:
    """BAL forks name their mode; nethermind narrows only `both`."""
    assert (
        bal_variants(engine_x_case("test", fork), client, BalMode(mode))
        == expected
    )


@pytest.mark.parametrize(
    "name,expected",
    [
        ("nethermind", True),
        ("nethermind_default", True),
        ("go-ethereum_default", False),
        ("reth", False),
    ],
)
def test_withhold_only_matches_hive_client_names(
    name: str, expected: bool
) -> None:
    """Hive client names carry a nametag suffix, so match by substring."""
    assert withholds_only(name) is expected


def _options(**values: str) -> SimpleNamespace:
    """Return a config whose `getoption` answers from `values` only."""

    def getoption(name: str, default: Any = None) -> Any:
        del default
        return values[name]

    return SimpleNamespace(getoption=getoption, stash=pytest.Stash())


@pytest.mark.parametrize(
    "mode,expected",
    [
        (
            "withhold",
            [
                "a-go-ethereum_default",
                "a-nethermind_default",
                "b-go-ethereum_default-bal_withheld",
                "b-nethermind_default-bal_withheld",
            ],
        ),
        (
            "serve",
            [
                "a-go-ethereum_default",
                "a-nethermind_default",
                "b-go-ethereum_default-bal_served",
                "b-nethermind_default-bal_served",
            ],
        ),
        (
            "both",
            [
                "a-go-ethereum_default",
                "a-nethermind_default",
                "b-go-ethereum_default-bal_withheld",
                "b-go-ethereum_default-bal_served",
                "b-nethermind_default-bal_withheld",
            ],
        ),
    ],
)
def test_wirex_configure_installs_bal_variants(
    mode: str, expected: list[str]
) -> None:
    """The wirex config feeds its `--wirex-bals` mode to the generator."""
    config = _options(wirex_bals=mode)
    wirex.pytest_configure(cast(pytest.Config, config))
    assert config.supported_fixture_formats == [BlockchainEngineXFixture]
    params = generate(
        [engine_x_case("a", Osaka), engine_x_case("b", Amsterdam)],
        clients=("go-ethereum_default", "nethermind_default"),
        group_variants=config.stash[group_variants_key],
    )
    assert [param.id for param in params] == expected
    assert [groups(param) for param in params] == [
        [f"{PRE_HASH}-{test_id[2:]}"] for test_id in expected
    ]


def _request(variant: str) -> pytest.FixtureRequest:
    """Return a request for a test of `variant`, with no option set."""
    marks = {"group_variant": pytest.mark.group_variant(variant).mark}
    node = SimpleNamespace(
        get_closest_marker=lambda name: marks.get(name) if variant else None
    )
    return cast(
        pytest.FixtureRequest, SimpleNamespace(node=node, config=_options())
    )


@pytest.mark.parametrize(
    "variant,expected",
    [("bal_served", True), ("bal_withheld", False), ("", False)],
)
def test_serve_bals_follows_the_variant(variant: str, expected: bool) -> None:
    """The peer serves BALs exactly when the test ID says `bal_served`."""
    serve_bals = fixture_body(wirex.wirex_serve_bals)(_request(variant))
    assert serve_bals is expected
