"""Reth execution client transition tool."""

from execution_testing.exceptions import (
    BlockException,
    ExceptionMapper,
    TransactionException,
)


class RethExceptionMapper(ExceptionMapper):
    """Reth exception mapper."""

    mapping_substring = {
        TransactionException.SENDER_NOT_EOA: (
            "reject transactions from senders with deployed code"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "lack of funds",
        TransactionException.INITCODE_SIZE_EXCEEDED: "create initcode size limit",
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: "gas price is less than basefee",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "priority fee is greater than max fee"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: "overflow",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: "unexpected length",
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: "unexpected list",
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: "blob version not supported",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "empty blobs",
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: "empty authorization list",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: "unexpected length",
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "eip 7702 transactions present in pre-prague payload"
        ),
        BlockException.INVALID_REQUESTS: "mismatched block requests hash",
        BlockException.INVALID_RECEIPTS_ROOT: "receipt root mismatch",
        BlockException.INVALID_STATE_ROOT: "mismatched block state root",
        BlockException.INVALID_BLOCK_HASH: "block hash mismatch",
        BlockException.INVALID_GAS_USED: "block gas used mismatch",
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: "block is too large: ",
        BlockException.INVALID_BASEFEE_PER_GAS: "block base fee mismatch",
        BlockException.EXTRA_DATA_TOO_BIG: "invalid payload extra data",
        BlockException.INVALID_LOG_BLOOM: "header bloom filter mismatch",
    }
    mapping_regex = {
        TransactionException.NONCE_MISMATCH_TOO_LOW: r"nonce \d+ too low, expected \d+",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: r"nonce \d+ too high, expected \d+",
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price \(\d+\) is greater than max fee per blob gas \(\d+\)"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"call gas cost \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"gas floor \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: r"too many blobs, have \d+, max \d+",
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob transactions present in pre-cancun payload|empty blobs"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"transaction gas limit \w+ is more than blocks available gas \w+"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"transaction gas limit.*is greater than the cap"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: r"failed to apply .* requests contract call",
        BlockException.INCORRECT_BLOB_GAS_USED: (
            r"blob gas used mismatch|blob gas used \d+ is not a multiple of blob gas per blob"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r"excess blob gas \d+ is not a multiple of blob gas per blob|invalid excess blob gas"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            r"block used gas \(\d+\) is greater than gas limit \(\d+\)"
        ),
        BlockException.INVALID_GASLIMIT: (
            r"child gas_limit \d+ max .* is .*|child gas limit \d+ is below the minimum allowed limit"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            r"block timestamp \d+ is in the past compared to the parent timestamp \d+"
        ),
        BlockException.INVALID_BLOCK_NUMBER: (
            r"block number \d+ does not match parent block number \d+"
        ),
        # BAL Exceptions: TODO - review once all clients completed.
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"Block BAL contains an account change that is not present in the computed BAL."
        ),
        BlockException.INVALID_BAL_HASH: (r"Block's access list is invalid."),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"Block BAL is missing an account change that is present in the computed BAL."
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"Block's access list is invalid."
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"Block's access list is invalid."
        ),
        # Reth does not validate the sizes or offsets of the deposit
        # contract logs. As a workaround we have set
        # INVALID_DEPOSIT_EVENT_LAYOUT equal to INVALID_REQUESTS.
        #
        # Although this is out of spec, it is understood that this
        # will not cause an issue so long as the mainnet/testnet
        # deposit contracts don't change.
        #
        # The offsets are checked second and the sizes are checked
        # third within the `is_valid_deposit_event_data` function:
        # https://eips.ethereum.org/EIPS/eip-6110#block-validity
        #
        # EELS definition for `is_valid_deposit_event_data`:
        # https://github.com/ethereum/execution-specs/blob/5ddb904fa7ba27daeff423e78466744c51e8cb6a/src/ethereum/forks/prague/requests.py#L51
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"failed to decode deposit requests from receipts|mismatched block requests hash"
        ),
    }
