"""Unit tests for the `eth_config` execute tests."""

import json
from os.path import realpath
from pathlib import Path

import pytest
import yaml

from ethereum_test_base_types import ForkHash
from ethereum_test_rpc import EthConfigResponse

from ..types import NetworkConfig, NetworkConfigFile

EXPECTED_CANCUN = json.loads("""
{
    "activationTime": 0,
    "blobSchedule": {
    "baseFeeUpdateFraction": 3338477,
    "max": 6,
    "target": 3
    },
    "chainId": "0x88bb0",
    "forkId": "0xbef71d30",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02"
    }
}
""")
EXPECTED_CANCUN_FORK_ID = ForkHash("0xbef71d30")
EXPECTED_PRAGUE = json.loads("""
{
    "activationTime": 1742999832,
    "blobSchedule": {
    "baseFeeUpdateFraction": 5007716,
    "max": 9,
    "target": 6
    },
    "chainId": "0x88bb0",
    "forkId": "0x0929e24e",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BLS12_G1ADD": "0x000000000000000000000000000000000000000b",
    "BLS12_G1MSM": "0x000000000000000000000000000000000000000c",
    "BLS12_G2ADD": "0x000000000000000000000000000000000000000d",
    "BLS12_G2MSM": "0x000000000000000000000000000000000000000e",
    "BLS12_MAP_FP2_TO_G2": "0x0000000000000000000000000000000000000011",
    "BLS12_MAP_FP_TO_G1": "0x0000000000000000000000000000000000000010",
    "BLS12_PAIRING_CHECK": "0x000000000000000000000000000000000000000f",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": "0x0000bbddc7ce488642fb579f8b00f3a590007251",
    "DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa",
    "HISTORY_STORAGE_ADDRESS": "0x0000f90827f1c53a10cb7a02335b175320002935",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "0x00000961ef480eb55e80d19ad83579a64c007002"
  }
}
""")
EXPECTED_PRAGUE_FORK_ID = ForkHash("0x0929e24e")
EXPECTED_BPO1 = json.loads("""
{
    "activationTime": 1753477608,
    "blobSchedule": {
    "baseFeeUpdateFraction": 5007716,
    "max": 12,
    "target": 9
    },
    "chainId": "0x88bb0",
    "forkId": "0x5e2e4e84",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BLS12_G1ADD": "0x000000000000000000000000000000000000000b",
    "BLS12_G1MSM": "0x000000000000000000000000000000000000000c",
    "BLS12_G2ADD": "0x000000000000000000000000000000000000000d",
    "BLS12_G2MSM": "0x000000000000000000000000000000000000000e",
    "BLS12_MAP_FP2_TO_G2": "0x0000000000000000000000000000000000000011",
    "BLS12_MAP_FP_TO_G1": "0x0000000000000000000000000000000000000010",
    "BLS12_PAIRING_CHECK": "0x000000000000000000000000000000000000000f",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": "0x0000bbddc7ce488642fb579f8b00f3a590007251",
    "DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa",
    "HISTORY_STORAGE_ADDRESS": "0x0000f90827f1c53a10cb7a02335b175320002935",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "0x00000961ef480eb55e80d19ad83579a64c007002"
  }
}
""")
EXPECTED_BPO1_FORK_ID = ForkHash("0x5e2e4e84")
EXPECTED_BPO2 = json.loads("""
{
    "activationTime": 1753575912,
    "blobSchedule": {
    "baseFeeUpdateFraction": 5007716,
    "max": 15,
    "target": 12
    },
    "chainId": "0x88bb0",
    "forkId": "0x9d7b6bfb",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BLS12_G1ADD": "0x000000000000000000000000000000000000000b",
    "BLS12_G1MSM": "0x000000000000000000000000000000000000000c",
    "BLS12_G2ADD": "0x000000000000000000000000000000000000000d",
    "BLS12_G2MSM": "0x000000000000000000000000000000000000000e",
    "BLS12_MAP_FP2_TO_G2": "0x0000000000000000000000000000000000000011",
    "BLS12_MAP_FP_TO_G1": "0x0000000000000000000000000000000000000010",
    "BLS12_PAIRING_CHECK": "0x000000000000000000000000000000000000000f",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": "0x0000bbddc7ce488642fb579f8b00f3a590007251",
    "DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa",
    "HISTORY_STORAGE_ADDRESS": "0x0000f90827f1c53a10cb7a02335b175320002935",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "0x00000961ef480eb55e80d19ad83579a64c007002"
  }
}
""")
EXPECTED_BPO2_FORK_ID = ForkHash("0x9d7b6bfb")
EXPECTED_BPO3 = json.loads("""
{
    "activationTime": 1753674216,
    "blobSchedule": {
    "baseFeeUpdateFraction": 5007716,
    "max": 18,
    "target": 15
    },
    "chainId": "0x88bb0",
    "forkId": "0xbebdd3a1",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BLS12_G1ADD": "0x000000000000000000000000000000000000000b",
    "BLS12_G1MSM": "0x000000000000000000000000000000000000000c",
    "BLS12_G2ADD": "0x000000000000000000000000000000000000000d",
    "BLS12_G2MSM": "0x000000000000000000000000000000000000000e",
    "BLS12_MAP_FP2_TO_G2": "0x0000000000000000000000000000000000000011",
    "BLS12_MAP_FP_TO_G1": "0x0000000000000000000000000000000000000010",
    "BLS12_PAIRING_CHECK": "0x000000000000000000000000000000000000000f",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": "0x0000bbddc7ce488642fb579f8b00f3a590007251",
    "DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa",
    "HISTORY_STORAGE_ADDRESS": "0x0000f90827f1c53a10cb7a02335b175320002935",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "0x00000961ef480eb55e80d19ad83579a64c007002"
  }
}
""")
EXPECTED_BPO3_FORK_ID = ForkHash("0xbebdd3a1")
EXPECTED_BPO4 = json.loads("""
{
    "activationTime": 1753772520,
    "blobSchedule": {
    "baseFeeUpdateFraction": 5007716,
    "max": 9,
    "target": 6
    },
    "chainId": "0x88bb0",
    "forkId": "0x190c2054",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BLS12_G1ADD": "0x000000000000000000000000000000000000000b",
    "BLS12_G1MSM": "0x000000000000000000000000000000000000000c",
    "BLS12_G2ADD": "0x000000000000000000000000000000000000000d",
    "BLS12_G2MSM": "0x000000000000000000000000000000000000000e",
    "BLS12_MAP_FP2_TO_G2": "0x0000000000000000000000000000000000000011",
    "BLS12_MAP_FP_TO_G1": "0x0000000000000000000000000000000000000010",
    "BLS12_PAIRING_CHECK": "0x000000000000000000000000000000000000000f",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": "0x0000bbddc7ce488642fb579f8b00f3a590007251",
    "DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa",
    "HISTORY_STORAGE_ADDRESS": "0x0000f90827f1c53a10cb7a02335b175320002935",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "0x00000961ef480eb55e80d19ad83579a64c007002"
  }
}
""")
EXPECTED_BPO4_FORK_ID = ForkHash("0x190c2054")
EXPECTED_BPO5 = json.loads("""
{
    "activationTime": 1753889256,
    "blobSchedule": {
    "baseFeeUpdateFraction": 5007716,
    "max": 20,
    "target": 15
    },
    "chainId": "0x88bb0",
    "forkId": "0xd3a4880b",
    "precompiles": {
    "BLAKE2F": "0x0000000000000000000000000000000000000009",
    "BLS12_G1ADD": "0x000000000000000000000000000000000000000b",
    "BLS12_G1MSM": "0x000000000000000000000000000000000000000c",
    "BLS12_G2ADD": "0x000000000000000000000000000000000000000d",
    "BLS12_G2MSM": "0x000000000000000000000000000000000000000e",
    "BLS12_MAP_FP2_TO_G2": "0x0000000000000000000000000000000000000011",
    "BLS12_MAP_FP_TO_G1": "0x0000000000000000000000000000000000000010",
    "BLS12_PAIRING_CHECK": "0x000000000000000000000000000000000000000f",
    "BN254_ADD": "0x0000000000000000000000000000000000000006",
    "BN254_MUL": "0x0000000000000000000000000000000000000007",
    "BN254_PAIRING": "0x0000000000000000000000000000000000000008",
    "ECREC": "0x0000000000000000000000000000000000000001",
    "ID": "0x0000000000000000000000000000000000000004",
    "KZG_POINT_EVALUATION": "0x000000000000000000000000000000000000000a",
    "MODEXP": "0x0000000000000000000000000000000000000005",
    "RIPEMD160": "0x0000000000000000000000000000000000000003",
    "SHA256": "0x0000000000000000000000000000000000000002"
    },
    "systemContracts": {
    "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": "0x0000bbddc7ce488642fb579f8b00f3a590007251",
    "DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa",
    "HISTORY_STORAGE_ADDRESS": "0x0000f90827f1c53a10cb7a02335b175320002935",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "0x00000961ef480eb55e80d19ad83579a64c007002"
  }
}
""")
EXPECTED_BPO5_FORK_ID = ForkHash("0xd3a4880b")

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent


STATIC_NETWORK_CONFIGS = """
# Static network configs so updates to the network configs don't break the tests.
Mainnet:
  chainId:              0x1
  genesisHash:          0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3
  forkActivationTimes:
    0:                  Frontier
    1150000:            Homestead
    1920000:            DAOFork
    2463000:            Tangerine
    2675000:            SpuriousDragon
    4370000:            Byzantium
    7280000:            Constantinople
    9069000:            Istanbul
    9200000:            MuirGlacier
    12244000:           Berlin
    12965000:           London
    13773000:           ArrowGlacier
    15050000:           GrayGlacier
    1681338455:         Shanghai
    1710338135:         Cancun
    1746612311:         Prague

Sepolia:
  chainId:              0xaa36a7
  genesisHash:          0x25a5cc106eea7138acab33231d7160d69cb777ee0c2c553fcddf5138993e6dd9
  forkActivationTimes:
    0:                  Berlin
    1735371:            London
    1677557088:         Shanghai
    1706655072:         Cancun
    1741159776:         Prague
  addressOverrides:
    0x00000000219ab540356cbb839cbe05303d7705fa: 0x7f02c3e3c98b133055b8b348b2ac625669ed295d

Hoodi:
  chainId:              0x88BB0
  genesisHash:          0xbbe312868b376a3001692a646dd2d7d1e4406380dfd86b98aa8a34d1557c971b
  forkActivationTimes:
    0:                  Cancun
    1742999832:         Prague

Holesky:
  chainId:              0x4268
  genesisHash:          0xb5f7f912443c940f21fd611f12828d75b534364ed9e95ca4e307729a4661bde4
  forkActivationTimes:
    0:                  Paris
    1696000704:         Shanghai
    1707305664:         Cancun
    1740434112:         Prague
  addressOverrides:
    0x00000000219ab540356cbb839cbe05303d7705fa: 0x4242424242424242424242424242424242424242

# Test-only network configs.
HoodiWithBPOs:
  chainId:              0x88BB0
  genesisHash:          0xbbe312868b376a3001692a646dd2d7d1e4406380dfd86b98aa8a34d1557c971b
  forkActivationTimes:
    0:                  Cancun
    1742999832:         Prague
  bpoForkActivationTimes:
    1753477608:
        target: 9
        max: 12
        base_fee_update_fraction: 5007716
    1753575912:
        target: 12
        max: 15
        base_fee_update_fraction: 5007716
    1753674216:
        target: 15
        max: 18
        base_fee_update_fraction: 5007716
    1753772520:
        target: 6
        max: 9
        base_fee_update_fraction: 5007716
    1753889256:
        target: 15
        max: 20
        base_fee_update_fraction: 5007716
"""


