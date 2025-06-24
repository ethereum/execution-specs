"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""
from dataclasses import dataclass
from typing import Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidSignatureError, InvalidTransaction

from .exceptions import TransactionTypeError
from .fork_types import Address, Authorization, VersionedHash

TX_BASE_COST = Uint(21000)
"""
Base cost of a transaction in gas units. This is the minimum amount of gas
required to execute a transaction.
"""

FLOOR_CALLDATA_COST = Uint(10)
"""
Minimum gas cost per byte of calldata as per [EIP-7623]. Used to calculate
the minimum gas cost for transactions that include calldata.

[EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
"""

STANDARD_CALLDATA_TOKEN_COST = Uint(4)
"""
Gas cost per byte of calldata as per [EIP-7623]. Used to calculate the
gas cost for transactions that include calldata.

[EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
"""

TX_CREATE_COST = Uint(32000)
"""
Additional gas cost for creating a new contract.
"""

TX_ACCESS_LIST_ADDRESS_COST = Uint(2400)
"""
Gas cost for including an address in the access list of a transaction.
"""

TX_ACCESS_LIST_STORAGE_KEY_COST = Uint(1900)
"""
Gas cost for including a storage key in the access list of a transaction.
"""


@slotted_freezable
@dataclass
class LegacyTransaction:
    """
    Atomic operation performed on the block chain. This represents the original
    transaction format used before [EIP-1559], [EIP-2930], [EIP-4844],
    and [EIP-7702].

    [EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    [EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    gas_price: Uint
    """
    The price of gas for this transaction, in wei.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Bytes0 | Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
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


@slotted_freezable
@dataclass
class Access:
    """
    A mapping from account address to storage slots that are pre-warmed as part
    of a transaction.
    """

    account: Address
    """
    The address of the account that is accessed.
    """

    slots: Tuple[Bytes32, ...]
    """
    A tuple of storage slots that are accessed in the account.
    """


