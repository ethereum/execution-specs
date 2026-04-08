"""Reference spec for [EIP-7708: ETH transfers and burns emit a log.](https://eips.ethereum.org/EIPS/eip-7708)."""

from dataclasses import dataclass

from execution_testing import Address, Hash, keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification metadata."""

    git_path: str
    version: str


ref_spec_7708 = ReferenceSpec(
    git_path="EIPS/eip-7708.md",
    version="9a8e498de01a9c5a81e417bf564736bbbe92093e",
)


@dataclass(frozen=True)
class Spec:
    """Constants from EIP-7708."""

    SYSTEM_ADDRESS: Address = Address(
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    )

    TRANSFER_EVENT_TOPIC: Hash = keccak256(
        b"Transfer(address,address,uint256)"
    )
    BURN_EVENT_TOPIC: Hash = keccak256(b"Burn(address,uint256)")
