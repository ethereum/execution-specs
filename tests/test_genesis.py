from ethereum import frontier, rlp
from ethereum.base_types import U64
from ethereum.crypto.hash import keccak256
from ethereum.frontier.fork import BlockChain
from ethereum.frontier.state import State
from ethereum.genesis import add_genesis_block, get_genesis_configuration
from ethereum.utils.hexadecimal import hex_to_hash

MAINNET_GENESIS_CONFIGURATION = get_genesis_configuration("mainnet.json")


def test_genesis_block_hash() -> None:
    chain = BlockChain([], State(), U64(1))
    add_genesis_block(frontier, chain, MAINNET_GENESIS_CONFIGURATION)

    assert keccak256(rlp.encode(chain.blocks[0].header)) == hex_to_hash(
        "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
    )