@slotted_freezable
@dataclass
class AccessListTransaction:
    """
    The transaction type added in [EIP-2930] to support access lists.

    This transaction type extends the legacy transaction with an access list
    and chain ID. The access list specifies which addresses and storage slots
    the transaction will access.

    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
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

    to: Bytes0 | Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    y_parity: U256
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


@slotted_freezable
@dataclass
class FeeMarketTransaction:
    """
    The transaction type added in [EIP-1559].

    This transaction type introduces a new fee market mechanism with two gas
    price parameters: max_priority_fee_per_gas and max_fee_per_gas.

    [EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Bytes0 | Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    y_parity: U256
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


@slotted_freezable
@dataclass
class BlobTransaction:
    """
    The transaction type added in [EIP-4844].

    This transaction type extends the fee market transaction to support
    blob-carrying transactions.

    [EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    max_fee_per_blob_gas: U256
    """
    The maximum fee per blob gas that the sender is willing to pay.
    """

    blob_versioned_hashes: Tuple[VersionedHash, ...]
    """
    A tuple of objects that represent the versioned hashes of the blobs
    included in the transaction.
    """

    y_parity: U256
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


@slotted_freezable
@dataclass
class SetCodeTransaction:
    """
    The transaction type added in [EIP-7702].

    This transaction type allows Ethereum Externally Owned Accounts (EOAs)
    to set code on their account, enabling them to act as smart contracts.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U64
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    authorizations: Tuple[Authorization, ...]
    """
    A tuple of `Authorization` objects that specify what code the signer
    desires to execute in the context of their EOA.
    """

    y_parity: U256
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


Transaction = (
    LegacyTransaction
    | AccessListTransaction
    | FeeMarketTransaction
    | BlobTransaction
    | SetCodeTransaction
)
"""
Union type representing any valid transaction type.
"""


def encode_transaction(tx: Transaction) -> LegacyTransaction | Bytes:
    """
    Encode a transaction into its RLP or typed transaction format.
    Needed because non-legacy transactions aren't RLP.

    Legacy transactions are returned as-is, while other transaction types
    are prefixed with their type identifier and RLP encoded.
    """
    if isinstance(tx, LegacyTransaction):
        return tx
    elif isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(tx)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(tx)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(tx)
    elif isinstance(tx, SetCodeTransaction):
        return b"\x04" + rlp.encode(tx)
    else:
        raise Exception(f"Unable to encode transaction of type {type(tx)}")


def decode_transaction(tx: LegacyTransaction | Bytes) -> Transaction:
    """
    Decode a transaction from its RLP or typed transaction format.
    Needed because non-legacy transactions aren't RLP.

    Legacy transactions are returned as-is, while other transaction types
    are decoded based on their type identifier prefix.
    """
    if isinstance(tx, Bytes):
        if tx[0] == 1:
            return rlp.decode_to(AccessListTransaction, tx[1:])
        elif tx[0] == 2:
            return rlp.decode_to(FeeMarketTransaction, tx[1:])
        elif tx[0] == 3:
            return rlp.decode_to(BlobTransaction, tx[1:])
        elif tx[0] == 4:
            return rlp.decode_to(SetCodeTransaction, tx[1:])
        else:
            raise TransactionTypeError(tx[0])
    else:
        return tx


def validate_transaction(tx: Transaction) -> Tuple[Uint, Uint]:
    """
    Verifies a transaction.

    The gas in a transaction gets used to pay for the intrinsic cost of
    operations, therefore if there is insufficient gas then it would not
    be possible to execute a transaction and it will be declared invalid.

    Additionally, the nonce of a transaction must not equal or exceed the
    limit defined in [EIP-2681].
    In practice, defining the limit as ``2**64-1`` has no impact because
    sending ``2**64-1`` transactions is improbable. It's not strictly
    impossible though, ``2**64-1`` transactions is the entire capacity of the
    Ethereum blockchain at 2022 gas limits for a little over 22 years.

    Also, the code size of a contract creation transaction must be within
    limits of the protocol.

    This function takes a transaction as a parameter and returns the intrinsic
    gas cost and the minimum calldata gas cost for the transaction after
    validation. It throws an `InvalidTransaction` exception
    if the transaction is invalid.

    [EIP-2681]: https://eips.ethereum.org/EIPS/eip-2681
    [EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
    """
    from .vm.interpreter import MAX_CODE_SIZE

    intrinsic_gas, calldata_floor_gas_cost = calculate_intrinsic_cost(tx)
    if max(intrinsic_gas, calldata_floor_gas_cost) > tx.gas:
        raise InvalidTransaction("Insufficient gas")
    if U256(tx.nonce) >= U256(U64.MAX_VALUE):
        raise InvalidTransaction("Nonce too high")
    if tx.to == Bytes0(b"") and len(tx.data) > 2 * MAX_CODE_SIZE:
        raise InvalidTransaction("Code size too large")

    return intrinsic_gas, calldata_floor_gas_cost


def calculate_intrinsic_cost(tx: Transaction) -> Tuple[Uint, Uint]:
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
    1. Base cost (`TX_BASE_COST`)
    2. Cost for data (zero and non-zero bytes)
    3. Cost for contract creation (if applicable)
    4. Cost for access list entries (if applicable)
    5. Cost for authorizations (if applicable)


    This function takes a transaction as a parameter and returns the intrinsic
    gas cost of the transaction and the minimum gas cost used by the
    transaction based on the calldata size.
    """
    from .vm.eoa_delegation import PER_EMPTY_ACCOUNT_COST
    from .vm.gas import init_code_cost

    zero_bytes = 0
    for byte in tx.data:
        if byte == 0:
            zero_bytes += 1

    tokens_in_calldata = Uint(zero_bytes + (len(tx.data) - zero_bytes) * 4)
    # EIP-7623 floor price (note: no EVM costs)
    calldata_floor_gas_cost = (
        tokens_in_calldata * FLOOR_CALLDATA_COST + TX_BASE_COST
    )

    data_cost = tokens_in_calldata * STANDARD_CALLDATA_TOKEN_COST

    if tx.to == Bytes0(b""):
        create_cost = TX_CREATE_COST + init_code_cost(ulen(tx.data))
    else:
        create_cost = Uint(0)

    access_list_cost = Uint(0)
    if isinstance(
        tx,
        (
            AccessListTransaction,
            FeeMarketTransaction,
            BlobTransaction,
            SetCodeTransaction,
        ),
    ):
        for access in tx.access_list:
            access_list_cost += TX_ACCESS_LIST_ADDRESS_COST
            access_list_cost += (
                ulen(access.slots) * TX_ACCESS_LIST_STORAGE_KEY_COST
            )

    auth_cost = Uint(0)
    if isinstance(tx, SetCodeTransaction):
        auth_cost += Uint(PER_EMPTY_ACCOUNT_COST * len(tx.authorizations))

    return (
        Uint(
            TX_BASE_COST
            + data_cost
            + create_cost
            + access_list_cost
            + auth_cost
        ),
        calldata_floor_gas_cost,
    )


def recover_sender(chain_id: U64, tx: Transaction) -> Address:
    """
    Extracts the sender address from a transaction.

    The v, r, and s values are the three parts that make up the signature
    of a transaction. In order to recover the sender of a transaction the two
    components needed are the signature (``v``, ``r``, and ``s``) and the
    signing hash of the transaction. The sender's public key can be obtained
    with these two values and therefore the sender address can be retrieved.

    This function takes chain_id and a transaction as parameters and returns
    the address of the sender of the transaction. It raises an
    `InvalidSignatureError` if the signature values (r, s, v) are invalid.
    """
    r, s = tx.r, tx.s
    if U256(0) >= r or r >= SECP256K1N:
        raise InvalidSignatureError("bad r")
    if U256(0) >= s or s > SECP256K1N // U256(2):
        raise InvalidSignatureError("bad s")

    if isinstance(tx, LegacyTransaction):
        v = tx.v
        if v == 27 or v == 28:
            public_key = secp256k1_recover(
                r, s, v - U256(27), signing_hash_pre155(tx)
            )
        else:
            chain_id_x2 = U256(chain_id) * U256(2)
            if v != U256(35) + chain_id_x2 and v != U256(36) + chain_id_x2:
                raise InvalidSignatureError("bad v")
            public_key = secp256k1_recover(
                r,
                s,
                v - U256(35) - chain_id_x2,
                signing_hash_155(tx, chain_id),
            )
    elif isinstance(tx, AccessListTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_2930(tx)
        )
    elif isinstance(tx, FeeMarketTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_1559(tx)
        )
    elif isinstance(tx, BlobTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_4844(tx)
        )
    elif isinstance(tx, SetCodeTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_7702(tx)
        )

    return Address(keccak256(public_key)[12:32])


def signing_hash_pre155(tx: LegacyTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a legacy (pre [EIP-155])
    signature.

    This function takes a legacy transaction as a parameter and returns the
    signing hash of the transaction.

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
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


def signing_hash_155(tx: LegacyTransaction, chain_id: U64) -> Hash32:
    """
    Compute the hash of a transaction used in a [EIP-155] signature.

    This function takes a legacy transaction and a chain ID as parameters
    and returns the hash of the transaction used in an [EIP-155] signature.

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
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
                chain_id,
                Uint(0),
                Uint(0),
            )
        )
    )


