"""Mempool Exceptions."""

from enum import auto, unique

from .base import ExceptionBase


@unique
class MempoolException(ExceptionBase):
    """
    Exception raised when the public mempool refuses a transaction that is
    valid for inclusion in the next block.

    A block that includes a transaction with any of these exceptions is still
    valid.
    """

    NONCE_GAP = auto()
    """Transaction nonce is above the sender's nonce, so it cannot execute."""
    FRAME_PREFIX_NOT_RECOGNIZED = auto()
    """Frame transaction validation prefix has no recognized shape."""
    FRAME_VALIDATION_BANNED_OPCODE = auto()
    """Frame transaction validation prefix executes a banned opcode."""
    FRAME_VALIDATION_STORAGE_ACCESS = auto()
    """Frame transaction validation prefix reads storage outside the sender."""
    FRAME_VALIDATION_GAS_EXCEEDED = auto()
    """Frame transaction validation prefix exceeds the validation gas cap."""
    FRAME_VALIDATION_STATE_GAS_EXCEEDED = auto()
    """Frame transaction validation prefix exceeds the state gas cap."""
    FRAME_VALIDATION_STATE_WRITE = auto()
    """Frame transaction validation prefix writes state it may not write."""
    FRAME_VALIDATION_REVERTED = auto()
    """A frame in the frame transaction validation prefix reverts."""
    FRAME_DEPLOY_CODE_NOT_INSTALLED = auto()
    """Frame transaction deploy frame installs no code at the sender."""
    FRAME_EXPIRED = auto()
    """Frame transaction deadline is before the head timestamp."""
    PAYMASTER_INSUFFICIENT_BALANCE = auto()
    """Paymaster balance does not cover the transaction's maximum cost."""
