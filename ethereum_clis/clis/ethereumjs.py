"""EthereumJS Transition tool interface."""

import re
from pathlib import Path
from typing import ClassVar, Dict, Optional

from ethereum_test_exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool


class EthereumJSTransitionTool(TransitionTool):
    """EthereumJS Transition tool interface wrapper class."""

    default_binary = Path("ethereumjs-t8ntool.sh")
    detect_binary_pattern = re.compile(r"^ethereumjs t8n\b")
    version_flag: str = "--version"
    t8n_use_stream = False

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the EthereumJS Transition tool interface."""
        super().__init__(exception_mapper=EthereumJSExceptionMapper(), binary=binary, trace=trace)

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.
        Currently, EthereumJS-t8n provides no way to determine supported forks.
        """
        return True


class EthereumJSExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by EthereumJS."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "would exceed maximum allowance"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "Invalid 4844 transactions: undefined"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            "gas limit * gasPrice cannot exceed MAX_INTEGER"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: "tx unable to pay base fee",
        TransactionException.NONCE_IS_MAX: "nonce cannot equal or exceed",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "maxFeePerGas cannot be less than maxPriorityFeePerGas"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "versioned hash does not start with KZG commitment version"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "exceed maximum allowance",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "tx should contain at least one blob",
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: "Invalid EIP-4844 transaction",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            'tx should have a "to" field and cannot be used to create contracts'
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "Invalid EIP-7702 transaction: authorization list is empty"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: "is lower than the minimum gas limit of",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "is lower than the minimum gas limit of"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "the initcode size of this transaction is too large"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            'tx should have a "to" field and cannot be used to create contracts'
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "sender doesn't have enough funds to send tx"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "the tx doesn't have the correct nonce",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "tx has a higher gas limit than the block",
        BlockException.INCORRECT_EXCESS_BLOB_GAS: "Invalid 4844 transactions",
        BlockException.INVALID_RECEIPTS_ROOT: "invalid receipttrie",
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "Error verifying block while running: error: number exceeds 53 bits"
        ),
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"tx causes total blob gas of \d+ to exceed maximum blob gas per block of \d+|"
            r"tx can contain at most \d+ blobs"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"tx causes total blob gas of \d+ to exceed maximum blob gas per block of \d+|"
            r"tx can contain at most \d+ blobs"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob tx used but field env.ExcessBlobGas missing|EIP-4844 not enabled on Common"
        ),
        BlockException.BLOB_GAS_USED_ABOVE_LIMIT: r"invalid blobGasUsed expected=\d+ actual=\d+",
        BlockException.INCORRECT_BLOB_GAS_USED: r"invalid blobGasUsed expected=\d+ actual=\d+",
        BlockException.INVALID_BLOCK_HASH: (
            r"Invalid blockHash, expected: 0x[0-9a-f]+, received: 0x[0-9a-f]+"
        ),
        BlockException.INVALID_REQUESTS: r"Unknown request identifier|invalid requestshash",
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            r"Invalid block: too much gas used. Used: \d+, gas limit: \d+"
        ),
    }
