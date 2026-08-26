"""Test parsing a genesis file to generate a network configuration."""

from os.path import realpath
from pathlib import Path

import pytest

from execution_testing.base_types import (
    Account,
    Address,
    Hash,
    StateCommitment,
)
from execution_testing.forks import (
    BPO1,
    BPO2,
    BPO3,
    BPO4,
    BPO5,
    Berlin,
    BinaryTree,
    Byzantium,
    Cancun,
    Constantinople,
    Homestead,
    Istanbul,
    London,
    Osaka,
    Paris,
    Prague,
    Shanghai,
)
from execution_testing.rpc import (
    ForkConfigBlobSchedule,
)
from execution_testing.test_types import Alloc

from ..execute_types import (
    ForkActivationTimes,
    Genesis,
    GenesisConfig,
    NetworkConfig,
)

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent


@pytest.fixture
def genesis_contents(genesis_file_name: str) -> str:
    """Read the genesis file contents."""
    genesis_path = CURRENT_FOLDER / genesis_file_name
    return genesis_path.read_text()


@pytest.mark.parametrize(
    "genesis_file_name,expected_hash,expected_network_config",
    [
        pytest.param(
            "genesis_example.json",
            Hash(
                0x3A8C8CEF63859865AA1D40DED77B083EEF06A1702B8188D5586434B9C3ADC4BE
            ),
            NetworkConfig(
                chain_id=7023102237,
                genesis_hash=Hash(
                    0x3A8C8CEF63859865AA1D40DED77B083EEF06A1702B8188D5586434B9C3ADC4BE
                ),
                fork_activation_times=ForkActivationTimes(
                    root={
                        Homestead: 0,
                        Byzantium: 0,
                        Constantinople: 0,
                        Istanbul: 0,
                        Berlin: 0,
                        London: 0,
                        Paris: 0,
                        Shanghai: 0,
                        Cancun: 0,
                        Prague: 0,
                        Osaka: 1753379304,
                        BPO1: 1753477608,
                        BPO2: 1753575912,
                        BPO3: 1753674216,
                        BPO4: 1753772520,
                        BPO5: 1753889256,
                    },
                ),
                blob_schedule={
                    Cancun: ForkConfigBlobSchedule(
                        target_blobs_per_block=3,
                        max_blobs_per_block=6,
                        base_fee_update_fraction=3338477,
                    ),
                    Prague: ForkConfigBlobSchedule(
                        target_blobs_per_block=6,
                        max_blobs_per_block=9,
                        base_fee_update_fraction=5007716,
                    ),
                    Osaka: ForkConfigBlobSchedule(
                        target_blobs_per_block=6,
                        max_blobs_per_block=9,
                        base_fee_update_fraction=5007716,
                    ),
                    BPO1: ForkConfigBlobSchedule(
                        target_blobs_per_block=9,
                        max_blobs_per_block=12,
                        base_fee_update_fraction=5007716,
                    ),
                    BPO2: ForkConfigBlobSchedule(
                        target_blobs_per_block=12,
                        max_blobs_per_block=15,
                        base_fee_update_fraction=5007716,
                    ),
                    BPO3: ForkConfigBlobSchedule(
                        target_blobs_per_block=15,
                        max_blobs_per_block=18,
                        base_fee_update_fraction=5007716,
                    ),
                    BPO4: ForkConfigBlobSchedule(
                        target_blobs_per_block=6,
                        max_blobs_per_block=9,
                        base_fee_update_fraction=5007716,
                    ),
                    BPO5: ForkConfigBlobSchedule(
                        target_blobs_per_block=15,
                        max_blobs_per_block=20,
                        base_fee_update_fraction=5007716,
                    ),
                },
            ),
        ),
    ],
)
def test_genesis_parsing(
    genesis_contents: str,
    expected_hash: Hash,
    expected_network_config: NetworkConfig,
) -> None:
    """
    Verify genesis config file is parsed and correctly converted into a network
    configuration.
    """
    parsed_genesis = Genesis.model_validate_json(genesis_contents)
    assert parsed_genesis.hash == expected_hash, (
        f"Unexpected genesis hash: {parsed_genesis.hash}, "
        f"expected: {expected_hash}"
    )
    network_config = parsed_genesis.network_config()
    assert network_config == expected_network_config, (
        f"Unexpected network config: {network_config}, "
        f"expected: {expected_network_config}"
    )


def test_binary_tree_genesis_seeds_alloc_state_commitment() -> None:
    """Genesis hashing must use the provider selected by the active fork."""
    address = Address(0x100)
    alloc = Alloc({address: Account(balance=1, storage={0: 1})})

    mpt_alloc = alloc.model_copy(deep=True)
    mpt_alloc.migrate_state_commitment(StateCommitment.MPT)
    mpt_root = mpt_alloc.state_root()

    genesis = Genesis(
        config=GenesisConfig(
            chain_id=1,
            terminal_total_difficulty=0,
            terminal_total_difficulty_passed=True,
            fork_activation_times=ForkActivationTimes(root={BinaryTree: 0}),
            blob_schedule={},
        ),
        alloc=alloc,
        fee_recipient=Address(0),
        difficulty=0,
        extra_data=b"",
        gas_limit=30_000_000,
        nonce=0,
        mixhash=Hash(0),
        timestamp=0,
        parent_hash=Hash(0),
    )

    assert genesis.config.fork() is BinaryTree
    assert genesis.alloc.state_commitment() is StateCommitment.BINARY_TREE
    assert genesis.alloc.state_root() != mpt_root
    _ = genesis.hash
