"""
A hive based simulator that executes RLP-encoded blocks against clients. The simulator uses the
`BlockchainFixtures` to test this against clients.

Clients consume the genesis and RLP-encoded blocks from input files upon start-up.
"""

import time

from ethereum_test_fixtures import BlockchainFixture
from ethereum_test_fixtures.blockchain import FixtureHeader
from ethereum_test_tools.rpc import EthRPC
from pytest_plugins.consume.hive_simulators.exceptions import GenesisBlockMismatchException


def test_via_rlp(
    timing_data,
    eth_rpc: EthRPC,
    blockchain_fixture: BlockchainFixture,
):
    """
    1. Check the client genesis block hash matches `blockchain_fixture.genesis.block_hash`.
    2. Check the client last block hash matches `blockchain_fixture.last_block_hash`.
    """
    t_rlp = time.perf_counter()
    genesis_block = eth_rpc.get_block_by_number(0)
    timing_data.get_genesis = time.perf_counter() - t_rlp
    if genesis_block["hash"] != str(blockchain_fixture.genesis.block_hash):
        raise GenesisBlockMismatchException(
            expected_header=blockchain_fixture.genesis, got_header=FixtureHeader(**genesis_block)
        )
    block = eth_rpc.get_block_by_number("latest")
    timing_data.test_case_execution = time.perf_counter() - timing_data.get_genesis - t_rlp
    assert block["hash"] == str(blockchain_fixture.last_block_hash), "hash mismatch in last block"
