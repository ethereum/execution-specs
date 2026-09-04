"""Defines EIP-6110 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_6110 = ReferenceSpec(
    "EIPS/eip-6110.md", "cbe8bf6a28fa1d096f9756af3513675849c4158e"
)


class Spec:
    """
    Parameters from the EIP-6110 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-6110.
    """

    DEPOSIT_EVENT_SIGNATURE_HASH = (
        0x649BBC62D0E31342AFEA4E5CD82D4049E7E1EE912FC0889AA790803BE39038C5
    )
    MIN_DEPOSIT_AMOUNT = 1_000_000_000
    MIN_DEPOSIT_VALUE = MIN_DEPOSIT_AMOUNT * 10**9
    MAX_DEPOSIT_REQUESTS_PER_PAYLOAD = 8192
    """
    Maximum deposit requests a consensus layer payload can carry:
    https://github.com/ethereum/consensus-specs/blob/721cc37193d0321fef6519119c9dc9d34a79dd57/presets/mainnet/electra.yaml#L36
    """
