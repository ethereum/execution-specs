import importlib
import json
import pkgutil
from typing import Any, Dict, List, cast

import pytest
from ethereum_rlp import rlp
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import keccak256
from ethereum.ethash import (
    cache_size,
    dataset_size,
    generate_cache,
    generate_seed,
    hashimoto_light,
)
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
)
from ethereum.utils.numeric import le_uint32_sequence_to_bytes

from . import FORKS, TEST_FIXTURES
from .helpers.load_blockchain_tests import Load

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

POW_FORKS = [
    "Frontier",
    "Homestead",
    "EIP150",
    "EIP158",
    "Byzantium",
    "ConstantinopleFix",
    "Istanbul",
    "Berlin",
]


@pytest.mark.parametrize("json_fork", POW_FORKS)
def test_ethtest_fixtures(json_fork: str) -> None:
    eels_fork = FORKS[json_fork]["eels_fork"]
    fork_module = importlib.import_module(f"ethereum.{eels_fork}.fork")

    ethereum_tests = load_pow_test_fixtures(json_fork)
    for test in ethereum_tests:
        header = test["header"]
        assert header.nonce == test["nonce"]
        assert header.mix_digest == test["mix_digest"]
        assert generate_seed(header.number) == test["seed"]
        assert cache_size(header.number) == test["cache_size"]
        assert dataset_size(header.number) == test["dataset_size"]

        header_hash = fork_module.generate_header_hash_for_pow(header)
        assert header_hash == test["header_hash"]

        cache = generate_cache(header.number)
        cache_hash = keccak256(
            b"".join(
                le_uint32_sequence_to_bytes(cache_item) for cache_item in cache
            )
        )
        assert cache_hash == test["cache_hash"]

        mix_digest, result = hashimoto_light(
            header_hash, header.nonce, cache, dataset_size(header.number)
        )
        assert mix_digest == test["mix_digest"]
        assert result == test["result"]


def load_pow_test_fixtures(json_fork: str) -> List[Dict[str, Any]]:
    eels_fork = FORKS[json_fork]["eels_fork"]
    Header = importlib.import_module(f"ethereum.{eels_fork}.blocks").Header

    with open(
        f"{ETHEREUM_TESTS_PATH}/PoWTests/ethash_tests.json"
    ) as pow_test_file_handler:
        return [
            {
                "nonce": hex_to_bytes8(raw_fixture["nonce"]),
                "mix_digest": hex_to_bytes32(raw_fixture["mixHash"]),
                "header": rlp.decode_to(
                    Header, hex_to_bytes(raw_fixture["header"])
                ),
                "seed": hex_to_bytes32(raw_fixture["seed"]),
                "result": hex_to_bytes32(raw_fixture["result"]),
                "cache_size": Uint(raw_fixture["cache_size"]),
                "dataset_size": Uint(raw_fixture["full_size"]),
                "header_hash": hex_to_bytes32(raw_fixture["header_hash"]),
                "cache_hash": hex_to_bytes32(raw_fixture["cache_hash"]),
            }
            for raw_fixture in json.load(pow_test_file_handler).values()
        ]


@pytest.mark.slow
@pytest.mark.parametrize("json_fork", POW_FORKS)
@pytest.mark.parametrize(
    "block_file_name",
    [
        "block_1.json",
        "block_1234567.json",
        "block_12964999.json",
    ],
)
def test_pow_validation_block_headers(
    json_fork: str, block_file_name: str
) -> None:
    eels_fork = FORKS[json_fork]["eels_fork"]
    fork_module = importlib.import_module(f"ethereum.{eels_fork}.fork")

    block_str_data = cast(
        bytes, pkgutil.get_data("ethereum", f"assets/blocks/{block_file_name}")
    ).decode()
    block_json_data = json.loads(block_str_data)

    load = Load(json_fork, eels_fork)
    header = load.json_to_header(block_json_data)
    fork_module.validate_proof_of_work(header)


# TODO: Once there is a method to download blocks, test the proof-of-work
# validation for the following blocks in each hardfork (except London as the
# current PoW algo won't work from London):
#   * Start of hardfork
#   * two random blocks inside the hardfork
#   * End of hardfork
