"""Ethrex execution client transition tool."""

from ethereum_test_exceptions import BlockException, ExceptionMapper, TransactionException


class EthrexExceptionMapper(ExceptionMapper):
    """Ethrex exception mapper."""

    mapping_substring = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "Exceeded MAX_BLOB_GAS_PER_BLOCK"
        ),
        TransactionException.INVALID_DEPOSIT_EVENT_LAYOUT: ("Invalid deposit request layout"),
        BlockException.INVALID_REQUESTS: (
            "Requests hash does not match the one in the header after executing"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: (
            "Receipts Root does not match the one in the header after executing"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "World State Root does not match the one in the header after executing"
        ),
        BlockException.INVALID_GAS_USED: "Gas used doesn't match value in header",
        BlockException.INCORRECT_BLOB_GAS_USED: "Blob gas used doesn't match value in header",
    }
    mapping_regex = {
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            r"(?i)priority fee is greater than max fee"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: r"(?i)empty authorization list",
        TransactionException.SENDER_NOT_EOA: (
            r"reject transactions from senders with deployed code|"
            r"Sender account should not have bytecode"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: r"nonce \d+ too low, expected \d+",
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
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob versioned hashes not supported|"
            r"Type 3 transactions are not supported before the Cancun fork"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            r"unexpected length|Contract creation in type 4 transaction"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            r"eip 7702 transactions present in pre-prague payload|"
            r"Type 4 transactions are not supported before the Prague fork"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            r"lack of funds \(\d+\) for max fee \(\d+\)|Insufficient account founds"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"gas floor exceeds the gas limit|call gas cost exceeds the gas limit|"
            r"Intrinsic gas too low"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            r"gas price is less than basefee|Insufficient max fee per gas"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price is greater than max fee per blob gas|"
            r"Insufficient max fee per blob gas"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            r"create initcode size limit|Initcode size exceeded"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (r"failed to apply .* requests contract call"),
        BlockException.INCORRECT_BLOB_GAS_USED: (r"Blob gas used doesn't match value in header"),
        BlockException.RLP_STRUCTURES_ENCODING: (r"Error decoding field '\D+' of type \w+.*"),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (r".* Excess blob gas is incorrect"),
        BlockException.INVALID_BLOCK_HASH: (r"Invalid block hash. Expected \w+, got \w+"),
    }
