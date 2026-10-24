# Overlay on the fork's `fork.py`: install the EVM replacement for the
# identity precompile when the fork activates.

from ethereum.state import EMPTY_ACCOUNT, Account
from ethereum.state_mpt import set_account, store_code

from .evmified_precompiles import IDENTITY_ADDRESS, IDENTITY_EVM_CODE


def apply_fork(old: BlockChain) -> BlockChain:
    """
    Transforms the state from the previous hard fork (`old`) into the block
    chain object for this hard fork and returns it.

    As required by [EIP-7666], the EVM replacement for the retired identity
    precompile is installed at its address when this fork activates. Only the
    code is installed: the account's other fields are left untouched, so a
    previously nonexistent account keeps a zero nonce and any balance the
    account held before the fork is preserved.

    Parameters
    ----------
    old :
        Previous block chain object.

    Returns
    -------
    new : `BlockChain`
        Upgraded block chain object for this hard fork.

    [EIP-7666]: https://eips.ethereum.org/EIPS/eip-7666

    """
    state = old.state
    existing_account = state.get_account_optional(IDENTITY_ADDRESS)
    if existing_account is None:
        existing_account = EMPTY_ACCOUNT
    code_hash = store_code(state, IDENTITY_EVM_CODE)
    set_account(
        state,
        IDENTITY_ADDRESS,
        Account(
            nonce=existing_account.nonce,
            balance=existing_account.balance,
            code_hash=code_hash,
        ),
    )
    return old
