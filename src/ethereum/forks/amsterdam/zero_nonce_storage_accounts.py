"""
Zero-Nonce Storage Accounts.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

One-time state transition at the fork block, specified by [EIP-8253], that
sets the nonce of every Mainnet account with empty code, a zero nonce, and
non-empty storage to one.

Before Spurious Dragon ([EIP-161]) a contract creation could write to
storage and then return empty code. Such an account has no code and a zero
nonce, so it satisfies the [EIP-684] preconditions for a later contract
creation at the same address, which would then inherit the old storage.
[EIP-7610] closed this hole with a storage check on every creation. Bumping
the nonce of the remaining Mainnet accounts to one makes them fail the
[EIP-684] nonce check instead, so no storage check is needed at runtime.

The transition happens at the start of the fork block, before the
pre-execution system contract calls and before any transaction. It
produces no transaction, receipt, or log, and consumes no gas. If the block
carries a block access list ([EIP-7928]), each targeted account records a
single nonce change from zero to one at block access index zero.

[EIP-161]: https://eips.ethereum.org/EIPS/eip-161
[EIP-684]: https://eips.ethereum.org/EIPS/eip-684
[EIP-7610]: https://eips.ethereum.org/EIPS/eip-7610
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
[EIP-8253]: https://eips.ethereum.org/EIPS/eip-8253
"""

from typing import Tuple

from ethereum_types.numeric import Uint

from ethereum.state import Account, Address

from .fork_types import BlockAccessIndex
from .state_tracker import (
    TransactionState,
    incorporate_tx_into_block,
    modify_state,
)
from .utils.hexadecimal import hex_to_address
from .vm import BlockEnvironment

ZERO_NONCE_STORAGE_ACCOUNTS: Tuple[Address, ...] = tuple(
    hex_to_address(address)
    for address in [
        "0xf468bcbc4a0bfdb06336e773382c5202e674db71",
        "0xd8253352f6044cfe55bcc0748c3fa37b7df81f98",
        "0x5983c6ac846dcf85fbbc4303f43eb91c379f79ae",
        "0xde425ad4b8d2d9e0e12f65cbcd6d55f447b44083",
        "0x50b1497068bae652df3562eb8ea7677ff84477fa",
        "0x8398ff6c618e9515468c1c4b198d53666cbe8462",
        "0x6f156dbf8ed30e53f7c9df73144e69f65cbb7e94",
        "0x2c081ed1949d7dd9447f9d96e509befe576d4461",
        "0xdb7c577b93baeb56dab50af4d6f86f99a06b96a2",
        "0x14725085d004f1b10ee07234a4ab28c5ad2a7b9e",
        "0xae3703584494ade958ad27ec2d289b7a67c19e90",
        "0x7d6ae067de8d44ae1a08750e7d626d61a623c44a",
        "0x4d149eb99bdeefc1f858f8fd22289c6beae99f2c",
        "0x361d7a60b43587c7f6bba4f9fd9642747f65210a",
        "0xb619f45637c39ca49a41ac64c11637a0a194455e",
        "0x5071cb62aa170b7f66b26cae8004d90e6078bb1e",
        "0xadd92e0650457c5db0c4c08cbf7ca580175d33d2",
        "0x3311c08066580cb906a7287b6786e504c2ebd09f",
        "0x02820e4bee488c40f7455fdca53125565148708f",
        "0xe62dc49c92fa799033644d2a9afd7e3babe5a80a",
        "0x5cc182fabfb81a056b6080d4200bc5150673d06f",
        "0xf4a835ec1364809003de3925685f24cd360bdffe",
        "0xfc4465f84b29a1f8794dc753f41bef1f4b025ed2",
        "0x40490c9c468622d5c89646d6f3097f8eaf80c411",
        "0xa21b22389bfc1cd6bc7ba19a4fc96adc3d0fe074",
        "0x59ec0410867828e3b8c23dd8a29d9796ef523b17",
        "0x19272418753b90d9a3e3efc8430b1612c55fcb3a",
        "0xfee7707fa4b8c0a923a0e40399db3e7ce26069c6",
    ]
)
"""
Mainnet accounts whose nonce is set to one at the fork block.

These are the 28 accounts that, at the time [EIP-8253] was written, still
had empty code, a zero nonce, and non-empty storage. All of them were
created before Spurious Dragon by a contract creation that stored to
storage and returned empty code. The list is ordered by the `keccak256`
hash of the address, matching the `targeted-accounts.json` asset of the
EIP, which also documents how the list was constructed and verified.

The list is specific to Mainnet. Chains forked from Mainnet after Spurious
Dragon share it; other chains have to derive their own.

[EIP-8253]: https://eips.ethereum.org/EIPS/eip-8253
"""


def bump_zero_nonce_storage_accounts(block_env: BlockEnvironment) -> None:
    """
    Set the nonce of every account in [`ZERO_NONCE_STORAGE_ACCOUNTS`] to one.

    Only called for the fork block. The balance, code, and storage of each
    account are left untouched. The change is applied unconditionally: an
    account that is missing from the state is created with a nonce of one,
    a zero balance, and no code.

    The block access list builder is still at block access index zero, so
    the nonce changes are recorded before any pre-execution system contract
    call, as [EIP-8253] requires.

    [`ZERO_NONCE_STORAGE_ACCOUNTS`]: ref:ethereum.forks.amsterdam.zero_nonce_storage_accounts.ZERO_NONCE_STORAGE_ACCOUNTS
    [EIP-8253]: https://eips.ethereum.org/EIPS/eip-8253

    Parameters
    ----------
    block_env :
        The block scoped environment of the fork block.

    """  # noqa: E501
    assert block_env.block_access_list_builder.block_access_index == (
        BlockAccessIndex(0)
    )

    fork_state = TransactionState(parent=block_env.state)

    def set_nonce_to_one(account: Account) -> None:
        account.nonce = Uint(1)

    for address in ZERO_NONCE_STORAGE_ACCOUNTS:
        modify_state(fork_state, address, set_nonce_to_one)

    incorporate_tx_into_block(fork_state, block_env.block_access_list_builder)
