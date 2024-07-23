"""
Defines EIP-7251 specification constants and functions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_7251 = ReferenceSpec("EIPS/eip-7251.md", "e5af719767e789c88c0e063406c6557c8f53cfba")


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7251 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7251#execution-layer
    """

    CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = 0x00B42DBF2194E931E80326D950320F7D9DBEAC02
    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE

    EXCESS_CONSOLIDATION_REQUESTS_STORAGE_SLOT = 0
    CONSOLIDATION_REQUEST_COUNT_STORAGE_SLOT = 1
    CONSOLIDATION_REQUEST_QUEUE_HEAD_STORAGE_SLOT = (
        2  # Pointer to head of the consolidation request message queue
    )
    CONSOLIDATION_REQUEST_QUEUE_TAIL_STORAGE_SLOT = (
        3  # Pointer to the tail of the consolidation request message queue
    )
    CONSOLIDATION_REQUEST_QUEUE_STORAGE_OFFSET = (
        4  # The start memory slot of the in-state consolidation request message queue
    )
    MAX_CONSOLIDATION_REQUESTS_PER_BLOCK = (
        1  # Maximum number of consolidation requests that can be de-queued into a block
    )
    TARGET_CONSOLIDATION_REQUESTS_PER_BLOCK = 1
    MIN_CONSOLIDATION_REQUEST_FEE = 1
    CONSOLIDATION_REQUEST_FEE_UPDATE_FRACTION = 17
    EXCESS_INHIBITOR = 1181

    @staticmethod
    def fake_exponential(factor: int, numerator: int, denominator: int) -> int:
        """
        Used to calculate the consolidation request fee.
        """
        i = 1
        output = 0
        numerator_accumulator = factor * denominator
        while numerator_accumulator > 0:
            output += numerator_accumulator
            numerator_accumulator = (numerator_accumulator * numerator) // (denominator * i)
            i += 1
        return output // denominator

    @staticmethod
    def get_fee(excess_consolidation_requests: int) -> int:
        """
        Calculate the fee for the excess consolidation requests.
        """
        return Spec.fake_exponential(
            Spec.MIN_CONSOLIDATION_REQUEST_FEE,
            excess_consolidation_requests,
            Spec.CONSOLIDATION_REQUEST_FEE_UPDATE_FRACTION,
        )

    @staticmethod
    def get_excess_consolidation_requests(previous_excess: int, count: int) -> int:
        """
        Calculate the new excess consolidation requests.
        """
        if previous_excess + count > Spec.TARGET_CONSOLIDATION_REQUESTS_PER_BLOCK:
            return previous_excess + count - Spec.TARGET_CONSOLIDATION_REQUESTS_PER_BLOCK
        return 0
