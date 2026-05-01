"""Reference spec for [EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7997 = ReferenceSpec(
    git_path="EIPS/eip-7997.md",
    version="ec05b85e530a7ea97ea52a1f0312d88eb0eb1be2",
)


@dataclass(frozen=True)
class Spec:
    """Constants from EIP-7997."""

    FACTORY_ADDRESS: int = 0x12
    FACTORY_BYTECODE: bytes = bytes.fromhex(
        "60203610602f57"
        "60003560203603806020600037600034f5"
        "806026573d600060003e3d6000fd"
        "5b60005260206000f3"
        "5b60006000fd"
    )
