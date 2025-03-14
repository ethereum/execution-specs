"""Pytest fixtures and classes for the `consume rlp` hive simulator."""

import io
from typing import List, Mapping, cast

import pytest

from ethereum_test_base_types import Bytes
from ethereum_test_fixtures import BlockchainFixture
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream

TestCase = TestCaseIndexFile | TestCaseStream


def pytest_configure(config):
    """Set the supported fixture formats for the rlp simulator."""
    config._supported_fixture_formats = [BlockchainFixture.format_name]


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eest/consume-rlp"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return "Execute blockchain tests by providing RLP-encoded blocks to a client upon start-up."


@pytest.fixture(scope="function")
def blocks_rlp(fixture: BlockchainFixture) -> List[Bytes]:
    """List of the fixture's blocks encoded as RLP."""
    return [block.rlp for block in fixture.blocks]


@pytest.fixture(scope="function")
def buffered_blocks_rlp(blocks_rlp: List[bytes]) -> List[io.BufferedReader]:
    """Convert the RLP-encoded blocks of the current test fixture to buffered readers."""
    block_rlp_files = []
    for _, block_rlp in enumerate(blocks_rlp):
        block_rlp_stream = io.BytesIO(block_rlp)
        block_rlp_files.append(io.BufferedReader(cast(io.RawIOBase, block_rlp_stream)))
    return block_rlp_files


@pytest.fixture(scope="function")
def client_files(
    buffered_genesis: io.BufferedReader,
    buffered_blocks_rlp: list[io.BufferedReader],
) -> Mapping[str, io.BufferedReader]:
    """
    Define the files that hive will start the client with.

    The files are specified as a dictionary whose:
    - Keys are the target file paths in the client's docker container, and,
    - Values are in-memory buffered file objects.
    """
    files = {f"/blocks/{i + 1:04d}.rlp": rlp for i, rlp in enumerate(buffered_blocks_rlp)}
    files["/genesis.json"] = buffered_genesis
    return files
