"""Defines EIP-5920 specification constants and reference spec."""

from dataclasses import dataclass

from execution_testing import Address, Bytes, Hash, TransactionLog, keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_5920 = ReferenceSpec(
    "EIPS/eip-5920.md", "f8c6f353cb4690043c096995ea1877bf763fb987"
)


class Spec:
    """
    Parameters from the EIP-5920 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-5920.
    """

    MAX_ADDRESS = 2**160 - 1
    INVALID_ADDRESS_MIN = 2**160
    SYSTEM_ADDRESS: Address = Address(
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    )
    TRANSFER_TOPIC: Hash = Hash(
        keccak256(b"Transfer(address,address,uint256)")
    )


def transfer_log(
    sender: Address, recipient: Address, amount: int
) -> TransactionLog:
    """Create an expected EIP-7708 Transfer log for a value-bearing PAY."""
    return TransactionLog(
        address=Spec.SYSTEM_ADDRESS,
        topics=[
            Spec.TRANSFER_TOPIC,
            Hash(bytes(sender).rjust(32, b"\x00")),
            Hash(bytes(recipient).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )
