"""Test the types in the `ethereum_test_rpc` package."""

from typing import Any, Dict

import pytest

from ethereum_test_rpc import EthConfigResponse

eth_config_dict: Dict[str, Any] = {
    "current": {
        "activationTime": 0,
        "blobSchedule": {"baseFeeUpdateFraction": 3338477, "max": 6, "target": 3},
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
            "SHA256": "0x0000000000000000000000000000000000000002",
        },
        "systemContracts": {"BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02"},
    },
    "next": {
        "activationTime": 1742999832,
        "blobSchedule": {"baseFeeUpdateFraction": 5007716, "max": 9, "target": 6},
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
            "SHA256": "0x0000000000000000000000000000000000000002",
        },
        "systemContracts": {
            "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
            "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": (
                "0x0000bbddc7ce488642fb579f8b00f3a590007251"
            ),
            "DEPOSIT_CONTRACT_ADDRESS": ("0x00000000219ab540356cbb839cbe05303d7705fa"),
            "HISTORY_STORAGE_ADDRESS": ("0x0000f90827f1c53a10cb7a02335b175320002935"),
            "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": ("0x00000961ef480eb55e80d19ad83579a64c007002"),
        },
    },
    "last": {
        "activationTime": 1742999832,
        "blobSchedule": {"baseFeeUpdateFraction": 5007716, "max": 9, "target": 6},
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
            "SHA256": "0x0000000000000000000000000000000000000002",
        },
        "systemContracts": {
            "BEACON_ROOTS_ADDRESS": "0x000f3df6d732807ef1319fb7b8bb8522d0beac02",
            "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS": (
                "0x0000bbddc7ce488642fb579f8b00f3a590007251"
            ),
            "DEPOSIT_CONTRACT_ADDRESS": ("0x00000000219ab540356cbb839cbe05303d7705fa"),
            "HISTORY_STORAGE_ADDRESS": ("0x0000f90827f1c53a10cb7a02335b175320002935"),
            "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": ("0x00000961ef480eb55e80d19ad83579a64c007002"),
        },
    },
}


@pytest.fixture
def eth_config_response() -> EthConfigResponse:
    """Get the `eth_config` response from the client to be verified by all tests."""
    return EthConfigResponse.model_validate(eth_config_dict)


def test_fork_config_get_hash(eth_config_response: EthConfigResponse) -> None:
    """Test the `get_hash` method of the `ForkConfig` class."""
    # Iterate through each fork config and validate
    for config_name in ("current", "next", "last"):
        config = getattr(eth_config_response, config_name)
        expected = eth_config_dict[config_name]
        if config is None:
            assert expected is None
            continue

        # Top-level fields
        assert config.activation_time == expected["activationTime"]
        assert str(config.chain_id) == expected["chainId"]
        assert str(config.fork_id) == expected["forkId"]

        # Precompiles
        assert set(config.precompiles.keys()) == set(expected["precompiles"].keys())
        for k, v in expected["precompiles"].items():
            assert config.precompiles[k] == v

        # System contracts
        assert set(config.system_contracts.keys()) == set(expected["systemContracts"].keys())
        for k, v in expected["systemContracts"].items():
            assert config.system_contracts[k] == v

        # Blob schedule
        if expected.get("blobSchedule") is not None:
            assert config.blob_schedule is not None
            assert (
                config.blob_schedule.target_blobs_per_block == expected["blobSchedule"]["target"]
            )
            assert config.blob_schedule.max_blobs_per_block == expected["blobSchedule"]["max"]
            assert (
                config.blob_schedule.base_fee_update_fraction
                == expected["blobSchedule"]["baseFeeUpdateFraction"]
            )
        else:
            assert config.blob_schedule is None
