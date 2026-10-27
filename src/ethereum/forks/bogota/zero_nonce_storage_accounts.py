"""
Zero-Nonce Storage Accounts.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

One-time state transition at the fork block, specified by [EIP-8253], that
sets the nonce of every account in a per-chain list of accounts with empty
code, a zero nonce, and non-empty storage to one.

Before Spurious Dragon ([EIP-161]) a contract creation could write to
storage and then return empty code. Such an account has no code and a zero
nonce, so it satisfies the [EIP-684] preconditions for a later contract
creation at the same address, which would then inherit the old storage.
[EIP-7610] closed this hole with a storage check on every creation. Bumping
the nonce of the remaining accounts to one makes them fail the [EIP-684]
nonce check instead, so no storage check is needed at runtime.

The list of accounts is part of the chain configuration, like the chain
identifier. A chain without such accounts has an empty list, and on it the
transition does nothing.

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
from .vm import BlockEnvironment


def bump_zero_nonce_storage_accounts(
    block_env: BlockEnvironment, accounts: Tuple[Address, ...]
) -> None:
    """
    Set the nonce of every account in `accounts` to one.

    Only called for the fork block. The balance, code, and storage of each
    account are left untouched. The change is applied unconditionally: an
    account that is missing from the state is created with a nonce of one,
    a zero balance, and no code.

    The block access list builder is still at block access index zero, so
    the nonce changes are recorded before any pre-execution system contract
    call, as [EIP-8253] requires.

    [EIP-8253]: https://eips.ethereum.org/EIPS/eip-8253

    Parameters
    ----------
    block_env :
        The block scoped environment of the fork block.
    accounts :
        The zero-nonce storage accounts listed in the chain configuration.

    """
    assert block_env.block_access_list_builder.block_access_index == (
        BlockAccessIndex(0)
    )

    fork_state = TransactionState(parent=block_env.state)

    def set_nonce_to_one(account: Account) -> None:
        account.nonce = Uint(1)

    for address in accounts:
        modify_state(fork_state, address, set_nonce_to_one)

    incorporate_tx_into_block(fork_state, block_env.block_access_list_builder)
