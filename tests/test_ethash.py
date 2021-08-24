import json
import multiprocessing as mp
import os
import pkgutil
import shutil
import subprocess
import tarfile
import tempfile
from random import randint
from typing import Tuple, cast

import pytest
import requests

from ethereum.base_types import Uint
from ethereum.crypto import keccak256
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
)
from ethereum.utils.numeric import is_prime


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


#
# Geth DAG related functionalities for fuzz testing
#


def download_geth(dir: str) -> None:
    geth_release_name = "geth-linux-amd64-1.10.8-26675454"
    # 26 seconds to fetch Geth. 1.5 minute for each epoch dataset creation
    url = f"https://gethstore.blob.core.windows.net/builds/{geth_release_name}.tar.gz"
    r = requests.get(url)

    with open(f"{dir}/geth.tar.gz", "wb") as f:
        f.write(r.content)

    geth_tar = tarfile.open(f"{dir}/geth.tar.gz")
    geth_tar.extractall(dir)

    shutil.move(f"{dir}/{geth_release_name}/geth", dir)
    shutil.rmtree(f"{dir}/{geth_release_name}", ignore_errors=True)
    os.remove(f"{dir}/geth.tar.gz")


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


def test_dataset_generation_random_epoch(tmpdir: str) -> None:
    """
    Generate a random epoch and obtain the DAG for that epoch from geth.
    Then ensure the following 2 test scenarios:
        1. The first 100 dataset indices are same when the python
        implementation is compared with the DAG dataset.
        2. Randomly take 500 indices between
        [101, `dataset size in words` - 1] and ensure that the values are
        same between python implementation and DAG dataset.
    """
    download_geth(tmpdir)

    epoch_number = Uint(randint(0, 100))
    block_number = epoch_number * EPOCH_SIZE + randint(0, EPOCH_SIZE - 1)
    generate_dag_via_geth(f"{tmpdir}/geth", block_number, f"{tmpdir}/.ethash")
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
