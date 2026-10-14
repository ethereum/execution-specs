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
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "create initcode size limit"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "gas price is less than basefee"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "priority fee is greater than max fee"
        ),
        TransactionException.GASPRICE_OVERFLOW: (
            "EIP-8141 max fee per gas exceeds 256 bits"
        ),
        TransactionException.PRIORITY_OVERFLOW: (
            "EIP-8141 max priority fee per gas exceeds 256 bits"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: "overflow",
        TransactionException.NONCE_IS_MAX: "nonce overflow in transaction",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: "unexpected length",
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: "unexpected list",
        TransactionException.INVALID_CHAINID: "invalid chain ID",
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "blob version not supported"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "empty blobs",
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "empty authorization list"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: "unexpected length",
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "eip 7702 transactions present in pre-prague payload"
        ),
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT: (
            "Eip8141 transaction has invalid fields"
        ),
        TransactionException.TYPE_6_INVALID_SIGNATURE: (
            "EIP-8141 signature validation failed"
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
        # alloy drops the parity error for an out-of-range legacy `v` and
        # reports the failed untagged decode ("Unexpected type flag") instead.
        TransactionException.INVALID_SIGNATURE_VRS: (
            r"invalid bool value, must be 0 or 1|"
            r"Failed to recover the signer|"
            r"Unexpected type flag"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            r"nonce \d+ too low, expected \d+|"
            r"EIP-8250 nonce sequence mismatch"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            r"nonce \d+ too high, expected \d+|"
            r"EIP-8250 nonce sequence mismatch"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price \(\d+\) is greater than "
            r"max fee per blob gas \(\d+\)"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"call gas cost \(\d+\) exceeds the gas limit \(\d+\)|"
            r"gas floor \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"gas floor \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"too many blobs, have \d+, max \d+"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob transactions present in pre-cancun payload|empty blobs"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"transaction gas limit \w+ is more than blocks available gas \w+|"
            r"caller gas limit exceeds the block gas limit"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"transaction gas limit.*is greater than the cap"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"failed to apply .* requests contract call"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            r"blob gas used mismatch|"
            r"blob gas used \d+ is not a multiple of blob gas per blob"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r"excess blob gas \d+ is not a multiple of blob gas per blob|"
            r"invalid excess blob gas"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            r"block used gas \(\d+\) is greater than gas limit \(\d+\)"
        ),
        BlockException.INVALID_GASLIMIT: (
            r"child gas_limit \d+ max .* is .*|"
            r"child gas_limit \d+ is below the max allowed decrease .*|"
            r"child gas limit \d+ is below the minimum allowed limit"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            r"block timestamp \d+ is in the past compared to "
            r"the parent timestamp \d+"
        ),
        BlockException.INVALID_BLOCK_NUMBER: (
            r"block number \d+ does not match parent block number \d+"
        ),
        BlockException.GAS_USED_OVERFLOW: (
            r"transaction gas limit \w+ is more than blocks available gas \w+"
        ),
        # BAL Exceptions
        BlockException.INVALID_BAL_HASH: (r"block access list hash mismatch"),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"failed to decode block access list|"
            r"block access list hash mismatch|"
            r"BAL rejection: FinalHashMismatch|"
            r"Bal error: Account .* not found in BAL|"
            r"Bal error: Slot .* not found in BAL for account .*"
        ),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            r"block access list item cost exceeds gas limit"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"system contract .* has no code"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"block access list hash mismatch|"
            r"BAL rejection: FinalHashMismatch"
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
            r"failed to decode deposit requests from receipts|"
            r"mismatched block requests hash"
        ),
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT: (
            r"invalid EIP-8141 frame format:|"
            r"invalid EIP-8141 address length|"
            r"invalid EIP-8141 frame mode|"
            r"invalid EIP-8141 signature scheme|"
            r"invalid EIP-8141 signature message length|"
            r"EIP-8141 signature message must be nonzero|"
            r"EIP-8141 frame count must be in 1\.\.=64|"
            r"EIP-8141 reserved frame flag is set|"
            r"only EIP-8141 SENDER frames may transfer value|"
            r"EIP-8141 execution approval target must be the sender|"
            r"EIP-8141 atomic flag is invalid on VERIFY frames|"
            r"EIP-8141 atomic batch must be followed by a non-VERIFY frame|"
            r"EIP-8141 atomic batch frames cannot carry approval scope|"
            r"malformed EIP-8141 expiry verifier frame|"
            r"multiple EIP-8141 expiry verifier frames|"
            r"EIP-8141 arbitrary signature signer must be empty|"
            r"EIP-8141 signature signer does not match|"
            r"EIP-7906 atomic flag is invalid on POST_TX frames|"
            r"EIP-7906 atomic batch cannot end on a POST_TX frame|"
            r"EIP-7906 POST_TX frames must form a trailing suffix|"
            r"EIP-8250 nonce key zero must be the only key|"
            r"EIP-8250 nonce keys must be strictly increasing|"
            r"EIP-8250 requires between 1 and 16 nonce keys|"
            r"EIP-8250 nonce key exceeds 256 bits|"
            r"EIP-8250 nonce sequence exceeds 64 bits"
        ),
        TransactionException.TYPE_6_INVALID_FRAME_EXECUTION: (
            r"EIP-8141 SENDER frame executed before execution approval|"
            r"EIP-8141 VERIFY frame failed|"
            r"EIP-8141 transaction did not approve a payer"
        ),
    }
