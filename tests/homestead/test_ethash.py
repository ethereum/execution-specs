import json
import pkgutil
import shutil
import subprocess
from random import randint
from typing import Any, Dict, List, Tuple, cast

import pytest

from ethereum import rlp
from ethereum.base_types import U256_CEIL_VALUE, Uint
from ethereum.crypto.hash import keccak256
from ethereum.ethash import (
    EPOCH_SIZE,
    HASH_BYTES,
    MIX_BYTES,
    cache_size,
    dataset_size,
    epoch,
    generate_cache,
    generate_dataset_item,
    generate_seed,
    hashimoto_light,
)
from ethereum.homestead.eth_types import Header
from ethereum.homestead.spec import (
    generate_header_hash_for_pow,
    validate_proof_of_work,
)
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
)
from ethereum.utils.numeric import is_prime, le_uint32_sequence_to_bytes

from ..helpers.load_state_tests import Load


@pytest.mark.parametrize(
    "block_number, expected_epoch",
    [
        (Uint(0), Uint(0)),
        (Uint(29999), Uint(0)),
        (Uint(30000), Uint(1)),
    ],
)
def test_epoch(block_number: Uint, expected_epoch: Uint) -> None:
    assert epoch(block_number) == expected_epoch


def test_epoch_start_and_end_blocks_have_same_epoch() -> None:
    for _ in range(100):
        block_number = Uint(randint(10 ** 9, 2 * (10 ** 9)))
        epoch_start_block_number = (block_number // EPOCH_SIZE) * EPOCH_SIZE
        epoch_end_block_number = epoch_start_block_number + EPOCH_SIZE - 1

        assert (
            epoch(block_number)
            == epoch(epoch_start_block_number)
            == epoch(epoch_end_block_number)
        )


def test_cache_size_1st_epoch() -> None:
    assert (
        cache_size(Uint(0)) == cache_size(Uint(0) + EPOCH_SIZE - 1) == 16776896
    )
    assert is_prime(cache_size(Uint(0)) // HASH_BYTES)


def test_cache_size_2048_epochs() -> None:
    cache_size_2048_epochs = json.loads(
        cast(
            bytes,
            pkgutil.get_data(
                "ethereum", "assets/cache_sizes_2048_epochs.json"
            ),
        ).decode()
    )
    assert len(cache_size_2048_epochs) == 2048

    for epoch_number in range(2048):
        assert (
            cache_size(Uint(epoch_number * EPOCH_SIZE))
            == cache_size_2048_epochs[epoch_number]
        )


def test_epoch_start_and_end_blocks_have_same_cache_size() -> None:
    for _ in range(100):
        block_number = Uint(randint(10 ** 9, 2 * (10 ** 9)))
        epoch_start_block_number = (block_number // EPOCH_SIZE) * EPOCH_SIZE
        epoch_end_block_number = epoch_start_block_number + EPOCH_SIZE - 1

        assert (
            cache_size(block_number)
            == cache_size(epoch_start_block_number)
            == cache_size(epoch_end_block_number)
        )


def test_dataset_size_1st_epoch() -> None:
    assert (
        dataset_size(Uint(0))
        == dataset_size(Uint(0 + EPOCH_SIZE - 1))
        == 1073739904
    )
    assert is_prime(dataset_size(Uint(0)) // MIX_BYTES)


def test_dataset_size_2048_epochs() -> None:
    dataset_size_2048_epochs = json.loads(
        cast(
            bytes,
            pkgutil.get_data(
                "ethereum", "assets/dataset_sizes_2048_epochs.json"
            ),
        ).decode()
    )
    assert len(dataset_size_2048_epochs) == 2048

    for epoch_number in range(2048):
        assert (
            dataset_size(Uint(epoch_number * EPOCH_SIZE))
            == dataset_size_2048_epochs[epoch_number]
        )


def test_epoch_start_and_end_blocks_have_same_dataset_size() -> None:
    for _ in range(100):
        block_number = Uint(randint(10 ** 9, 2 * (10 ** 9)))
        epoch_start_block_number = (block_number // EPOCH_SIZE) * EPOCH_SIZE
        epoch_end_block_number = epoch_start_block_number + EPOCH_SIZE - 1

        assert (
            dataset_size(block_number)
            == dataset_size(epoch_start_block_number)
            == dataset_size(epoch_end_block_number)
        )


def test_seed() -> None:
    assert (
        generate_seed(Uint(0))
        == generate_seed(Uint(0 + EPOCH_SIZE - 1))
        == b"\x00" * 32
    )
    assert (
        generate_seed(Uint(EPOCH_SIZE))
        == generate_seed(Uint(2 * EPOCH_SIZE - 1))
        == keccak256(b"\x00" * 32)
    )
    # NOTE: The below bytes value was obtained by obtaining the seed for the same block number from Geth.
    assert (
        generate_seed(Uint(12345678))
        == b"[\x8c\xa5\xaaC\x05\xae\xed<\x87\x1d\xbc\xabQBGj\xfd;\x9cJ\x98\xf6Dq\\z\xaao\x1c\xf7\x03"
    )


def test_epoch_start_and_end_blocks_have_same_seed() -> None:
    for _ in range(100):
        block_number = Uint(randint(10000, 20000))
        epoch_start_block_number = (block_number // EPOCH_SIZE) * EPOCH_SIZE
        epoch_end_block_number = epoch_start_block_number + EPOCH_SIZE - 1

        assert (
            generate_seed(epoch_start_block_number)
            == generate_seed(block_number)
            == generate_seed(epoch_end_block_number)
        )


def test_ethtest_fixtures() -> None:
    ethereum_tests = load_pow_test_fixtures()
    for test in ethereum_tests:
        header = test["header"]
        assert header.nonce == test["nonce"]
        assert header.mix_digest == test["mix_digest"]
        assert generate_seed(header.number) == test["seed"]
        assert cache_size(header.number) == test["cache_size"]
        assert dataset_size(header.number) == test["dataset_size"]

        header_hash = generate_header_hash_for_pow(header)
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


def load_pow_test_fixtures() -> List[Dict[str, Any]]:
    with open(
        "tests/fixtures/PoWTests/ethash_tests.json"
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
@pytest.mark.parametrize(
    "block_number, block_difficulty, header_hash, nonce, expected_mix_digest, expected_result",
    [
        [
            Uint(1),
            Uint(17171480576),
            "0x85913a3057ea8bec78cd916871ca73802e77724e014dda65add3405d02240eb7",
            "0x539bd4979fef1ec4",
            "0x969b900de27b6ac6a67742365dd65f55a0526c41fd18e1b16f1a1215c2e66f59",
            "0x000000002bc095dd4de049873e6302c3f14a7f2e5b5a1f60cdf1f1798164d610",
        ],
        [
            Uint(5),
            Uint(17154711556),
            "0xfe557bbc2346abe74c4e66b1843df7a884f83e3594a210d96594c455c32d33c1",
            "0xfba9d0cff9dc5cf3",
            "0x17b85b5ec310c4868249fa2f378c83b4f330e2d897e5373a8195946c71d1d19e",
            "0x000000000767f35d1d21220cb5c53e060afd84fadd622db784f0d4b0541c034a",
        ],
        [
            Uint(123456),
            Uint(4505282870523),
            "0xad896938ef53ff923b4336d03573d52c69097dabf8734d71b9546d31db603121",
            "0xf4b883fed83092b2",
            "0x84d4162717b039a996ffaf59a54158443c62201b76170b02dbad626cca3226d5",
            "0x00000000000fb25dfcfe2fcdc9a63c892ce795aba4380513a9705489bf247b07",
        ],
        [
            Uint(1000865),
            Uint(12652630789208),
            "0xcc868f6114e4cadc3876e4ca4e0705b2bcb76955f459bb019a80d72a512eefdb",
            "0xc6613bcf40e716d6",
            "0xce47e0609103ac85d56bf1637e51afd28e29431f47c11df47db80a63d95efbae",
            "0x000000000015de37404be3c9beda75e12ae41ef7c937dcd52130cfc3b389bf42",
        ],
    ],
)
def test_pow_random_blocks(
    block_number: Uint,
    block_difficulty: Uint,
    header_hash: str,
    nonce: str,
    expected_mix_digest: str,
    expected_result: str,
) -> None:
    mix_digest, result = hashimoto_light(
        hex_to_bytes32(header_hash),
        hex_to_bytes8(nonce),
        generate_cache(block_number),
        dataset_size(block_number),
    )

    assert mix_digest == hex_to_bytes32(expected_mix_digest)
    assert result == hex_to_bytes(expected_result)
    assert Uint.from_be_bytes(result) <= U256_CEIL_VALUE // (block_difficulty)


@pytest.mark.slow
@pytest.mark.parametrize(
    "block_file_name",
    [
        "block_1.json",
        "block_1234567.json",
        "block_12964999.json",
    ],
)
def test_pow_validation_block_headers(block_file_name: str) -> None:
    block_str_data = cast(
        bytes, pkgutil.get_data("ethereum", f"assets/blocks/{block_file_name}")
    ).decode()
    block_json_data = json.loads(block_str_data)

    load = Load("Homestead", "homestead")
    header: Header = cast(Header, load.json_to_header(block_json_data))
    validate_proof_of_work(header)


# TODO: Once there is a method to download blocks, test the proof-of-work
# validation for the following blocks in each hardfork (except London as the
# current PoW algo won't work from London):
#   * Start of hardfork
#   * two random blocks inside the hardfork
#   * End of hardfork


#
# Geth DAG related functionalities for fuzz testing
#


def generate_dag_via_geth(
    geth_path: str, block_number: Uint, dag_dump_dir: str
) -> None:
    subprocess.call([geth_path, "makedag", str(block_number), dag_dump_dir])


def fetch_dag_data(dag_dump_dir: str, epoch_seed: bytes) -> Tuple[bytes, ...]:
    dag_file_path = f"{dag_dump_dir}/full-R23-{epoch_seed.hex()[:16]}"
    with open(dag_file_path, "rb") as fp:
        dag_dataset = fp.read()
        # The first 8 bytes are Magic Bytes and can be ignored.
        dag_dataset = dag_dataset[8:]

    dag_dataset_items = []
    for i in range(0, len(dag_dataset), HASH_BYTES):
        dag_dataset_items.append(dag_dataset[i : i + HASH_BYTES])

    return tuple(dag_dataset_items)


GETH_MISSING = """geth binary not found.

Some tests require a copy of the go-ethereum client binary to generate required
data.

The tool `scripts/download_geth_linux.py` can fetch the appropriate version, or
you can download geth from:

    https://geth.ethereum.org/downloads/

Make sure you add the directory containing `geth` to your PATH, then try
running the tests again.
"""


@pytest.mark.slow
def test_dataset_generation_random_epoch(tmpdir: str) -> None:
    """
    Generate a random epoch and obtain the DAG for that epoch from geth.
    Then ensure the following 2 test scenarios:
        1. The first 100 dataset indices are same when the python
        implementation is compared with the DAG dataset.
        2. Randomly take 500 indices between
        [101, `dataset size in words` - 1] and ensure that the values are
        same between python implementation and DAG dataset.

    NOTE - For this test case to run, it is mandatory for Geth to be
    installed and accessible
    """
    geth_path = shutil.which("geth")
    if geth_path is None:
        raise Exception(GETH_MISSING)

    epoch_number = Uint(randint(0, 100))
    block_number = epoch_number * EPOCH_SIZE + randint(0, EPOCH_SIZE - 1)
    generate_dag_via_geth(geth_path, block_number, f"{tmpdir}/.ethash")
    seed = generate_seed(block_number)
    dag_dataset = fetch_dag_data(f"{tmpdir}/.ethash", seed)

    cache = generate_cache(block_number)
    dataset_size_bytes = dataset_size(block_number)
    dataset_size_words = dataset_size_bytes // HASH_BYTES

    assert len(dag_dataset) == dataset_size_words

    assert generate_dataset_item(cache, Uint(0)) == dag_dataset[0]

    for i in range(100):
        assert generate_dataset_item(cache, Uint(i)) == dag_dataset[i]

    # Then for this dataset randomly take 5000 indices and check the
    # data obtained from our implementation with geth DAG
    for _ in range(500):
        index = Uint(randint(101, dataset_size_words - 1))
        dataset_item = generate_dataset_item(cache, index)
        assert dataset_item == dag_dataset[index], index

    # Manually forcing the dataset out of the memory incase the gc
    # doesn't kick in immediately
    del dag_dataset
