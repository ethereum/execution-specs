import pytest
from ethereum_rlp import rlp
from ethereum_types.numeric import U64

from ethereum.crypto.hash import keccak256
from ethereum.frontier.blocks import Block, Header
from ethereum.frontier.fork import BlockChain
from ethereum.frontier.fork_types import Account, Address, Bloom
from ethereum.frontier.state import State, set_account, set_storage, state_root
from ethereum.frontier.trie import Trie, root
from ethereum.frontier.utils.hexadecimal import hex_to_address
from ethereum.genesis import (
    GenesisFork,
    add_genesis_block,
    get_genesis_configuration,
)
from ethereum.utils.hexadecimal import hex_to_hash
from ethereum_spec_tools.forks import Hardfork

MAINNET_GENESIS_CONFIGURATION = get_genesis_configuration("mainnet.json")


def test_frontier_block_hash() -> None:
    description: GenesisFork[
        Address, Account, State, Trie, Bloom, Header, Block
    ] = GenesisFork(
        Address=Address,
        Account=Account,
        Trie=Trie,
        Bloom=Bloom,
        Header=Header,
        Block=Block,
        set_account=set_account,
        set_storage=set_storage,
        state_root=state_root,
        root=root,
        hex_to_address=hex_to_address,
    )

    chain = BlockChain([], State(), U64(1))
    add_genesis_block(description, chain, MAINNET_GENESIS_CONFIGURATION)

    assert keccak256(rlp.encode(chain.blocks[0].header)) == hex_to_hash(
        "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
    )


def fork_name(fork: Hardfork) -> str:
    return fork.short_name


@pytest.mark.parametrize("fork", Hardfork.discover(), ids=fork_name)
def test_genesis(fork: Hardfork) -> None:
    description: GenesisFork = GenesisFork(
        Address=fork.module("fork_types").Address,
        Account=fork.module("fork_types").Account,
        Trie=fork.module("trie").Trie,
        Bloom=fork.module("fork_types").Bloom,
        Header=fork.module("blocks").Header,
        Block=fork.module("blocks").Block,
        set_account=fork.module("state").set_account,
        set_storage=fork.module("state").set_storage,
        state_root=fork.module("state").state_root,
        root=fork.module("trie").root,
        hex_to_address=fork.module("utils.hexadecimal").hex_to_address,
    )

    state = fork.module("state").State()
    chain = fork.module("fork").BlockChain([], state, U64(1))
    add_genesis_block(description, chain, MAINNET_GENESIS_CONFIGURATION)

    assert len(chain.blocks) == 1
