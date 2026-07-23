"""
Set EOA account code.
"""

from typing import Optional, Set, Tuple

from ethereum_rlp import rlp
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidSignatureError
from ethereum.state import Address

from ..fork_types import Authorization
from ..state_tracker import (
    account_exists,
    get_account,
    get_code,
    get_pre_state_account,
    increment_nonce,
    set_code,
)
from ..utils.hexadecimal import hex_to_address
from ..vm.gas import (
    GasCosts,
    StateGasCosts,
    charge_gas,
    charge_state_gas,
)
from . import Evm, Message

SET_CODE_TX_MAGIC = b"\x05"
EOA_DELEGATION_MARKER = b"\xef\x01\x00"
EOA_DELEGATION_MARKER_LENGTH = len(EOA_DELEGATION_MARKER)
EOA_DELEGATED_CODE_LENGTH = 23
NULL_ADDRESS = hex_to_address("0x0000000000000000000000000000000000000000")


def is_valid_delegation(code: bytes) -> bool:
    """
    Whether the code is a valid delegation designation.

    Parameters
    ----------
    code: `bytes`
        The code to check.

    Returns
    -------
    valid : `bool`
        True if the code is a valid delegation designation,
        False otherwise.

    """
    return (
        len(code) == EOA_DELEGATED_CODE_LENGTH
        and code[:EOA_DELEGATION_MARKER_LENGTH] == EOA_DELEGATION_MARKER
    )


def get_delegated_code_address(code: bytes) -> Optional[Address]:
    """
    Get the address to which the code delegates.

    Parameters
    ----------
    code: `bytes`
        The code to get the address from.

    Returns
    -------
    address : `Optional[Address]`
        The address of the delegated code.

    """
    if is_valid_delegation(code):
        return Address(code[EOA_DELEGATION_MARKER_LENGTH:])
    return None


def recover_authority(authorization: Authorization) -> Address:
    """
    Recover the authority address from the authorization.

    Parameters
    ----------
    authorization
        The authorization to recover the authority from.

    Raises
    ------
    InvalidSignatureError
        If the signature is invalid.

    Returns
    -------
    authority : `Address`
        The recovered authority address.

    """
    y_parity, r, s = authorization.y_parity, authorization.r, authorization.s
    if y_parity not in (0, 1):
        raise InvalidSignatureError("Invalid y_parity in authorization")
    if U256(0) >= r or r >= SECP256K1N:
        raise InvalidSignatureError("Invalid r value in authorization")
    if U256(0) >= s or s > SECP256K1N // U256(2):
        raise InvalidSignatureError("Invalid s value in authorization")

    signing_hash = keccak256(
        SET_CODE_TX_MAGIC
        + rlp.encode(
            (
                authorization.chain_id,
                authorization.address,
                authorization.nonce,
            )
        )
    )

    public_key = secp256k1_recover(r, s, U256(y_parity), signing_hash)
    return Address(keccak256(public_key)[12:32])


def calculate_delegation_cost(
    evm: Evm, address: Address
) -> Tuple[bool, Address, Uint]:
    """
    Get the delegation address and the cost of access from the address.

    Parameters
    ----------
    evm : `Evm`
        The execution frame.
    address : `Address`
        The address to check for delegation.

    Returns
    -------
    delegation : `Tuple[bool, Address, Uint]`
        The delegation address and access gas cost.

    """
    tx_state = evm.message.tx_env.state

    code = get_code(tx_state, get_account(tx_state, address).code_hash)

    if not is_valid_delegation(code):
        return False, address, Uint(0)

    delegated_address = Address(code[EOA_DELEGATION_MARKER_LENGTH:])

    if delegated_address in evm.accessed_addresses:
        delegation_gas_cost = GasCosts.WARM_ACCESS
    else:
        delegation_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS

    return True, delegated_address, delegation_gas_cost


