"""
Types and functions for beginning a new chain.

_Genesis_ is the term for the beginning of a new chain, and so a genesis block
is a block with no parent (its [`parent_hash`] is all zeros.)

The genesis configuration for a chain is specified with a
[`GenesisConfiguration`], and genesis blocks are created with
[`add_genesis_block`].

[`parent_hash`]: ref:ethereum.frontier.blocks.Header.parent_hash
[`GenesisConfiguration`]: ref:ethereum.genesis.GenesisConfiguration
[`add_genesis_block`]: ref:ethereum.genesis.add_genesis_block
"""
import json
import pkgutil
from dataclasses import dataclass
from typing import Any, Dict, Type

from ethereum import rlp
from ethereum.base_types import (
    U64,
    U256,
    Bytes,
    Bytes8,
    FixedBytes,
    Uint,
    slotted_freezable,
)
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_u256,
    hex_to_uint,
)


@slotted_freezable
@dataclass
class GenesisConfiguration:
    """
    Configuration for the first block of an Ethereum chain.

    Specifies the allocation of ether set out in the pre-sale, and some of
    the fields of the genesis block.
    """

    chain_id: U64
    """
    Discriminant between diverged blockchains; `1` for Ethereum's main network.
    """

    difficulty: Uint
    """
    See [`difficulty`] (and subsequent forks.)

    [`difficulty`]: ref:ethereum.frontier.blocks.Header.difficulty
    """

    extra_data: Bytes
    """
    See [`extra_data`] (and subsequent forks.)

    [`extra_data`]: ref:ethereum.frontier.blocks.Header.extra_data
    """

    gas_limit: Uint
    """
    See [`gas_limit`] (and subsequent forks.)

    [`gas_limit`]: ref:ethereum.frontier.blocks.Header.gas_limit
    """

    nonce: Bytes8
    """
    See [`nonce`] (and subsequent forks.)

    [`nonce`]: ref:ethereum.frontier.blocks.Header.nonce
    """

    timestamp: U256
    """
    See [`timestamp`] (and subsequent forks.)

    [`timestamp`]: ref:ethereum.frontier.blocks.Header.timestamp
    """

    initial_accounts: Dict[str, Dict]
    """
    State of the blockchain at genesis.
    """


def get_genesis_configuration(genesis_file: str) -> GenesisConfiguration:
    """
    Read a genesis configuration from the given JSON file path.

    The genesis file should be present in the `assets` directory.
    """
    genesis_path = f"assets/{genesis_file}"
    genesis_bytes = pkgutil.get_data("ethereum", genesis_path)
    if genesis_bytes is None:
        raise Exception(f"Unable to read genesis from `{genesis_path}`")

    genesis_data = json.loads(genesis_bytes.decode())

    return GenesisConfiguration(
        chain_id=U64(genesis_data["config"]["chainId"]),
        difficulty=hex_to_uint(genesis_data["difficulty"]),
        extra_data=hex_to_bytes(genesis_data["extraData"]),
        gas_limit=hex_to_uint(genesis_data["gasLimit"]),
        nonce=hex_to_bytes8(genesis_data["nonce"]),
        timestamp=hex_or_base_10_str_to_u256(genesis_data["timestamp"]),
        initial_accounts=genesis_data["alloc"],
    )


def hex_or_base_10_str_to_u256(balance: str) -> U256:
    """
    Convert a string in either hexadecimal or base-10 to a [`U256`].

    [`U256`]: ref:ethereum.base_types.U256
    """
    if balance.startswith("0x"):
        return hex_to_u256(balance)
    else:
        return U256(int(balance))


def add_genesis_block(
    hardfork: Any, chain: Any, genesis: GenesisConfiguration
) -> None:
    """
    Adds the genesis block to an empty blockchain.

    The genesis block is an entirely sui generis block (unique) that is not
    governed by the general rules applying to all other Ethereum blocks.
    Instead, the only consensus requirement is that it must be identical to
    the block added by this function.

    The mainnet genesis configuration was originally created using the
    `mk_genesis_block.py` script. It is long since defunct, but is still
    available at <https://github.com/ethereum/genesis_block_generator>.

    The initial state is populated with balances based on the Ethereum presale
    that happened on the Bitcoin blockchain. Additional ether worth 1.98% of
    the presale was given to the foundation.

    The `state_root` is set to the root of the initial state. The `gas_limit`
    and `difficulty` are set to suitable starting values. In particular the
    low gas limit made sending transactions impossible in the early stages of
    Frontier.

    The `nonce` field is `0x42` referencing Douglas Adams' "HitchHiker's Guide
    to the Galaxy".

    The `extra_data` field contains the hash of block `1028201` on
    the pre-launch Olympus testnet. The creation of block `1028201` on Olympus
    marked the "starting gun" for Ethereum block creation. Including its hash
    in the genesis block ensured a fair launch of the Ethereum mining process.

    The remaining fields are set to appropriate default values.

    On testnets the genesis configuration usually allocates 1 wei to addresses
    `0x00` to `0xFF` to avoid edge cases around precompiles being created or
    cleared (by [EIP-161]).

    [EIP-161]: https://eips.ethereum.org/EIPS/eip-161
    """
    Address: Type[FixedBytes] = hardfork.fork_types.Address
    assert issubclass(Address, FixedBytes)

    for address, account in genesis.initial_accounts.items():
        address = hardfork.utils.hexadecimal.hex_to_address(address)
        hardfork.state.set_account(
            chain.state,
            address,
            hardfork.fork_types.Account(
                Uint(int(account.get("nonce", "0"))),
                hex_or_base_10_str_to_u256(account.get("balance", 0)),
                hex_to_bytes(account.get("code", "0x")),
            ),
        )
        for key, value in account.get("storage", {}).items():
            hardfork.state.set_storage(
                chain.state, address, hex_to_bytes32(key), hex_to_uint(value)
            )

    fields = {
        "parent_hash": hardfork.fork_types.Hash32(b"\0" * 32),
        "ommers_hash": rlp.rlp_hash(()),
        "coinbase": Address(b"\0" * Address.LENGTH),
        "state_root": hardfork.state.state_root(chain.state),
        "transactions_root": hardfork.trie.root(
            hardfork.trie.Trie(False, None)
        ),
        "receipt_root": hardfork.trie.root(hardfork.trie.Trie(False, None)),
        "bloom": hardfork.fork_types.Bloom(b"\0" * 256),
        "difficulty": genesis.difficulty,
        "number": Uint(0),
        "gas_limit": genesis.gas_limit,
        "gas_used": Uint(0),
        "timestamp": genesis.timestamp,
        "extra_data": genesis.extra_data,
        "nonce": genesis.nonce,
    }

    if hasattr(hardfork.blocks.Header, "mix_digest"):
        fields["mix_digest"] = hardfork.fork_types.Hash32(b"\0" * 32)
    else:
        fields["prev_randao"] = hardfork.fork_types.Hash32(b"\0" * 32)

    if hasattr(hardfork.blocks.Header, "base_fee_per_gas"):
        fields["base_fee_per_gas"] = Uint(10**9)

    genesis_header = hardfork.blocks.Header(**fields)

    genesis_block = hardfork.blocks.Block(
        header=genesis_header,
        transactions=(),
        ommers=(),
    )

    chain.blocks.append(genesis_block)
    chain.chain_id = genesis.chain_id
