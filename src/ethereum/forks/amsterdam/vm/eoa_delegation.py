"""
Set EOA account code.
"""

from typing import Optional, Set, Tuple

from ethereum_rlp import rlp
from ethereum_types.numeric import U64, U256

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidSignatureError
from ethereum.state import Address

from ..fork_types import Authorization, ExecutionGas
from ..state_tracker import (
    TransactionState,
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
    GasMeter,
    StateGasCosts,
    charge_gas_from_meter,
    charge_state_gas_from_meter,
)
from . import BlockEnvironment, Evm, TransactionEnvironment

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


def resolve_delegated_code_address(
    state: TransactionState,
    gas_meter: GasMeter,
    accessed_addresses: Set[Address],
    target_address: Address,
) -> Tuple[Address, bool]:
    """
    Resolve the address of the code a call target executes.

    If `target_address` carries a delegation designation, charge the
    warm or cold access for the delegated address, warm it, and return
    it with precompiles disabled; otherwise return `target_address`
    unchanged.
    """
    code = get_code(
        state,
        get_account(state, target_address).code_hash,
        target_address,
    )
    delegated_address = get_delegated_code_address(code)
    if delegated_address is None:
        return target_address, False

    if delegated_address in accessed_addresses:
        charge_gas_from_meter(gas_meter, GasCosts.WARM_ACCESS)
    else:
        charge_gas_from_meter(gas_meter, GasCosts.COLD_ACCOUNT_ACCESS)
        accessed_addresses.add(delegated_address)

    return delegated_address, True


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
) -> Tuple[bool, Address, ExecutionGas]:
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
    delegation : `Tuple[bool, Address, ExecutionGas]`
        The delegation address and access gas cost.

    """
    tx_state = evm.tx_env.state

    code = get_code(
        tx_state,
        get_account(tx_state, address).code_hash,
        address,
    )

    if not is_valid_delegation(code):
        return False, address, GasCosts.ZERO

    delegated_address = Address(code[EOA_DELEGATION_MARKER_LENGTH:])

    if delegated_address in evm.accessed_addresses:
        delegation_gas_cost = GasCosts.WARM_ACCESS
    else:
        delegation_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS

    return True, delegated_address, delegation_gas_cost


def validate_authorization(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    accessed_authorities: Set[Address],
    auth: Authorization,
) -> Optional[Address]:
    """
    Check if the given `Authorization` is valid against the current state.

    Returns the `authority` address, or `None` if the validation was
    unsuccessful.
    """
    tx_state = tx_env.state

    if auth.chain_id not in (block_env.chain_id, U256(0)):
        return None

    if auth.nonce >= U64.MAX_VALUE:
        return None

    try:
        authority = recover_authority(auth)
    except InvalidSignatureError:
        return None

    accessed_authorities.add(authority)

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

    return authority


def set_delegation(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    gas_meter: GasMeter,
) -> Set[Address]:
    """
    Apply the EIP-7702 authorizations and charge their state-dependent
    costs at the top frame.

    Each valid authorization is charged, on top of the
    state-independent ``GasCosts.EXECUTION_PER_AUTH_BASE_COST`` already
    paid in the intrinsic cost:

    - ``StateGasCosts.NEW_ACCOUNT`` (state) when the authority's
      account leaf does not yet exist.
    - ``GasCosts.ACCOUNT_WRITE`` (execution) when applying the
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
    block_env :
        Environment for the Ethereum Virtual Machine.
    tx_env :
        Environment for the transaction.
    gas_meter :
        Gas meter of the top-level frame.

    Returns
    -------
    accessed_authorities : `Set[Address]`
        Authorities recovered from the authorizations, warmed for the
        transaction.

    """
    assert not tx_env.is_create
    tx_state = tx_env.state
    # Authorities a delegation was set for earlier in this transaction.
    accessed_authorities: Set[Address] = set()
    delegation_set_for: Set[Address] = set()
    for auth in tx_env.authorizations:
        match validate_authorization(
            block_env, tx_env, accessed_authorities, auth
        ):
            case None:
                continue
            case authority:
                pass

        if not account_exists(tx_state, authority):
            charge_state_gas_from_meter(gas_meter, StateGasCosts.NEW_ACCOUNT)

        if authority not in tx_env.accounts_with_paid_writes:
            charge_gas_from_meter(gas_meter, GasCosts.ACCOUNT_WRITE)
            tx_env.accounts_with_paid_writes.add(authority)

        pre_state_authority_account = get_pre_state_account(
            tx_state, authority
        )
        pre_state_authority_code = get_code(
            tx_state,
            pre_state_authority_account.code_hash,
            authority,
        )
        delegated_before_tx = is_valid_delegation(pre_state_authority_code)

        if auth.address == NULL_ADDRESS:
            code_to_set = b""
        else:
            if not delegated_before_tx and authority not in delegation_set_for:
                charge_state_gas_from_meter(gas_meter, StateGasCosts.AUTH_BASE)
            delegation_set_for.add(authority)
            code_to_set = EOA_DELEGATION_MARKER + auth.address

        set_code(tx_state, authority, code_to_set)
        increment_nonce(tx_state, authority)

    return accessed_authorities