def signing_hash_2930(tx: AccessListTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a [EIP-2930] signature.

    This function takes an access list transaction as a parameter
    and returns the hash of the transaction used in an [EIP-2930] signature.

    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    """
    return keccak256(
        b"\x01"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_1559(tx: FeeMarketTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in an [EIP-1559] signature.

    This function takes a fee market transaction as a parameter
    and returns the hash of the transaction used in an [EIP-1559] signature.

    [EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
    """
    return keccak256(
        b"\x02"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_4844(tx: BlobTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in an [EIP-4844] signature.

    This function takes a transaction as a parameter and returns the
    signing hash of the transaction used in an [EIP-4844] signature.

    [EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
    """
    return keccak256(
        b"\x03"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
                tx.max_fee_per_blob_gas,
                tx.blob_versioned_hashes,
            )
        )
    )


def signing_hash_7702(tx: SetCodeTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a [EIP-7702] signature.

    This function takes a transaction as a parameter and returns the
    signing hash of the transaction used in a [EIP-7702] signature.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """
    return keccak256(
        b"\x04"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
                tx.authorizations,
            )
        )
    )


def get_transaction_hash(tx: Bytes | LegacyTransaction) -> Hash32:
    """
    Compute the hash of a transaction.

    This function takes a transaction as a parameter and returns the
    keccak256 hash of the transaction. It can handle both legacy transactions
    and typed transactions (`AccessListTransaction`, `FeeMarketTransaction`,
    etc.).
    """
    assert isinstance(tx, (LegacyTransaction, Bytes))
    if isinstance(tx, LegacyTransaction):
        return keccak256(rlp.encode(tx))
    else:
        return keccak256(tx)
