"""Transaction Exceptions."""

from enum import auto, unique

from .base import ExceptionBase


@unique
class TransactionException(ExceptionBase):
    """
    Exception raised when a transaction is invalid, and thus cannot be executed.

    If a transaction with any of these exceptions is included in a block, the block is invalid.
    """

    TYPE_NOT_SUPPORTED = auto()
    """
    Transaction type is not supported on this chain configuration.
    """
    SENDER_NOT_EOA = auto()
    """
    Transaction is coming from address that is not exist anymore.
    """
    ADDRESS_TOO_SHORT = auto()
    """
    Transaction `to` is not allowed to be less than 20 bytes.
    """
    ADDRESS_TOO_LONG = auto()
    """
    Transaction `to` is not allowed to be more than 20 bytes.
    """
    NONCE_MISMATCH_TOO_HIGH = auto()
    """
    Transaction nonce > sender.nonce.
    """
    NONCE_MISMATCH_TOO_LOW = auto()
    """
    Transaction nonce < sender.nonce.
    """
    NONCE_TOO_BIG = auto()
    """
    Transaction `nonce` is not allowed to be max_uint64 - 1 (this is probably TransactionTest).
    """
    NONCE_IS_MAX = auto()
    """
    Transaction `nonce` is not allowed to be max_uint64 - 1 (this is StateTests).
    """
    NONCE_OVERFLOW = auto()
    """
    Transaction `nonce` is not allowed to be more than uint64.
    """
    GASLIMIT_OVERFLOW = auto()
    """
    Transaction gaslimit exceeds 2^64-1 maximum value.
    """
    VALUE_OVERFLOW = auto()
    """
    Transaction value exceeds 2^256-1 maximum value.
    """
    GASPRICE_OVERFLOW = auto()
    """
    Transaction gasPrice exceeds 2^256-1 maximum value.
    """
    GASLIMIT_PRICE_PRODUCT_OVERFLOW = auto()
    """
    Transaction gasPrice * gasLimit exceeds 2^256-1 maximum value.
    """
    INVALID_SIGNATURE_VRS = auto()
    """
    Invalid transaction v, r, s values.
    """
    RLP_INVALID_SIGNATURE_R = auto()
    """
    Error reading transaction signature R value.
    """
    RLP_INVALID_SIGNATURE_S = auto()
    """
    Error reading transaction signature S value.
    """
    RLP_LEADING_ZEROS_GASLIMIT = auto()
    """
    Error reading transaction gaslimit field RLP.
    """
    RLP_LEADING_ZEROS_GASPRICE = auto()
    """
    Error reading transaction gasprice field RLP.
    """
    RLP_LEADING_ZEROS_VALUE = auto()
    """
    Error reading transaction value field RLP.
    """
    RLP_LEADING_ZEROS_NONCE = auto()
    """
    Error reading transaction nonce field RLP.
    """
    RLP_LEADING_ZEROS_R = auto()
    """
    Error reading transaction signature R field RLP.
    """
    RLP_LEADING_ZEROS_S = auto()
    """
    Error reading transaction signature S field RLP.
    """
    RLP_LEADING_ZEROS_V = auto()
    """
    Error reading transaction signature V field RLP.
    """
    RLP_LEADING_ZEROS_BASEFEE = auto()
    """
    Error reading transaction basefee field RLP.
    """
    RLP_LEADING_ZEROS_PRIORITY_FEE = auto()
    """
    Error reading transaction priority fee field RLP.
    """
    RLP_LEADING_ZEROS_DATA_SIZE = auto()
    """
    Error reading transaction data field RLP, (rlp field length has leading zeros).
    """
    RLP_LEADING_ZEROS_NONCE_SIZE = auto()
    """
    Error reading transaction nonce field RLP, (rlp field length has leading zeros).
    """
    RLP_TOO_FEW_ELEMENTS = auto()
    """
    Error reading transaction RLP, structure has too few elements than expected.
    """
    RLP_TOO_MANY_ELEMENTS = auto()
    """
    Error reading transaction RLP, structure has too many elements than expected.
    """
    RLP_ERROR_EOF = auto()
    """
    Error reading transaction RLP, rlp stream unexpectedly finished.
    """
    RLP_ERROR_SIZE = auto()
    """
    Error reading transaction RLP, rlp size is invalid.
    """
    RLP_ERROR_SIZE_LEADING_ZEROS = auto()
    """
    Error reading transaction RLP, field size has leading zeros.
    """
    INVALID_CHAINID = auto()
    """
    Transaction chain id encoding is incorrect.
    """
    RLP_INVALID_DATA = auto()
    """
    Transaction data field is invalid rlp.
    """
    RLP_INVALID_GASLIMIT = auto()
    """
    Transaction gaslimit field is invalid rlp.
    """
    RLP_INVALID_NONCE = auto()
    """
    Transaction nonce field is invalid rlp.
    """
    RLP_INVALID_TO = auto()
    """
    Transaction to field is invalid rlp.
    """
    RLP_INVALID_ACCESS_LIST_ADDRESS_TOO_LONG = auto()
    """
    Transaction access list address is > 20 bytes.
    """
    RLP_INVALID_ACCESS_LIST_ADDRESS_TOO_SHORT = auto()
    """
    Transaction access list address is < 20 bytes.
    """
    RLP_INVALID_ACCESS_LIST_STORAGE_TOO_LONG = auto()
    """
    Transaction access list storage hash > 32 bytes.
    """
    RLP_INVALID_ACCESS_LIST_STORAGE_TOO_SHORT = auto()
    """
    Transaction access list storage hash < 32 bytes.
    """
    RLP_INVALID_HEADER = auto()
    """
    Transaction failed to read from RLP as rlp header is invalid.
    """
    RLP_INVALID_VALUE = auto()
    """
    Transaction value field is invalid rlp/structure.
    """
    EC_RECOVERY_FAIL = auto()
    """
    Transaction has correct signature, but ec recovery failed.
    """
    INSUFFICIENT_ACCOUNT_FUNDS = auto()
    """
    Transaction's sender does not have enough funds to pay for the transaction.
    """
    INSUFFICIENT_MAX_FEE_PER_GAS = auto()
    """
    Transaction's max-fee-per-gas is lower than the block base-fee.
    """
    PRIORITY_OVERFLOW = auto()
    """
    Transaction's max-priority-fee-per-gas is exceeds 2^256-1 maximum value.
    """
    PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS = auto()
    """
    Transaction's max-priority-fee-per-gas is greater than the max-fee-per-gas.
    """
    PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS_2 = auto()
    """
    Transaction's max-priority-fee-per-gas is greater than the max-fee-per-gas (TransactionTests).
    """
    INSUFFICIENT_MAX_FEE_PER_BLOB_GAS = auto()
    """
    Transaction's max-fee-per-blob-gas is lower than the block's blob-gas price.
    """
    INTRINSIC_GAS_TOO_LOW = auto()
    """
    Transaction's gas limit is too low.
    """
    INTRINSIC_GAS_BELOW_FLOOR_GAS_COST = auto()
    """
    Transaction's gas limit is below the floor gas cost.
    """
    INITCODE_SIZE_EXCEEDED = auto()
    """
    Transaction's initcode for a contract-creating transaction is too large.
    """
    TYPE_3_TX_PRE_FORK = auto()
    """
    Transaction type 3 included before activation fork.
    """
    TYPE_3_TX_ZERO_BLOBS_PRE_FORK = auto()
    """
    Transaction type 3, with zero blobs, included before activation fork.
    """
    TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH = auto()
    """
    Transaction contains a blob versioned hash with an invalid version.
    """
    TYPE_3_TX_WITH_FULL_BLOBS = auto()
    """
    Transaction contains full blobs (network-version of the transaction).
    """
    TYPE_3_TX_BLOB_COUNT_EXCEEDED = auto()
    """
    Transaction contains too many blob versioned hashes.
    """
    TYPE_3_TX_CONTRACT_CREATION = auto()
    """
    Transaction is a type 3 transaction and has an empty `to`.
    """
    TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED = auto()
    """
    Transaction causes block to go over blob gas limit.
    """
    GAS_ALLOWANCE_EXCEEDED = auto()
    """
    Transaction causes block to go over blob gas limit.
    """
    GAS_LIMIT_EXCEEDS_MAXIMUM = auto()
    """
    Transaction gas limit exceeds the maximum allowed limit of 30 million.
    """
    TYPE_3_TX_ZERO_BLOBS = auto()
    """
    Transaction is type 3, but has no blobs.
    """
    TYPE_4_EMPTY_AUTHORIZATION_LIST = auto()
    """
    Transaction is type 4, but has an empty authorization list.
    """
    TYPE_4_INVALID_AUTHORITY_SIGNATURE = auto()
    """
    Transaction authority signature is invalid
    """
    TYPE_4_INVALID_AUTHORITY_SIGNATURE_S_TOO_HIGH = auto()
    """
    Transaction authority signature is invalid
    """
    TYPE_4_TX_CONTRACT_CREATION = auto()
    """
    Transaction is a type 4 transaction and has an empty `to`.
    """
    TYPE_4_INVALID_AUTHORIZATION_FORMAT = auto()
    """
    Transaction is type 4, but contains an authorization that has an invalid format.
    """
    TYPE_4_TX_PRE_FORK = auto()
    """
    Transaction type 4 included before activation fork.
    """