@pytest.fixture(scope="session")
def network_configs() -> NetworkConfigFile:
    """Get the file contents from the provided network configs file."""
    return NetworkConfigFile(root=yaml.safe_load(STATIC_NETWORK_CONFIGS))


@pytest.fixture
def network(request: pytest.FixtureRequest, network_configs: NetworkConfigFile) -> NetworkConfig:
    """Get the network that is under test."""
    network_name = request.param
    assert network_name in network_configs.root, (
        f"Network {network_name} could not be found in network_configs."
    )
    return network_configs.root[network_name]


@pytest.fixture
def eth_config(network: NetworkConfig, current_time: int) -> EthConfigResponse:
    """Get the `eth_config` response from the client to be verified by all tests."""
    return network.get_eth_config(current_time)


@pytest.mark.parametrize(
    [
        "network",
        "current_time",
        "expected_eth_config",
    ],
    [
        pytest.param(
            "Hoodi",
            0,
            EthConfigResponse(
                current=EXPECTED_CANCUN,
                next=EXPECTED_PRAGUE,
                last=EXPECTED_PRAGUE,
            ),
            id="Hoodi_cancun",
        ),
        pytest.param(
            "Hoodi",
            1753477608,
            EthConfigResponse(
                current=EXPECTED_PRAGUE,
            ),
            id="Hoodi_prague",
        ),
        pytest.param(
            "HoodiWithBPOs",
            1742999832,
            EthConfigResponse(
                current=EXPECTED_PRAGUE,
                next=EXPECTED_BPO1,
                last=EXPECTED_BPO5,
            ),
            id="Hoodi_prague_with_bpos_1",
        ),
        pytest.param(
            "HoodiWithBPOs",
            1753575912,
            EthConfigResponse(
                current=EXPECTED_BPO2,
                next=EXPECTED_BPO3,
                last=EXPECTED_BPO5,
            ),
            id="Hoodi_prague_with_bpos_2",
        ),
        pytest.param(
            "HoodiWithBPOs",
            1753674216,
            EthConfigResponse(
                current=EXPECTED_BPO3,
                next=EXPECTED_BPO4,
                last=EXPECTED_BPO5,
            ),
            id="Hoodi_prague_with_bpos_3",
        ),
        pytest.param(
            "HoodiWithBPOs",
            1753772520,
            EthConfigResponse(
                current=EXPECTED_BPO4,
                next=EXPECTED_BPO5,
                last=EXPECTED_BPO5,
            ),
            id="Hoodi_prague_with_bpos_4",
        ),
        pytest.param(
            "HoodiWithBPOs",
            1753889256,
            EthConfigResponse(
                current=EXPECTED_BPO5,
            ),
            id="Hoodi_prague_with_bpos_5",
        ),
    ],
    indirect=["network"],
)
def test_fork_config_from_fork(
    eth_config: EthConfigResponse,
    expected_eth_config: EthConfigResponse,
):
    """Test the `fork_config_from_fork` function."""
    current_config, next_config = (eth_config.current, eth_config.next)
    assert current_config.model_dump(
        mode="json", by_alias=True
    ) == expected_eth_config.current.model_dump(mode="json", by_alias=True), (
        f"Expected {expected_eth_config.current.model_dump_json()} but got "
        f"{current_config.model_dump_json()}"
    )
    assert current_config.fork_id == expected_eth_config.current.fork_id, (
        f"Expected {expected_eth_config.current.fork_id} but got {current_config.fork_id}"
    )
    if expected_eth_config.next is not None:
        assert next_config is not None, "Expected next to be not None"
        assert next_config.model_dump(
            mode="json", by_alias=True
        ) == expected_eth_config.next.model_dump(mode="json", by_alias=True), (
            f"Expected {expected_eth_config.next.model_dump_json()} but got "
            f"{next_config.model_dump_json()}"
        )
        assert next_config.fork_id == expected_eth_config.next.fork_id, (
            f"Expected {expected_eth_config.next.fork_id} but got {next_config.fork_id}"
        )
    else:
        assert next_config is None, "Expected next to be None"
    if expected_eth_config.last is not None:
        assert eth_config.last is not None, "Expected last to be not None"
        assert eth_config.last.model_dump(
            mode="json", by_alias=True
        ) == expected_eth_config.last.model_dump(mode="json", by_alias=True), (
            f"Expected {expected_eth_config.last.model_dump_json()} but got "
            f"{eth_config.last.model_dump_json()}"
        )
        assert eth_config.last.fork_id == expected_eth_config.last.fork_id, (
            f"Expected {expected_eth_config.last.fork_id} but got {eth_config.last.fork_id}"
        )
    else:
        assert eth_config.last is None, "Expected last to be None"


