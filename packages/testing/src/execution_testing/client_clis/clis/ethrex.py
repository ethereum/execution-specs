"""Ethrex execution client transition tool."""

from execution_testing.exceptions import (
    BlockException,
    ExceptionMapper,
    TransactionException,
)


class EthrexExceptionMapper(ExceptionMapper):
    """Ethrex exception mapper."""

    mapping_substring = {
        BlockException.INVALID_GASLIMIT: (
            "Gas limit changed more than allowed from the parent"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "Exceeded MAX_BLOB_GAS_PER_BLOCK"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "Invalid deposit request layout"
        ),
        BlockException.INVALID_REQUESTS: (
            "Requests hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: (
            "Receipts Root does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "World State Root does not match the one in "
            "the header after executing"
        ),
        BlockException.GAS_USED_OVERFLOW: "Block gas used overflow",
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_BAL_HASH: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            "not in strictly ascending order for"
        ),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            "Block access list exceeds gas limit"
        ),
        BlockException.INVALID_GAS_USED: (
            "Gas used doesn't match value in header"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            "Blob gas used doesn't match value in header"
        ),
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "Base fee per gas is incorrect"
        ),
    }
    mapping_regex = {
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            r"(?i)priority fee.* is greater than max fee.*"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            r"(?i)empty authorization list"
        ),
        TransactionException.SENDER_NOT_EOA: (
            r"reject transactions from senders with deployed code|"
            r"Sender account .* shouldn't be a contract"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            r"nonce \d+ too low, expected \d+|Nonce mismatch.*"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: r"Nonce mismatch.*",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            r"blob transactions present in pre-cancun payload|empty blobs|"
            r"Type 3 transaction without blobs"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            r"blob version not supported|Invalid blob versioned hash"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            r"Type 2 transactions are not supported before the London fork"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob versioned hashes not supported|"
            r"Type 3 transactions are not supported before the Cancun fork"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            r"unexpected length|Contract creation in type 4 transaction|"
            r"Error decoding field 'to' of type primitive_types::H160: "
            r"InvalidLength"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            r"unexpected length|Contract creation in type 3 transaction|"
            r"Error decoding field 'to' of type primitive_types::H160: "
            r"InvalidLength"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            r"eip 7702 transactions present in pre-prague payload|"
            r"Type 4 transactions are not supported before the Prague fork"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            r"lack of funds \(\d+\) for max fee \(\d+\)|"
            r"Insufficient account funds"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"gas floor exceeds the gas limit|"
            r"call gas cost exceeds the gas limit|"
            r"Transaction gas limit lower than the minimum gas cost "
            r"to execute the transaction|"
            r"Transaction gas limit lower than the gas cost floor "
            r"for calldata tokens"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"Transaction gas limit lower than the gas cost floor "
            r"for calldata tokens"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            r"gas price is less than basefee|"
            r"Insufficient max fee per gas"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price is greater than max fee per blob gas|"
            r"Insufficient max fee per blob gas.*"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            r"create initcode size limit|Initcode size exceeded.*"
        ),
        TransactionException.NONCE_IS_MAX: (r"Nonce is max"),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"Gas allowance exceeded.*"
        ),
        BlockException.GAS_USED_OVERFLOW: (r"Block gas used overflow.*"),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"Blob count exceeded.*"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            r"Invalid transaction: Gas limit price product overflow.*"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"Invalid transaction: "
            r"Transaction gas limit exceeds maximum.*"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"Invalid deposit request layout|BAL validation failed.*"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (r"System call failed.*"),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"System contract:.* has no code after deployment"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            r"Blob gas used doesn't match value in header"
        ),
        BlockException.RLP_STRUCTURES_ENCODING: (
            r"Error decoding field '\D+' of type \w+.*"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r".* Excess blob gas is incorrect"
        ),
        BlockException.INVALID_BLOCK_HASH: (
            r"Invalid block hash. Expected \w+, got \w+"
        ),
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            r"Maximum block size exceeded.*"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"Block access list accounts not in strictly ascending order.*|"
            r"BAL validation failed: account .* was never accessed.*"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (r"absent from BAL"),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"Block access list contains index \d+ "
            r"exceeding max valid index \d+|"
            r"Failed to RLP decode BAL|"
            r"Block access list .+ not in strictly ascending order.*|"
            r"BAL validation failed for (tx \d+|system_tx|withdrawal): .*|"
            r"BAL validation failed: .*|"
            r"Block access list slot .+ is in both "
            r"storage_changes and storage_reads.*"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"Block access list hash does not match "
            r"the one in the header after executing|"
            r"Block access list contains index \d+ "
            r"exceeding max valid index \d+|"
            r"Failed to RLP decode BAL|"
            r"Block access list accounts not in strictly ascending order.*"
        ),
    }
