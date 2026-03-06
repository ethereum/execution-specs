"""Defines EIP-8037 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8037 = ReferenceSpec(
    "EIPS/eip-8037.md", "e8ad70217a9853a16e1d78aeb37dd738e6ef3694"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8037 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8037.
    """

    COST_PER_STATE_BYTE = 1_174
    CREATE_REGULAR = 9_000
    CREATE_STATE = 112 * COST_PER_STATE_BYTE
    PER_AUTH_BASE_REGULAR = 7_500
    PER_AUTH_BASE_STATE = 23 * COST_PER_STATE_BYTE
    PER_EMPTY_ACCOUNT_STATE = 112 * COST_PER_STATE_BYTE
    TOTAL_AUTH_STATE = PER_AUTH_BASE_STATE + PER_EMPTY_ACCOUNT_STATE
    CODE_DEPOSIT_REGULAR_PER_WORD = 6
    CODE_DEPOSIT_STATE_PER_BYTE = COST_PER_STATE_BYTE