@pytest.mark.parametrize(
    [
        "network",
        "current_time",
        "expected_current_fork_id",
        "expected_next_fork_id",
        "expected_last_fork_id",
    ],
    [
        pytest.param(
            "Mainnet",
            1746612310,  # Right before Prague activation
            ForkHash(0x9F3D2254),
            ForkHash(0xC376CF8B),
            ForkHash(0xC376CF8B),
            id="mainnet_cancun",
        ),
        pytest.param(
            "Sepolia",
            1741159775,  # Right before Prague activation
            ForkHash(0x88CF81D9),
            ForkHash(0xED88B5FD),
            ForkHash(0xED88B5FD),
            id="sepolia_cancun",
        ),
        pytest.param(
            "Holesky",
            1740434111,  # Right before Prague activation
            ForkHash(0x9B192AD0),
            ForkHash(0xDFBD9BED),
            ForkHash(0xDFBD9BED),
            id="holesky_cancun",
        ),
        pytest.param(
            "Hoodi",
            1742999831,  # Right before Prague activation
            ForkHash(0xBEF71D30),
            ForkHash(0x0929E24E),
            ForkHash(0x0929E24E),
            id="hoodi_prague",
        ),
    ],
    indirect=["network"],
)
def test_fork_ids(
    eth_config: EthConfigResponse,
    expected_current_fork_id: ForkHash,
    expected_next_fork_id: ForkHash | None,
    expected_last_fork_id: ForkHash | None,
):
    """Test various configurations of fork Ids for different timestamps."""
    assert expected_current_fork_id == eth_config.current.fork_id, (
        f"Unexpected current fork id: {eth_config.current.fork_id} != {expected_current_fork_id}"
    )
    if expected_next_fork_id is not None:
        assert eth_config.next is not None, "Expected next to be not None"
        assert expected_next_fork_id == eth_config.next.fork_id, (
            f"Unexpected next fork id: {eth_config.next.fork_id} != {expected_next_fork_id}"
        )
    else:
        assert eth_config.next is None, "Expected next to be None"
    if expected_last_fork_id is not None:
        assert eth_config.last is not None, "Expected last to be not None"
        assert expected_last_fork_id == eth_config.last.fork_id, (
            f"Unexpected last fork id: {eth_config.last.fork_id} != {expected_last_fork_id}"
        )
    else:
        assert eth_config.last is None, "Expected last to be None"
