"""
Set EOA account code.
"""


from typing import Optional, Tuple

from ethereum import rlp
from ethereum.base_types import U64, U256, Bytes, Uint
from ethereum.crypto import InvalidSignature
from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock

from ..fork_types import Address, Authorization
from ..state import account_exists, get_account, increment_nonce, set_code
from ..utils.hexadecimal import hex_to_address
from ..vm.gas import GAS_COLD_ACCOUNT_ACCESS, GAS_WARM_ACCESS
from . import Evm, Message

SET_CODE_TX_MAGIC = b"\x05"
EOA_DELEGATION_MARKER = b"\xEF\x01\x00"
EOA_DELEGATION_MARKER_LENGTH = len(EOA_DELEGATION_MARKER)
EOA_DELEGATED_CODE_LENGTH = 23
PER_EMPTY_ACCOUNT_COST = 25000
PER_AUTH_BASE_COST = 12500
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
    if (
        len(code) == EOA_DELEGATED_CODE_LENGTH
        and code[:EOA_DELEGATION_MARKER_LENGTH] == EOA_DELEGATION_MARKER
    ):
        return True
    return False


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
    InvalidSignature
        If the signature is invalid.

    Returns
    -------
    authority : `Address`
        The recovered authority address.
    """
    y_parity, r, s = authorization.y_parity, authorization.r, authorization.s
    if y_parity not in (0, 1):
        raise InvalidSignature("Invalid y_parity in authorization")
    if 0 >= r or r >= SECP256K1N:
        raise InvalidSignature("Invalid r value in authorization")
    if 0 >= s or s > SECP256K1N // 2:
        raise InvalidSignature("Invalid s value in authorization")

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
    code = get_account(evm.block_env.state, address).code
    if not is_valid_delegation(code):
        return False, address, code, Uint(0)

    address = Address(code[EOA_DELEGATION_MARKER_LENGTH:])
    if address in evm.accessed_addresses:
        access_gas_cost = GAS_WARM_ACCESS
    else:
        evm.accessed_addresses.add(address)
        access_gas_cost = GAS_COLD_ACCOUNT_ACCESS
    code = get_account(evm.block_env.state, address).code

    return True, address, code, access_gas_cost


def set_delegation(message: Message) -> U256:
    """
    Set the delegation code for the authorities in the message.

    Parameters
    ----------
    message :
        Transaction specific items.
    env :
        External items required for EVM execution.

    Returns
    -------
    refund_counter: `U256`
        Refund from authority which already exists in state.
    """
    block_env = message.block_env
    tx_env = message.tx_env
    refund_counter = U256(0)
    for auth in tx_env.authorizations:
        if auth.chain_id not in (block_env.chain_id, U64(0)):
            continue

        if auth.nonce >= U64.MAX_VALUE:
            continue

        try:
            authority = recover_authority(auth)
        except InvalidSignature:
            continue

        message.accessed_addresses.add(authority)

        authority_account = get_account(block_env.state, authority)
        authority_code = authority_account.code

        if authority_code != bytearray() and not is_valid_delegation(
            authority_code
        ):
            continue

        authority_nonce = authority_account.nonce
        if authority_nonce != auth.nonce:
            continue

        if account_exists(block_env.state, authority):
            refund_counter += PER_EMPTY_ACCOUNT_COST - PER_AUTH_BASE_COST

        if auth.address == NULL_ADDRESS:
            code_to_set = b""
        else:
            code_to_set = EOA_DELEGATION_MARKER + auth.address
        set_code(block_env.state, authority, code_to_set)

        increment_nonce(block_env.state, authority)

    if message.code_address is None:
        raise InvalidBlock("Invalid type 4 transaction: no target")
    message.code = get_account(block_env.state, message.code_address).code

    if is_valid_delegation(message.code):
        message.code_address = Address(
            message.code[EOA_DELEGATION_MARKER_LENGTH:]
        )
        message.accessed_addresses.add(message.code_address)

        message.code = get_account(block_env.state, message.code_address).code

    return refund_counter
