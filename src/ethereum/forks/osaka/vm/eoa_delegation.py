"""
Set EOA account code.
"""

from typing import Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock, InvalidSignatureError
from ethereum.state import Address

from ..fork_types import Authorization
from ..state_tracker import (
    account_exists,
    get_account,
    get_code,
    increment_nonce,
    set_code,
)
from ..utils.hexadecimal import hex_to_address
from ..vm.gas import GasCosts
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


def access_delegation(
    evm: Evm, address: Address
) -> Tuple[bool, Address, Bytes, Uint]:
    """
    Get the delegation address, code, and the cost of access from the address.

    Parameters
    ----------
    evm : `Evm`
        The execution frame.
    address : `Address`
        The address to get the delegation from.

    Returns
    -------
    delegation : `Tuple[bool, Address, Bytes, Uint]`
        The delegation address, code, and access gas cost.

    """
    tx_state = evm.message.tx_env.state

    code = get_code(tx_state, get_account(tx_state, address).code_hash)
    if not is_valid_delegation(code):
        return False, address, code, Uint(0)

    address = Address(code[EOA_DELEGATION_MARKER_LENGTH:])
    if address in evm.accessed_addresses:
        access_gas_cost = GasCosts.WARM_ACCESS
    else:
        evm.accessed_addresses.add(address)
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    code = get_code(tx_state, get_account(tx_state, address).code_hash)

    return True, address, code, access_gas_cost


def validate_authorization(
    message: Message, auth: Authorization
) -> None | Address:
    """
    Check if the given `Authorization` is valid against the current state.

    Returns the `authority` address or `None` if the validation was
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


def set_delegation(message: Message) -> U256:
    """
    Set the delegation code for the authorities in the message.

    Parameters
    ----------
    message :
        Transaction specific items.

    Returns
    -------
    refund_counter: `U256`
        Refund from authority which already exists in state.

    """
    tx_state = message.tx_env.state
    refund_counter = U256(0)
    for auth in message.tx_env.authorizations:
        match validate_authorization(message, auth):
            case None:
                continue
            case authority:
                pass

        if account_exists(tx_state, authority):
            refund_counter += U256(
                GasCosts.AUTH_PER_EMPTY_ACCOUNT
                - GasCosts.REFUND_AUTH_PER_EXISTING_ACCOUNT
            )

        if auth.address == NULL_ADDRESS:
            code_to_set = b""
        else:
            code_to_set = EOA_DELEGATION_MARKER + auth.address
        set_code(tx_state, authority, code_to_set)

        increment_nonce(tx_state, authority)

    if message.code_address is None:
        raise InvalidBlock("Invalid type 4 transaction: no target")

    message.code = get_code(
        tx_state, get_account(tx_state, message.code_address).code_hash
    )

    return refund_counter
