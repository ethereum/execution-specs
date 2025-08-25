"""Nimbus Transition tool interface."""

import re
import subprocess
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


class NimbusTransitionTool(TransitionTool):
    """Nimbus `evm` Transition tool interface wrapper class."""

    default_binary = Path("t8n")
    detect_binary_pattern = re.compile(r"^Nimbus-t8n\b")
    version_flag: str = "--version"

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the Nimbus Transition tool interface."""
        super().__init__(exception_mapper=NimbusExceptionMapper(), binary=binary, trace=trace)
        args = [str(self.binary), "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(
                f"evm process unexpectedly returned a non-zero status code: {e}."
            ) from e
        except Exception as e:
            raise Exception(f"Unexpected exception calling evm tool: {e}.") from e
        self.help_string = result.stdout

    def version(self) -> str:
        """Get `evm` binary version."""
        if self.cached_version is None:
            self.cached_version = re.sub(r"\x1b\[0m", "", super().version()).strip()

        return self.cached_version

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.
        """
        return fork.transition_tool_name() in self.help_string


class NimbusExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Nimbus."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "set code transaction must not be a create transaction"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "invalid tx: not enough cash to send",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "would exceed maximum allowance"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max fee per blob gas less than block blob gas fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "blob tx used but field env.ExcessBlobGas missing"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "invalid tx: one of blobVersionedHash has invalid version"
        ),
        # TODO: temp solution until mapper for nimbus is fixed
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: "zero gasUsed but transactions present",
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "exceeds maximum allowance",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "blob transaction missing blob hashes",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "zero gasUsed but transactions present",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: "intrinsic gas too low",
        TransactionException.INITCODE_SIZE_EXCEEDED: "max initcode size exceeded",
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            # TODO:
            "ExceededBlockSizeLimit: Exceeded block size limit"
        ),
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
