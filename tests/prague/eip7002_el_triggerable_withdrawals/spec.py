"""
Common procedures to test
[EIP-7002: Execution layer triggerable
withdrawals](https://eips.ethereum.org/EIPS/eip-7002).
"""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7002 = ReferenceSpec(
    "EIPS/eip-7002.md", "695ac757472b9bbbdcbc88a020ba15c1ac782869"
)


# Constants
class Spec:
    """
    Parameters from the EIP-7002 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7002#configuration.

    The request queue parameters live on the framework's `WithdrawalRequest`.
    """

    WITHDRAWAL_REQUEST_PREDEPLOY_SENDER = Address(
        0x8646861A7CF453DDD086874D622B0696DE5B9674
    )
    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE

    SYSTEM_CALL_GAS_LIMIT = 30_000_000
    EXCESS_RETURN_GAS_STIPEND = 2300

    MAX_AMOUNT = 2**64 - 1
