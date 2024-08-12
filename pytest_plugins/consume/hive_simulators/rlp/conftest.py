"""
Pytest fixtures and classes for the `consume rlp` hive simulator.
"""

import io
from pathlib import Path
from typing import List, Mapping, cast

import pytest

from ethereum_test_base_types import Bytes
from ethereum_test_fixtures import BlockchainFixture
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_fixtures.file import BlockchainFixtures
from pytest_plugins.consume.consume import JsonSource

TestCase = TestCaseIndexFile | TestCaseStream


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """
    The name of the hive test suite used in this simulator.
    """
    return "eest-block-rlp"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """
    The description of the hive test suite used in this simulator.
    """
    return "Execute blockchain tests by providing RLP-encoded blocks to a client upon start-up."


@pytest.fixture(scope="function")
def blockchain_fixture(fixture_source: JsonSource, test_case: TestCase) -> BlockchainFixture:
    """
    Create the blockchain fixture pydantic model for the current test case.

    The fixture is either already available within the test case (if consume
    is taking input on stdin) or loaded from the fixture json file if taking
    input from disk (fixture directory with index file).
    """
    if fixture_source == "stdin":
        assert isinstance(test_case, TestCaseStream), "Expected a stream test case"
        assert isinstance(
            test_case.fixture, BlockchainFixture
        ), "Expected a blockchain test fixture"
        fixture = test_case.fixture
    else:
        assert isinstance(test_case, TestCaseIndexFile), "Expected an index file test case"
        # TODO: Optimize, json files will be loaded multiple times. This pytest fixture
        # is executed per test case, and a fixture json will contain multiple test cases.
        fixtures = BlockchainFixtures.from_file(Path(fixture_source) / test_case.json_path)
        fixture = fixtures[test_case.id]
    return fixture


@pytest.fixture(scope="function")
def blocks_rlp(blockchain_fixture: BlockchainFixture) -> List[Bytes]:
    """
    A list of the fixture's blocks encoded as RLP.
    """
    return [block.rlp for block in blockchain_fixture.blocks]


@pytest.fixture(scope="function")
def buffered_blocks_rlp(blocks_rlp: List[bytes]) -> List[io.BufferedReader]:
    """
    Convert the RLP-encoded blocks of the current test fixture to buffered readers.
    """
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
