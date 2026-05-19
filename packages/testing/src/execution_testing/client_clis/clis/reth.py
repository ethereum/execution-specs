"""
Reth execution client transition tool — exception mapper only.

Reth's EVM is revm, so all the EVM-level error strings reth surfaces
match revm's `Display for InvalidTransaction` output and live in the
shared [`RevmExceptionMapper`] base. This module only contains the
strings that come from layers *above* revm — reth's payload validator,
its consensus engine, its tx pool, and its BAL validator — because
those wrap or replace revm's errors with reth-specific phrasing.
"""

from execution_testing.client_clis.clis.revm import RevmExceptionMapper
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)


class RethExceptionMapper(RevmExceptionMapper):
    """
    Reth-specific overrides on top of the revm base mapper.

    Only entries that diverge from revm's `Display for
    InvalidTransaction` belong here. Anything matching revm's core
    error vocabulary lives in [`RevmExceptionMapper`].
    """

    mapping_substring = {
        **RevmExceptionMapper.mapping_substring,
        # Reth's payload validator wording (revm itself says
        # "blob versioned hashes not supported" — that's the base).
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "blob transactions present in pre-cancun payload"
        ),
        # Reth's payload validator wording for EIP-7702 pre-Prague.
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "eip 7702 transactions present in pre-prague payload"
        ),
        # Reth's RLP decoder catches type-3/type-4 contract-creation
        # attempts at decode time and surfaces them as "unexpected
        # length" / "unexpected list" — revm never sees them, so these
        # are reth-only.
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: "unexpected length",
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: "unexpected list",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: "unexpected length",
        # Block-envelope / consensus errors — emitted by reth's
        # consensus engine, never by revm.
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
        **RevmExceptionMapper.mapping_regex,
        # Reth's blob-allowance checker phrasing.
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        # Reth tx-pool phrasing for over-budget tx gas (revm's
        # equivalent "caller gas limit exceeds the block gas limit"
        # lives in the base).
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"transaction gas limit \w+ is more than blocks available gas \w+"
        ),
        # Reth tx-pool phrasing.
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"transaction gas limit.*is greater than the cap"
        ),
        # Reth consensus / block-execution errors.
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
        # BAL exceptions — reth's BAL validator.
        BlockException.INVALID_BAL_HASH: (r"block access list hash mismatch"),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"block access list hash mismatch"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"block access list hash mismatch"
        ),
        # Reth does not validate the sizes or offsets of the deposit
        # contract logs. As a workaround we map INVALID_DEPOSIT_EVENT_LAYOUT
        # to the same error pattern as INVALID_REQUESTS.
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
    }
