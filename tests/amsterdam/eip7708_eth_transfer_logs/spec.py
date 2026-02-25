"""Defines EIP-7708 specification constants and functions."""

from dataclasses import dataclass

from execution_testing import Address, Bytes, Hash, TransactionLog, keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7708 = ReferenceSpec(
    "EIPS/eip-7708.md", "172188d7b090ed1afb876140f45e19ac00cba4bb"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7708 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7708.
    """

    SYSTEM_ADDRESS: Address = Address(
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    )
    TRANSFER_TOPIC: Hash = Hash(
        keccak256(b"Transfer(address,address,uint256)")
    )
    BURN_TOPIC: Hash = Hash(keccak256(b"Burn(address,uint256)"))


def transfer_log(
    sender: Address, recipient: Address, amount: int
) -> TransactionLog:
    """Create an expected Transfer log for EIP-7708."""
    return TransactionLog(
        address=Spec.SYSTEM_ADDRESS,
        topics=[
            Spec.TRANSFER_TOPIC,
            Hash(bytes(sender).rjust(32, b"\x00")),
            Hash(bytes(recipient).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )


def burn_log(contract_address: Address, amount: int) -> TransactionLog:
    """Create an expected Burn log for EIP-7708."""
    return TransactionLog(
        address=Spec.SYSTEM_ADDRESS,
        topics=[
            Spec.BURN_TOPIC,
            Hash(bytes(contract_address).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )
