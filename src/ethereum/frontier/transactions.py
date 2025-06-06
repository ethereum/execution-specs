"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""
from dataclasses import dataclass
from typing import Union

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidSignatureError, InvalidTransaction

from .fork_types import Address

TX_BASE_COST = Uint(21000)
"""
Base cost of a transaction in gas units. This is the minimum amount of gas
required to execute a transaction.
"""

TX_DATA_COST_PER_NON_ZERO = Uint(68)
"""
Gas cost per non-zero byte in the transaction data.
"""

TX_DATA_COST_PER_ZERO = Uint(4)
"""
Gas cost per zero byte in the transaction data.
"""


@slotted_freezable
@dataclass
class Transaction:
    """
    Atomic operation performed on the block chain.
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    gas_price: Uint
    """
    The price of gas for this transaction.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Union[Bytes0, Address]
    """
    The address of the recipient. If empty, the transaction is a contract creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions on contracts or to create new contracts.
    """

    v: U256
    """
    The recovery id of the signature.
    """

    r: U256
    """
    The first part of the signature.
    """

    s: U256
    """
    The second part of the signature.
    """


def validate_transaction(tx: Transaction) -> Uint:
    """
    Verifies a transaction.

    The gas in a transaction gets used to pay for the intrinsic cost of
    operations, therefore if there is insufficient gas then it would not
    be possible to execute a transaction and it will be declared invalid.

    Additionally, the nonce of a transaction must not equal or exceed the
    limit defined in [EIP-2681], applied retroactively.
    In practice, defining the limit as ``2**64-1`` has no impact because
    sending ``2**64-1`` transactions is improbable. It's not strictly
    impossible though, ``2**64-1`` transactions is the entire capacity of the
    Ethereum blockchain at 2022 gas limits for a little over 22 years.

    #### Parameters
    - tx: Transaction to validate.

    #### Returns
    - intrinsic_gas: `ethereum.base_types.Uint`
    The intrinsic cost of the transaction.

    #### Raises
    - InvalidTransaction: If the transaction is not valid.

    [EIP-2681]: https://eips.ethereum.org/EIPS/eip-2681
    """
    intrinsic_gas = calculate_intrinsic_cost(tx)
    if intrinsic_gas > tx.gas:
        raise InvalidTransaction("insufficient gas")
    if U256(tx.nonce) >= U256(U64.MAX_VALUE):
        raise InvalidTransaction("nonce too high")
    return intrinsic_gas


def calculate_intrinsic_cost(tx: Transaction) -> Uint:
    """
    Calculates the gas that is charged before execution is started.

    The intrinsic cost of the transaction is charged before execution has
    begun. Functions/operations in the EVM cost money to execute so this
    intrinsic cost is for the operations that need to be paid for as part of
    the transaction. Data transfer, for example, is part of this intrinsic
    cost. It costs ether to send data over the wire and that ether is
    accounted for in the intrinsic cost calculated in this function. This
    intrinsic cost must be calculated and paid for before execution in order
    for all operations to be implemented.

    The intrinsic cost includes:
    1. Base cost (TX_BASE_COST)
    2. Cost for data (zero and non-zero bytes)

    #### Parameters
    - tx : Transaction to compute the intrinsic cost of.

    #### Returns
    - intrinsic_gas : `ethereum.base_types.Uint`
    The intrinsic cost of the transaction.
    """
    data_cost = Uint(0)

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    return TX_BASE_COST + data_cost


def recover_sender(tx: Transaction) -> Address:
    """
    Extracts the sender address from a transaction.

    The v, r, and s values are the three parts that make up the signature
    of a transaction. In order to recover the sender of a transaction the two
    components needed are the signature (``v``, ``r``, and ``s``) and the
    signing hash of the transaction. The sender's public key can be obtained
    with these two values and therefore the sender address can be retrieved.

    #### Parameters
    - tx: Transaction of interest.

    #### Returns
    - sender: `ethereum.fork_types.Address`
    The address of the account that signed the transaction.

    #### Raises
    - InvalidSignatureError: If the signature values (r, s, v) are invalid.
    """
    v, r, s = tx.v, tx.r, tx.s
    if v != 27 and v != 28:
        raise InvalidSignatureError("bad v")
    if U256(0) >= r or r >= SECP256K1N:
        raise InvalidSignatureError("bad r")
    if U256(0) >= s or s >= SECP256K1N:
        raise InvalidSignatureError("bad s")

    public_key = secp256k1_recover(r, s, v - U256(27), signing_hash(tx))
    return Address(keccak256(public_key)[12:32])


def signing_hash(tx: Transaction) -> Hash32:
    """
    Compute the hash of a transaction used in the signature.

    #### Parameters
    - tx: Transaction of interest.

    #### Returns
    - hash: `ethereum.crypto.hash.Hash32`
    Hash of the transaction.
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
            )
        )
    )


def get_transaction_hash(tx: Transaction) -> Hash32:
    """
    Compute the hash of a transaction.

    #### Parameters
    - tx: Transaction of interest.

    #### Returns
    - hash: `ethereum.crypto.hash.Hash32`
    Hash of the transaction.
    """
    return keccak256(rlp.encode(tx))
