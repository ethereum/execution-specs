"""Tests for the `consume reorg` simulator's client environment fixture."""

from execution_testing.base_types import Hash
from execution_testing.fixtures.blockchain import FixtureConfig
from execution_testing.fixtures.reorg import BlockchainEngineReorgFixture
from execution_testing.forks import Cancun

from ..simulators.reorg.conftest import environment

GENESIS_HEADER = {
    "parentHash": Hash(0),
    "unclesHash": Hash(0),
    "coinbase": "0x" + "00" * 20,
    "stateRoot": Hash(0),
    "transactionsTrie": Hash(0),
    "receiptTrie": Hash(0),
    "bloom": "0x" + "00" * 256,
    "difficulty": "0x0",
    "number": "0x0",
    "gasLimit": "0x1000000",
    "gasUsed": "0x0",
    "timestamp": "0x0",
    "extraData": "0x",
    "mixHash": Hash(0),
    "nonce": "0x0000000000000000",
    "baseFeePerGas": "0x0",
    "withdrawalsRoot": Hash(0),
    "blobGasUsed": "0x0",
    "excessBlobGas": "0x0",
    "parentBeaconBlockRoot": Hash(0),
}


def make_fixture(min_reorg_depth: int | None) -> BlockchainEngineReorgFixture:
    """A minimal reorg fixture with the given `minReorgDepth`."""
    return BlockchainEngineReorgFixture(
        fork=Cancun,
        config=FixtureConfig(fork=Cancun),
        genesis=GENESIS_HEADER,
        pre={},
        blocks={},
        steps=[],
        min_reorg_depth=min_reorg_depth,
    )


def test_environment_maps_min_reorg_depth_to_hive_var() -> None:
    """A set `minReorgDepth` becomes `HIVE_ENGINE_MAX_REORG_DEPTH`."""
    fixture = make_fixture(72)
    env = environment.__wrapped__(fixture, 8545)  # type: ignore[attr-defined]
    assert env["HIVE_ENGINE_MAX_REORG_DEPTH"] == "72"


def test_environment_omits_var_when_min_reorg_depth_unset() -> None:
    """No `minReorgDepth` means no depth override; client defaults apply."""
    fixture = make_fixture(None)
    env = environment.__wrapped__(fixture, 8545)  # type: ignore[attr-defined]
    assert "HIVE_ENGINE_MAX_REORG_DEPTH" not in env