def validate_authorization(
    message: Message, auth: Authorization
) -> Optional[Address]:
    """
    Check if the given `Authorization` is valid against the current state.

    Returns the `authority` address, or `None` if the validation was
    unsuccessful.
    """
    tx_state = message.tx_env.state

    if auth.chain_id not in (message.block_env.chain_id, U256(0)):
        return None

    if auth.nonce >= U64.MAX_VALUE:
        return None

    try:
        authority = recover_authority(auth)
    except InvalidSignatureError:
        return None

    message.accessed_addresses.add(authority)

    authority_account = get_account(tx_state, authority)
    authority_code = get_code(tx_state, authority_account.code_hash)

    if authority_code and not is_valid_delegation(authority_code):
        return None

    authority_nonce = authority_account.nonce
    if authority_nonce != auth.nonce:
        return None

    return authority


def set_delegation(evm: Evm) -> None:
    """
    Apply the EIP-7702 authorizations and charge their state-dependent
    costs at the top frame.

    Each valid authorization is charged, on top of the
    state-independent ``GasCosts.REGULAR_PER_AUTH_BASE_COST`` already
    paid in the intrinsic cost:

    - ``StateGasCosts.NEW_ACCOUNT`` (state) when the authority's
      account leaf does not yet exist.
    - ``GasCosts.ACCOUNT_WRITE`` (regular) when applying the
      authorization is the transaction's first write to the authority's
      leaf. Writes the transaction already prices elsewhere are
      exempt: the sender's, covered by ``TX_BASE``, and, for a
      value-bearing transaction, the recipient's, covered by
      ``TX_VALUE_COST``. Repeated authorizations on one authority pay
      it once.
    - ``StateGasCosts.AUTH_BASE`` (state) when a net-new delegation
      indicator is written: the authority held no delegation before the
      transaction, none was set for it earlier in the transaction, and
      this authorization sets one. It is charged at most once per
      authority and is never credited back -- a delegation set and then
      cleared in the same transaction keeps its charge.

    These costs depend on the authority's current state and so cannot
    be charged in the intrinsic cost. Insufficient gas raises an
    ``OutOfGasError``; the caller rolls back the authorizations applied
    so far and halts the top frame.

    Parameters
    ----------
    evm :
        The top-level transaction frame.

    """
    message = evm.message
    tx_state = message.tx_env.state
    # Accounts whose write the transaction has already priced: the
    # sender's leaf was written at inclusion (nonce bump and fee
    # deduction), and a value-bearing transaction prepays the
    # recipient's balance write -- the transfer itself only happens at
    # frame entry, after these charges.
    written_accounts: Set[Address] = {message.tx_env.origin}
    if evm.message.tx_env.value > U256(0):
        written_accounts.add(evm.message.current_target)
    # Authorities a delegation was set for earlier in this transaction.
    delegation_set_for: Set[Address] = set()
    for auth in message.tx_env.authorizations:
        match validate_authorization(message, auth):
            case None:
                continue
            case authority:
                pass

        if not account_exists(tx_state, authority):
            charge_state_gas(evm, StateGasCosts.NEW_ACCOUNT)

        if authority not in written_accounts:
            charge_gas(evm, GasCosts.ACCOUNT_WRITE)
            written_accounts.add(authority)

        pre_state_authority_account = get_pre_state_account(
            tx_state, authority
        )
        pre_state_authority_code = get_code(
            tx_state, pre_state_authority_account.code_hash
        )
        delegated_before_tx = is_valid_delegation(pre_state_authority_code)

        if auth.address == NULL_ADDRESS:
            code_to_set = b""
        else:
            if not delegated_before_tx and authority not in delegation_set_for:
                charge_state_gas(evm, StateGasCosts.AUTH_BASE)
            delegation_set_for.add(authority)
            code_to_set = EOA_DELEGATION_MARKER + auth.address

        set_code(tx_state, authority, code_to_set)
        increment_nonce(tx_state, authority)
