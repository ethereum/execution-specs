"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""

from dataclasses import dataclass
from typing import Tuple, TypeGuard, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import (
    InsufficientTransactionGasError,
    InvalidBlock,
    InvalidSignatureError,
    NonceMismatchError,
    NonceOverflowError,
)
from ethereum.state import Address

from .exceptions import (
    BlobCountExceededError,
    EmptyAuthorizationListError,
    InitCodeTooLargeError,
    InsufficientMaxFeePerGasError,
    InvalidBlobVersionedHashError,
    NoBlobDataError,
    PriorityFeeGreaterThanMaxFeeError,
    TransactionTypeContractCreationError,
    TransactionTypeError,
)
from .fork_types import Authorization, ExecutionGas, VersionedHash


@final
@dataclass
class IntrinsicGasCost:
    """Intrinsic gas costs for a transaction, split by gas type."""

    execution: ExecutionGas
    """Execution gas (calldata, base cost, access list, etc.)."""

    content_floor: ExecutionGas
    """
    Minimum gas cost based on the transaction's content bytes per
    [EIP-8131].

    [EIP-8131]: https://eips.ethereum.org/EIPS/eip-8131
    """


TX_MAX_GAS_LIMIT = Uint(16_777_216)

BLOB_COUNT_LIMIT = 6
"""
Maximum number of blobs a single transaction may carry.
"""

VERSIONED_HASH_VERSION_KZG = b"\x01"
"""
Version byte that every blob versioned hash must start with.
"""

ACCESS_LIST_ADDRESS_BYTES = Uint(20)
"""
Content bytes contributed by a single access list address.
"""

ACCESS_LIST_STORAGE_KEY_BYTES = Uint(32)
"""
Content bytes contributed by a single access list storage key.
"""

AUTHORIZATION_BYTES = Uint(108)
"""
Content bytes contributed by a single [EIP-7702] authorization, taken
as the largest it can encode to.

[EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
"""

BLOB_VERSIONED_HASH_BYTES = Uint(32)
"""
Content bytes contributed by a single blob versioned hash.
"""


@final
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


@final
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


@final
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


@final
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


@final
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


@final
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


AccessListCapableTransaction = (
    AccessListTransaction
    | FeeMarketTransaction
    | BlobTransaction
    | SetCodeTransaction
)
"""
Transaction types that include an [EIP-2930]-style access list.

See [`has_access_list`][hal] and [`Access`][a] for more details.

[EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
[hal]: ref:ethereum.forks.amsterdam.transactions.has_access_list
[a]: ref:ethereum.forks.amsterdam.transactions.Access
"""


FeeMarketCapableTransaction = (
    FeeMarketTransaction | BlobTransaction | SetCodeTransaction
)
"""
Transaction types that include the [EIP-1559]-style fee structure.

See [`FeeMarketTransaction`][fmt] for more details.

[EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
[fmt]: ref:ethereum.forks.amsterdam.transactions.FeeMarketTransaction
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

    Accept a ``LegacyTransaction`` object (returned as-is) or raw
    bytes.

    EIP-2718 states that the first byte distinguishes the format:
    [0x00, 0x7f] is a typed transaction, [0xc0, 0xfe] is a legacy
    transaction (RLP list prefix).
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
        elif tx[0] >= 0xC0:
            assert tx[0] <= 0xFE
            return rlp.decode_to(LegacyTransaction, tx)
        else:
            raise TransactionTypeError(tx[0])
    else:
        return tx


def validate_transaction(tx: Transaction, sender: Address) -> IntrinsicGasCost:
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

    This function takes a transaction and gas_limit as parameters and
    returns the intrinsic gas costs for the transaction after validation.
    It throws an `InsufficientTransactionGasError` exception if the
    transaction does not provide enough gas to cover the intrinsic cost
    or the content floor ([EIP-8131]), and a `NonceOverflowError`
    exception if the nonce overflows.
    It also raises an `InitCodeTooLargeError` if the code
    size of a contract creation transaction exceeds the maximum allowed
    size, and a `PriorityFeeGreaterThanMaxFeeError` if the maximum
    priority fee per gas of a fee market transaction exceeds its maximum
    fee per gas.

    [EIP-2681]: https://eips.ethereum.org/EIPS/eip-2681
    [EIP-8131]: https://eips.ethereum.org/EIPS/eip-8131
    """
    from .vm.interpreter import MAX_INIT_CODE_SIZE

    if U256(tx.nonce) >= U256(U64.MAX_VALUE):
        raise NonceOverflowError("Nonce too high")

    if tx.to == Bytes0(b"") and len(tx.data) > MAX_INIT_CODE_SIZE:
        raise InitCodeTooLargeError("Code size too large")

    if isinstance(tx, FeeMarketCapableTransaction):
        if tx.max_fee_per_gas < tx.max_priority_fee_per_gas:
            raise PriorityFeeGreaterThanMaxFeeError(
                "priority fee greater than max fee"
            )

    if isinstance(tx, BlobTransaction):
        blob_count = len(tx.blob_versioned_hashes)
        if blob_count == 0:
            raise NoBlobDataError("no blob data in transaction")
        if blob_count > BLOB_COUNT_LIMIT:
            raise BlobCountExceededError(
                f"Tx has {blob_count} blobs. Max allowed: {BLOB_COUNT_LIMIT}"
            )
        for blob_versioned_hash in tx.blob_versioned_hashes:
            if blob_versioned_hash[0:1] != VERSIONED_HASH_VERSION_KZG:
                raise InvalidBlobVersionedHashError(
                    "invalid blob versioned hash"
                )

    if isinstance(tx, (BlobTransaction, SetCodeTransaction)):
        if not isinstance(tx.to, Address):
            raise TransactionTypeContractCreationError(tx)

    if isinstance(tx, SetCodeTransaction):
        if not any(tx.authorizations):
            raise EmptyAuthorizationListError("empty authorization list")

    intrinsic = calculate_intrinsic_cost(tx, sender)
    intrinsic_gas = Uint(intrinsic.execution)
    if intrinsic_gas > tx.gas:
        raise InsufficientTransactionGasError("Insufficient intrinsic gas")
    if intrinsic.content_floor > tx.gas:
        raise InsufficientTransactionGasError("Insufficient content floor")
    if intrinsic.execution > TX_MAX_GAS_LIMIT:
        raise InsufficientTransactionGasError(
            "Intrinsic execution gas exceeds TX_MAX_GAS_LIMIT"
        )
    if intrinsic.content_floor > TX_MAX_GAS_LIMIT:
        raise InsufficientTransactionGasError(
            "Intrinsic content floor exceeds TX_MAX_GAS_LIMIT"
        )

    return intrinsic


