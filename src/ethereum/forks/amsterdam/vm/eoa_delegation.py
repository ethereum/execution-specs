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
    get_pre_state_account,
    increment_nonce,
    set_code,
)
from ..utils.hexadecimal import hex_to_address
from ..vm.gas import (
    GasCosts,
    StateGasCosts,
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

    code = get_code(
        tx_state,
        get_account(tx_state, address).code_hash,
        address,
    )

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
) -> None | Tuple[Address, Bytes]:
    """
    Check if the given `Authorization` is valid against the current state.

    Returns the `authority` address and its code, or `None` if the
    validation was unsuccessful.
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
    authority_code = get_code(
        tx_state,
        authority_account.code_hash,
        authority,
    )

    if authority_code and not is_valid_delegation(authority_code):
        return None

    authority_nonce = authority_account.nonce
    if authority_nonce != auth.nonce:
        return None

    return (authority, authority_code)


def set_delegation(message: Message) -> Tuple[Uint, Uint]:
    """
    Set the delegation code for the authorities in the message.

    Refills `StateGasCosts.NEW_ACCOUNT` when the authority's account
    leaf already exists, and `StateGasCosts.AUTH_BASE` when its code
    slot already holds a delegation indicator. When the authority leaf
    already exists, the worst-case `GasCosts.ACCOUNT_WRITE` charged in
    the intrinsic cost is also refunded to the regular-gas refund
    counter. The totals are returned so block accounting can subtract
    the state refill from `tx_state_gas` and apply the regular refund.

    Parameters
    ----------
    message :
        Transaction specific items.

    Returns
    -------
    state_refund : `Uint`
        Total state gas refunded across all processed authorizations.
    regular_refund : `Uint`
        Total regular gas (`ACCOUNT_WRITE`) refunded for authorities
        whose account leaf already existed.

    """
    tx_state = message.tx_env.state
    state_refund = Uint(0)
    regular_refund = Uint(0)
    for auth in message.tx_env.authorizations:
        match validate_authorization(message, auth):
            case None:
                refund = StateGasCosts.AUTH_BASE + StateGasCosts.NEW_ACCOUNT
                message.state_gas_reservoir += refund
                state_refund += refund
                regular_refund += GasCosts.ACCOUNT_WRITE
                continue
            case (authority, authority_code):
                pass

        refund = Uint(0)

        if account_exists(tx_state, authority):
            refund += StateGasCosts.NEW_ACCOUNT
            # The new-account ACCOUNT_WRITE charged at intrinsic time is
            # not needed: refund it to the regular refund counter.
            regular_refund += GasCosts.ACCOUNT_WRITE

        pre_state_authority_account = get_pre_state_account(
            tx_state, authority
        )
        pre_state_authority_code = get_code(
            tx_state,
            pre_state_authority_account.code_hash,
            authority,
        )

        delegated_before_tx = is_valid_delegation(pre_state_authority_code)
        delegated_now = is_valid_delegation(authority_code)

        if auth.address == NULL_ADDRESS:
            refund += StateGasCosts.AUTH_BASE

            if delegated_now and not delegated_before_tx:
                refund += StateGasCosts.AUTH_BASE

            code_to_set = b""
        else:
            code_to_set = EOA_DELEGATION_MARKER + auth.address

            if delegated_now or delegated_before_tx:
                refund += StateGasCosts.AUTH_BASE

        set_code(tx_state, authority, code_to_set)
        increment_nonce(tx_state, authority)

        message.state_gas_reservoir += refund
        state_refund += refund

    if message.code_address is None:
        raise InvalidBlock("Invalid type 4 transaction: no target")

    message.code = get_code(
        tx_state,
        get_account(tx_state, message.code_address).code_hash,
        message.code_address,
    )

    return state_refund, regular_refund
