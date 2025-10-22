"""
A hive based simulator that executes RLP-encoded blocks against clients. The
simulator uses the `BlockchainFixtures` to test this against clients.

Clients consume the genesis and RLP-encoded blocks from input files upon
start-up.
"""

import logging

from ethereum_test_fixtures import BlockchainFixture
from ethereum_test_fixtures.blockchain import FixtureBlock, FixtureHeader
from ethereum_test_rpc import EthRPC

from ..helpers.exceptions import GenesisBlockMismatchExceptionError
from ..helpers.timing import TimingData

logger = logging.getLogger(__name__)


def test_via_rlp(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    fixture: BlockchainFixture,
) -> None:
    """
    1. Check the client genesis block hash matches
       `fixture.genesis.block_hash`.
    2. Check the client last block hash matches `fixture.last_block_hash`.
    """
    with timing_data.time("Get genesis block"):
        logger.info("Calling getBlockByNumber to get genesis block...")
        genesis_block = eth_rpc.get_block_by_number(0)
        assert genesis_block, "`getBlockByNumber` didn't return a block."
        if genesis_block["hash"] != str(fixture.genesis.block_hash):
            raise GenesisBlockMismatchExceptionError(
                expected_header=fixture.genesis,
                got_genesis_block=genesis_block,
            )
    with timing_data.time("Get latest block"):
        logger.info("Calling getBlockByNumber to get latest block...")
        block = eth_rpc.get_block_by_number("latest")
        assert block, "`getBlockByNumber` didn't return a block."
        if block["hash"] != str(fixture.last_block_hash):
            try:
                block_header = FixtureHeader.model_validate(block).model_dump()
                last_block = FixtureBlock.model_validate(fixture.blocks[-1])
                last_block_header = last_block.header.model_dump()

                if block_header["number"] != last_block_header["number"]:
                    # raise with clearer message if block number mismatches
                    raise AssertionError(
                        f"block number mismatch in last block: got "
                        f"`{block_header['number']}`, "
                        f"expected `{last_block_header['number']}``"
                    )

                # find all mismatched fields
                mismatches = []
                for block_field, block_value in block_header.items():
                    fixture_value = last_block_header[block_field]
                    if str(block_value) != str(fixture_value):
                        mismatches.append(
                            f"    {block_field}: got `{block_value}`, expected `{fixture_value}`"
                        )
                raise AssertionError(
                    "blockHash mismatch in last block - field mismatches:"
                    "\n" + "\n".join(mismatches)
                )
            except Exception:
                raise AssertionError(
                    f"blockHash mismatch in last block: got `{block['hash']}`, "
                    f"expected `{fixture.last_block_hash}`"
                ) from None