def calculate_intrinsic_cost(
    tx: Transaction, sender: Address
) -> IntrinsicGasCost:
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
    1. Sender cost (`TX_BASE`).
    2. Recipient cost (`COLD_ACCOUNT_ACCESS` for a non-self-transfer
       call, or `CREATE_ACCESS` for a contract creation). The created
       account's `NEW_ACCOUNT` state gas is state-dependent and is
       charged at the top frame, not here.
    3. Value cost (`TX_VALUE_COST` for a non-self-transfer call) when
       ``tx.value > 0``.
    4. Calldata cost (zero and non-zero bytes).
    5. Access list entries (if applicable).
    6. Authorizations (if applicable): only the state-independent base
       cost (`EXECUTION_PER_AUTH_BASE_COST`) per tuple. The
       state-dependent account-creation and delegation-write costs are
       charged at the top frame by `set_delegation`.

    Self-transfers (``sender == tx.to``) skip the recipient and value
    charges.

    This function takes a transaction and its sender as parameters and
    returns the intrinsic execution gas cost and the minimum (floor)
    gas cost, which charges every [content byte][cb] at
    `FLOOR_PER_BYTE`. The floor is anchored on the execution-gas
    portion of items 1 to 3 above rather than `TX_BASE` alone, so it
    never undercuts the transaction's own intrinsic base.

    [cb]: ref:ethereum.forks.amsterdam.transactions.count_content_bytes
    """
    from .vm.gas import GasCosts, init_code_cost

    tokens_in_calldata = count_tokens_in_data(tx.data)

    data_cost = tokens_in_calldata * GasCosts.TX_DATA_TOKEN_STANDARD

    is_create = tx.to == Bytes0(b"")
    is_self_transfer = tx.to == sender

    recipient_execution_gas = Uint(0)
    init_code_gas = Uint(0)
    if is_create:
        recipient_execution_gas = GasCosts.CREATE_ACCESS
        init_code_gas = init_code_cost(ulen(tx.data))
    elif not is_self_transfer:
        recipient_execution_gas = GasCosts.COLD_ACCOUNT_ACCESS
        if tx.value > U256(0):
            recipient_execution_gas += GasCosts.TX_VALUE_COST

    access_list_cost = Uint(0)
    if has_access_list(tx):
        for access in tx.access_list:
            access_list_cost += GasCosts.TX_ACCESS_LIST_ADDRESS
            access_list_cost += (
                ulen(access.slots) * GasCosts.TX_ACCESS_LIST_STORAGE_KEY
            )

    auth_cost = Uint(0)
    if isinstance(tx, SetCodeTransaction):
        auth_cost = GasCosts.EXECUTION_PER_AUTH_BASE_COST * ulen(
            tx.authorizations
        )

    # Decomposed execution-gas intrinsic base (EIP-2780), which also
    # anchors the content floor.
    base_execution_gas = GasCosts.TX_BASE + recipient_execution_gas

    # Floor gas cost (EIP-8131: every content byte at `FLOOR_PER_BYTE`).
    content_floor_gas_cost = (
        count_content_bytes(tx) * GasCosts.FLOOR_PER_BYTE + base_execution_gas
    )

    return IntrinsicGasCost(
        execution=ExecutionGas(
            base_execution_gas
            + init_code_gas
            + data_cost
            + access_list_cost
            + auth_cost
        ),
        content_floor=ExecutionGas(content_floor_gas_cost),
    )


def count_content_bytes(tx: Transaction) -> Uint:
    """
    Count the user-controlled content bytes of a transaction.

    Calldata, access list entries, authorizations, and blob versioned
    hashes each contribute their size. A field the transaction type does
    not carry contributes nothing.
    """
    content_bytes = ulen(tx.data)

    if has_access_list(tx):
        for access in tx.access_list:
            content_bytes += ACCESS_LIST_ADDRESS_BYTES
            content_bytes += ulen(access.slots) * ACCESS_LIST_STORAGE_KEY_BYTES

    if isinstance(tx, SetCodeTransaction):
        content_bytes += ulen(tx.authorizations) * AUTHORIZATION_BYTES

    if isinstance(tx, BlobTransaction):
        content_bytes += (
            ulen(tx.blob_versioned_hashes) * BLOB_VERSIONED_HASH_BYTES
        )

    return content_bytes


def count_tokens_in_data(data: bytes) -> Uint:
    """
    Count the data tokens in arbitrary input bytes.

    Zero bytes count as 1 token; non-zero bytes count as 4 tokens.
    """
    num_zeros = Uint(data.count(0))
    num_non_zeros = ulen(data) - num_zeros

    return num_zeros + num_non_zeros * Uint(4)


def calculate_effective_gas_price(
    tx: Transaction, base_fee_per_gas: Uint
) -> Uint:
    """
    Calculate the price per unit of gas the transaction actually pays.

    A fee-market transaction pays the base fee plus a priority fee
    capped by both of its fee caps; its maximum fee must cover the base
    fee, or an `InsufficientMaxFeePerGasError` is raised. A transaction
    priced with a plain gas price pays that price outright, which must
    likewise cover the base fee.
    """
    if isinstance(tx, FeeMarketCapableTransaction):
        if tx.max_fee_per_gas < base_fee_per_gas:
            raise InsufficientMaxFeePerGasError(
                tx.max_fee_per_gas, base_fee_per_gas
            )

        priority_fee_per_gas = min(
            tx.max_priority_fee_per_gas,
            tx.max_fee_per_gas - base_fee_per_gas,
        )
        return priority_fee_per_gas + base_fee_per_gas

    if tx.gas_price < base_fee_per_gas:
        raise InvalidBlock
    return tx.gas_price


def calculate_max_gas_fee(tx: Transaction, gas_limit: Uint) -> Uint:
    """
    Calculate the largest execution-gas fee the transaction can incur:
    `gas_limit` priced at the transaction's fee cap.
    """
    if isinstance(tx, FeeMarketCapableTransaction):
        return gas_limit * tx.max_fee_per_gas
    return gas_limit * tx.gas_price


def check_nonce(tx: Transaction, sender_nonce: Uint) -> None:
    """
    Check that the transaction's nonce equals the sender's next nonce.
    """
    if sender_nonce > Uint(tx.nonce):
        raise NonceMismatchError("nonce too low")
    elif sender_nonce < Uint(tx.nonce):
        raise NonceMismatchError("nonce too high")


def chain_id(tx: Transaction) -> None | U64:
    """
    Extract the chain identifier from a transaction. See [EIP-155].

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
    """
    if isinstance(tx, LegacyTransaction):
        if tx.v == 27 or tx.v == 28:
            return None

        if tx.v < U256(35):
            raise InvalidSignatureError("bad v")

        return U64((tx.v - U256(35)) >> U256(1))
    else:
        return tx.chain_id


def recover_sender(tx: Transaction) -> Address:
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
            assert v >= U256(35), "call chain_id before recover_sender"
            tx_chain_id = U64((v - U256(35)) >> U256(1))
            v = (v - U256(35)) & U256(1)
            public_key = secp256k1_recover(
                r,
                s,
                v,
                signing_hash_155(tx, tx_chain_id),
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


def has_access_list(
    tx: Transaction,
) -> TypeGuard[AccessListCapableTransaction]:
    """
    Return whether the transaction has an [EIP-2930]-style access list.

    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    """
    return isinstance(
        tx,
        AccessListCapableTransaction,
    )
