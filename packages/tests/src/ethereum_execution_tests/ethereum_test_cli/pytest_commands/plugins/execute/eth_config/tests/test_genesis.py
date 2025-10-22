"""Test parsing a genesis file to generate a network configuration."""

from os.path import realpath
from pathlib import Path

import pytest

from ethereum_test_base_types import Hash
from ethereum_test_forks import (
    BPO1,
    BPO2,
    BPO3,
    BPO4,
    BPO5,
    Berlin,
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
from ethereum_test_rpc import (
    ForkConfigBlobSchedule,
)

from ..execute_types import ForkActivationTimes, Genesis, NetworkConfig

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
                        target=3, max=6, baseFeeUpdateFraction=3338477
                    ),
                    Prague: ForkConfigBlobSchedule(
                        target=6, max=9, baseFeeUpdateFraction=5007716
                    ),
                    Osaka: ForkConfigBlobSchedule(
                        target=6, max=9, baseFeeUpdateFraction=5007716
                    ),
                    BPO1: ForkConfigBlobSchedule(
                        target=9, max=12, baseFeeUpdateFraction=5007716
                    ),
                    BPO2: ForkConfigBlobSchedule(
                        target=12, max=15, baseFeeUpdateFraction=5007716
                    ),
                    BPO3: ForkConfigBlobSchedule(
                        target=15, max=18, baseFeeUpdateFraction=5007716
                    ),
                    BPO4: ForkConfigBlobSchedule(
                        target=6, max=9, baseFeeUpdateFraction=5007716
                    ),
                    BPO5: ForkConfigBlobSchedule(
                        target=15, max=20, baseFeeUpdateFraction=5007716
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
        f"Unexpected genesis hash: {parsed_genesis.hash}, expected: {expected_hash}"
    )
    network_config = parsed_genesis.network_config()
    assert network_config == expected_network_config, (
        f"Unexpected network config: {network_config}, expected: {expected_network_config}"
    )
