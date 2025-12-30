"""
Set EOA account code.
"""

from typing import Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock, InvalidSignatureError

from ..fork_types import Address, Authorization
from ..state import (
    account_exists,
    get_account,
    increment_nonce,
    set_authority_code,
)
from ..state_tracker import (
    capture_pre_code,
    track_address,
    track_code_change,
    track_nonce_change,
)
from ..utils.hexadecimal import hex_to_address
from ..vm.gas import GAS_COLD_ACCOUNT_ACCESS, GAS_WARM_ACCESS
from . import Evm, Message

SET_CODE_TX_MAGIC = b"\x05"
EOA_DELEGATION_MARKER = b"\xef\x01\x00"
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
    state = evm.message.block_env.state

    code = get_account(state, address).code
    track_address(evm.state_changes, address)

    if not is_valid_delegation(code):
        return False, address, Uint(0)

    delegated_address = Address(code[EOA_DELEGATION_MARKER_LENGTH:])

    if delegated_address in evm.accessed_addresses:
        delegation_gas_cost = GAS_WARM_ACCESS
    else:
        delegation_gas_cost = GAS_COLD_ACCOUNT_ACCESS

    return True, delegated_address, delegation_gas_cost


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
    state = message.block_env.state
    refund_counter = U256(0)
    for auth in message.tx_env.authorizations:
        if auth.chain_id not in (message.block_env.chain_id, U256(0)):
            continue

        if auth.nonce >= U64.MAX_VALUE:
            continue

        try:
            authority = recover_authority(auth)
        except InvalidSignatureError:
            continue

        message.accessed_addresses.add(authority)

        authority_account = get_account(state, authority)
        authority_code = authority_account.code

        track_address(message.tx_env.state_changes, authority)

        if authority_code and not is_valid_delegation(authority_code):
            continue

        authority_nonce = authority_account.nonce
        if authority_nonce != auth.nonce:
            continue

        if account_exists(state, authority):
            refund_counter += U256(PER_EMPTY_ACCOUNT_COST - PER_AUTH_BASE_COST)

        if auth.address == NULL_ADDRESS:
            code_to_set = b""
        else:
            code_to_set = EOA_DELEGATION_MARKER + auth.address

        tx_frame = message.tx_env.state_changes
        # EIP-7928: Capture pre-code before any changes
        capture_pre_code(tx_frame, authority, authority_code)

        set_authority_code(state, authority, code_to_set)

        if authority_code != code_to_set:
            # Track code change if different from current
            track_code_change(tx_frame, authority, code_to_set)

        increment_nonce(state, authority)
        nonce_after = get_account(state, authority).nonce
        track_nonce_change(tx_frame, authority, U64(nonce_after))

    if message.code_address is None:
        raise InvalidBlock("Invalid type 4 transaction: no target")

    message.code = get_account(state, message.code_address).code

    return refund_counter
