"""Define constants for EIP-7997: Deterministic Factory Contract."""

from dataclasses import dataclass

from execution_testing import Address, Bytes


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7997 = ReferenceSpec(
    git_path="EIPS/eip-7997.md",
    version="192193facea01dfb8b87ad59d67e8385bf9304b1",
)


@dataclass(frozen=True)
class Spec:
    """Constants from EIP-7997."""

    FACTORY_ADDRESS: int = 0x4E59B44847B379578588920CA78FBF26C0B4956C
    FACTORY_BYTECODE: Bytes = Bytes(
        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0"
        "3601600081602082378035828234f58015156039578182fd"
        "5b8082525050506014600cf3"
    )
    SALT_SIZE: int = 32
    """The factory reads the salt from the first 32 bytes of calldata."""


@dataclass(frozen=True)
class KeylessDeployment:
    """
    Define the canonical keyless creation transaction.

    Its fixed signature determines the sender and factory address.
    Preserve its signed gas fields even when fork gas schedules change.

    See https://github.com/Arachnid/deterministic-deployment-proxy.
    """

    DEPLOYER_ADDRESS: Address = Address(
        0x3FAB184622DC19B6109349B94811493BF2A45362
    )
    GAS_PRICE: int = 100 * 10**9
    GAS_LIMIT: int = 100_000
    INITCODE: Bytes = Bytes(
        bytes.fromhex("604580600e600039806000f350fe")
        + bytes(Spec.FACTORY_BYTECODE)
    )
    V: int = 27
    R: int = 0x2222222222222222222222222222222222222222222222222222222222222222
    S: int = 0x2222222222222222222222222222222222222222222222222222222222222222
