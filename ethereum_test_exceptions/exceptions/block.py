"""Block Exceptions."""

from enum import auto, unique

from .base import ExceptionBase


@unique
class BlockException(ExceptionBase):
    """
    Exception raised when a block is invalid, but not due to a transaction.

    E.g. all transactions in the block are valid, and can be applied to the state, but the
    block header contains an invalid field.
    """

    TOO_MANY_UNCLES = auto()
    """
    Block declares too many uncles over the allowed limit.
    """
    UNCLE_IN_CHAIN = auto()
    """
    Block declares uncle header that is already imported into chain.
    """
    UNCLE_IS_ANCESTOR = auto()
    """
    Block declares uncle header that is directly a parent of this block.
    """
    UNCLE_IS_BROTHER = auto()
    """
    Block declares two similar uncle headers.
    """
    UNCLE_PARENT_INCORRECT = auto()
    """
    Block declares uncle header that is an outdated block to be an uncle.
    """
    EXTRA_DATA_TOO_BIG = auto()
    """
    Block header's extra data >32 bytes.
    """
    EXTRA_DATA_INVALID_DAO = auto()
    """
    Block header's extra data after dao fork must be a fixed pre defined hash.
    """
    UNKNOWN_PARENT = auto()
    """
    Block header's parent hash does not correspond to any of existing blocks on chain.
    """
    UNCLE_UNKNOWN_PARENT = auto()
    """
    Uncle header's parent hash does not correspond to any of existing blocks on chain.
    """
    UNKNOWN_PARENT_ZERO = auto()
    """
    Block header's parent hash is zero hash.
    """
    GASLIMIT_TOO_BIG = auto()
    """
    Block header's gas limit > 0x7fffffffffffffff.
    """
    INVALID_BLOCK_NUMBER = auto()
    """
    Block header's number != parent header's number + 1.
    """
    INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT = auto()
    """
    Block header's timestamp <= parent header's timestamp.
    """
    INVALID_DIFFICULTY = auto()
    """
    Block header's difficulty does not match the difficulty formula calculated from previous block.
    """
    INVALID_LOG_BLOOM = auto()
    """
    Block header's logs bloom hash does not match the actually computed log bloom.
    """
    INVALID_STATE_ROOT = auto()
    """
    Block header's state root hash does not match the actually computed hash of the state.
    """
    INVALID_RECEIPTS_ROOT = auto()
    """
    Block header's receipts root hash does not match the actually computed hash of receipts.
    """
    INVALID_TRANSACTIONS_ROOT = auto()
    """
    Block header's transactions root hash does not match the actually computed hash of tx tree.
    """
    INVALID_UNCLES_HASH = auto()
    """
    Block header's uncle hash does not match the actually computed hash of block's uncles.
    """
    GAS_USED_OVERFLOW = auto()
    """
    Block transactions consume more gas than block header allow.
    """
    INVALID_GASLIMIT = auto()
    """
    Block header's gas limit does not match the gas limit formula calculated from previous block.
    """
    INVALID_BASEFEE_PER_GAS = auto()
    """
    Block header's base_fee_per_gas field is calculated incorrect.
    """
    INVALID_GAS_USED = auto()
    """
    Block header's actual gas used does not match the provided header's value
    """
    INVALID_GAS_USED_ABOVE_LIMIT = auto()
    """
    Block header's gas used value is above the gas limit field's value.
    """
    INVALID_WITHDRAWALS_ROOT = auto()
    """
    Block header's withdrawals root does not match calculated withdrawals root.
    """
    INCORRECT_BLOCK_FORMAT = auto()
    """
    Block's format is incorrect, contains invalid fields, is missing fields, or contains fields of
    a fork that is not active yet.
    """
    BLOB_GAS_USED_ABOVE_LIMIT = auto()
    """
    Block's blob gas used in header is above the limit.
    """
    INCORRECT_BLOB_GAS_USED = auto()
    """
    Block's blob gas used in header is incorrect.
    """
    INCORRECT_EXCESS_BLOB_GAS = auto()
    """
    Block's excess blob gas in header is incorrect.
    """
    INVALID_VERSIONED_HASHES = auto()
    """
    Incorrect number of versioned hashes in a payload.
    """
    RLP_STRUCTURES_ENCODING = auto()
    """
    Block's rlp encoding is valid but ethereum structures in it are invalid.
    """
    RLP_WITHDRAWALS_NOT_READ = auto()
    """
    Block's rlp encoding is missing withdrawals.
    """
    RLP_INVALID_FIELD_OVERFLOW_64 = auto()
    """
    One of block's fields rlp is overflow 2**64 value.
    """
    RLP_INVALID_ADDRESS = auto()
    """
    Block withdrawals address is rlp of invalid address != 20 bytes.
    """
    RLP_BLOCK_LIMIT_EXCEEDED = auto()
    """
    Block's rlp encoding is larger than the allowed limit.
    """
    INVALID_REQUESTS = auto()
    """
    Block's requests are invalid.
    """
    IMPORT_IMPOSSIBLE_LEGACY = auto()
    """
    Legacy block import is impossible in this chain configuration.
    """
    IMPORT_IMPOSSIBLE_LEGACY_WRONG_PARENT = auto()
    """
    Legacy block import is impossible, trying to import on top of a block that is not legacy.
    """
    IMPORT_IMPOSSIBLE_LONDON_WRONG_PARENT = auto()
    """
    Trying to import london (basefee) block on top of block that is not 1559.
    """
    IMPORT_IMPOSSIBLE_PARIS_WRONG_POW = auto()
    """
    Trying to import paris(merge) block with PoW enabled.
    """
    IMPORT_IMPOSSIBLE_PARIS_WRONG_POS = auto()
    """
    Trying to import paris(merge) block with PoS enabled before TTD is reached.
    """
    IMPORT_IMPOSSIBLE_LONDON_OVER_PARIS = auto()
    """
    Trying to import london looking block over paris network (POS).
    """
    IMPORT_IMPOSSIBLE_PARIS_OVER_SHANGHAI = auto()
    """
    Trying to import paris block on top of shanghai block.
    """
    IMPORT_IMPOSSIBLE_SHANGHAI = auto()
    """
    Shanghai block import is impossible in this chain configuration.
    """
    IMPORT_IMPOSSIBLE_UNCLES_OVER_PARIS = auto()
    """
    Trying to import a block after paris fork that has not empty uncles hash.
    """
    IMPORT_IMPOSSIBLE_DIFFICULTY_OVER_PARIS = auto()
    """
    Trying to import a block after paris fork that has difficulty != 0.
    """
    SYSTEM_CONTRACT_EMPTY = auto()
    """
    A system contract address contains no code at the end of fork activation block.
    """
    SYSTEM_CONTRACT_CALL_FAILED = auto()
    """
    A system contract call at the end of block execution (from the system address) fails.
    """
    INVALID_BLOCK_HASH = auto()
    """
    Block header's hash does not match the actually computed hash of the block.
    """
    INVALID_DEPOSIT_EVENT_LAYOUT = auto()
    """
    Transaction emits a `DepositEvent` in the deposit contract (EIP-6110), but the layout
    of the event does not match the required layout.
    """
