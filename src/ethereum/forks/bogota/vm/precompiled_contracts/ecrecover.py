"""
Ethereum Virtual Machine (EVM) ECRECOVER PRECOMPILED CONTRACT.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `ECRECOVER` precompiled contract.
"""

from ethereum_types.numeric import U256

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidSignatureError
from ethereum.state import Address
from ethereum.utils.byte import left_pad_zero_bytes

from ...state_tracker import get_account, get_code
from ...vm import Evm
from ...vm.eoa_delegation import is_valid_delegation
from ...vm.gas import GasCosts, charge_gas
from ...vm.memory import buffer_read


def ecrecover(evm: Evm) -> None:
    """
    Recover the address that signed a message hash and write it, left-padded
    to a word, to the output.

    A successful recovery pays for accessing the recovered account and for
    reading its code, and warms the account. Leave the output empty if
    recovery fails or if the account holds code other than a delegation
    designation; protocol rules already bar such an account from sending
    transactions with its original key.
    """
    data = evm.call_data

    # GAS
    charge_gas(evm, GasCosts.PRECOMPILE_ECRECOVER)

    # OPERATION
    message_hash_bytes = buffer_read(data, U256(0), U256(32))
    message_hash = Hash32(message_hash_bytes)
    v = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    r = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))
    s = U256.from_be_bytes(buffer_read(data, U256(96), U256(32)))

    if v != U256(27) and v != U256(28):
        return
    if U256(0) >= r or r >= SECP256K1N:
        return
    if U256(0) >= s or s >= SECP256K1N:
        return

    try:
        public_key = secp256k1_recover(r, s, v - U256(27), message_hash)
    except InvalidSignatureError:
        # unable to extract public key
        return

    address = Address(keccak256(public_key)[12:32])

    # GAS (STATE-INDEPENDENT)
    is_cold_access = address not in evm.accessed_addresses
    if is_cold_access:
        access_gas_cost = GasCosts.COLD_ACCOUNT_ACCESS
    else:
        access_gas_cost = GasCosts.WARM_ACCESS
    access_gas_cost += GasCosts.WARM_ACCESS  # Code reading cost
    charge_gas(evm, access_gas_cost)

    # STATE ACCESS (STATE-DEPENDENT GAS)
    if is_cold_access:
        evm.accessed_addresses.add(address)
    tx_state = evm.tx_env.state
    code = get_code(tx_state, get_account(tx_state, address).code_hash)

    # OPERATION
    if code and not is_valid_delegation(code):
        return

    evm.output = left_pad_zero_bytes(address, 32)
