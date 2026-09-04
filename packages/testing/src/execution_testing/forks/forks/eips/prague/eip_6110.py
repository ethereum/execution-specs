"""
EIP-6110: Supply validator deposits on chain.

Provides validator deposits as a list of deposit operations added to the
Execution Layer block.

https://eips.ethereum.org/EIPS/eip-6110
"""

from functools import cached_property
from hashlib import sha256
from typing import ClassVar, List, Mapping, Self, Type

from execution_testing.base_types import (
    Address,
    BLSPublicKey,
    BLSSignature,
    Hash,
    HexNumber,
)

from ....base_fork import BaseFork, SystemCallPhase
from ....bytecode import load_contract_bytecode
from ....requests import SystemContractRequest

DEPOSIT_CONTRACT_ADDRESS = 0x00000000219AB540356CBB839CBE05303D7705FA
DEPOSIT_CONTRACT_BYTECODE = load_contract_bytecode(
    __name__, "deposit_contract.bin"
)


def _sha256(*args: bytes) -> bytes:
    """Return sha256 hash of the concatenated input."""
    return sha256(b"".join(args)).digest()


def create_deposit_log_bytes(
    pubkey_size: int = 48,
    pubkey_data: bytes = b"",
    pubkey_offset: int = 160,
    withdrawal_credentials_size: int = 32,
    withdrawal_credentials_data: bytes = b"",
    withdrawal_credentials_offset: int = 256,
    amount_size: int = 8,
    amount_data: bytes = b"",
    amount_offset: int = 320,
    signature_size: int = 96,
    signature_data: bytes = b"",
    signature_offset: int = 384,
    index_size: int = 8,
    index_data: bytes = b"",
    index_offset: int = 512,
) -> bytes:
    """Create the deposit log bytes."""
    result = bytearray(576)
    offset = 0

    def write_uint256(value: int) -> None:
        nonlocal offset
        result[offset : offset + 32] = value.to_bytes(32, byteorder="big")
        offset += 32

    def write_bytes(data: bytes, size: int) -> None:
        nonlocal offset
        padded = data.ljust(size, b"\x00")
        result[offset : offset + size] = padded
        offset += size

    write_uint256(pubkey_offset)
    write_uint256(withdrawal_credentials_offset)
    write_uint256(amount_offset)
    write_uint256(signature_offset)
    write_uint256(index_offset)

    write_uint256(pubkey_size)
    write_bytes(pubkey_data, 64)

    write_uint256(withdrawal_credentials_size)
    write_bytes(withdrawal_credentials_data, 32)

    write_uint256(amount_size)
    write_bytes(amount_data, 32)

    write_uint256(signature_size)
    write_bytes(signature_data, 96)

    write_uint256(index_size)
    write_bytes(index_data, 32)

    return bytes(result)


class DepositRequest(SystemContractRequest):
    """Deposit request (EIP-6110), read from the deposit contract's log."""

    pubkey: BLSPublicKey
    """The public key of the beacon chain validator."""
    withdrawal_credentials: Hash
    """The withdrawal credentials of the beacon chain validator."""
    amount: HexNumber
    """The amount in gwei of the deposit."""
    signature: BLSSignature
    """
    The signature of the deposit using the validator's private key that matches
    the `pubkey`.
    """
    index: HexNumber
    """The index of the deposit."""

    extra_wei: int = 0
    """
    Extra amount in wei to be sent with the deposit. If this value modulo 10**9
    is not zero, the deposit will be invalid. The value can be negative but if
    the total value is negative, an exception will be raised.
    """

    type: ClassVar[int] = 0
    system_contract_address: ClassVar[Address] = Address(
        DEPOSIT_CONTRACT_ADDRESS,
        label="DEPOSIT_CONTRACT_ADDRESS",
    )

    def __bytes__(self) -> bytes:
        """Return deposit's attributes as bytes."""
        return (
            bytes(self.pubkey)
            + bytes(self.withdrawal_credentials)
            + self.amount.to_bytes(8, "little")
            + bytes(self.signature)
            + self.index.to_bytes(8, "little")
        )

    @property
    def value(self) -> int:
        """
        Return the value of the deposit transaction, equal to the amount in
        gwei plus the extra amount in wei.
        """
        value = (self.amount * 10**9) + self.extra_wei
        if value < 0:
            raise ValueError("Value cannot be negative")
        return value

    @cached_property
    def deposit_data_root(self) -> Hash:
        """Return the deposit data root of the deposit."""
        pubkey_root = _sha256(self.pubkey, b"\x00" * 16)
        signature_root = _sha256(
            _sha256(self.signature[:64]),
            _sha256(self.signature[64:], b"\x00" * 32),
        )
        pubkey_withdrawal_root = _sha256(
            pubkey_root, self.withdrawal_credentials
        )
        amount_bytes = (self.amount).to_bytes(32, byteorder="little")
        amount_signature_root = _sha256(amount_bytes, signature_root)
        return Hash(_sha256(pubkey_withdrawal_root, amount_signature_root))

    @property
    def calldata(self) -> bytes:
        """
        Return the calldata needed to call the beacon chain deposit contract
        and make the deposit.

        deposit(
          bytes calldata pubkey,
          bytes calldata withdrawal_credentials,
          bytes calldata signature,
          bytes32 deposit_data_root
        )
        """
        offset_length = 32
        pubkey_offset = offset_length * 3 + len(self.deposit_data_root)
        withdrawal_offset = pubkey_offset + offset_length + len(self.pubkey)
        signature_offset = (
            withdrawal_offset
            + offset_length
            + len(self.withdrawal_credentials)
        )
        return self.calldata_modifier(
            b"\x22\x89\x51\x18"
            + pubkey_offset.to_bytes(offset_length, byteorder="big")
            + withdrawal_offset.to_bytes(offset_length, byteorder="big")
            + signature_offset.to_bytes(offset_length, byteorder="big")
            + self.deposit_data_root
            + len(self.pubkey).to_bytes(offset_length, byteorder="big")
            + self.pubkey
            + len(self.withdrawal_credentials).to_bytes(
                offset_length, byteorder="big"
            )
            + self.withdrawal_credentials
            + len(self.signature).to_bytes(offset_length, byteorder="big")
            + self.signature
        )

    def log(self, *, include_abi_encoding: bool = True) -> bytes:
        """
        Return the log data for the deposit event.

        event DepositEvent(
          bytes pubkey,
          bytes withdrawal_credentials,
          bytes amount,
          bytes signature,
          bytes index
        );
        """
        data = bytearray(576)
        if include_abi_encoding:
            # Insert ABI encoding
            data[30:32] = b"\x00\xa0"  # Offset: pubkey (160)
            data[62:64] = b"\x01\x00"  # Offset: withdrawal_credentials (256)
            data[94:96] = b"\x01\x40"  # Offset: amount (320)
            data[126:128] = b"\x01\x80"  # Offset: signature (384)
            data[158:160] = b"\x02\x00"  # Offset: index (512)
            data[190:192] = b"\x00\x30"  # Size: pubkey (48)
            data[286:288] = b"\x00\x20"  # Size: withdrawal_credentials (32)
            data[350:352] = b"\x00\x08"  # Size: amount (8)
            data[414:416] = b"\x00\x60"  # Size: signature (96)
            data[542:544] = b"\x00\x08"  # Size: index (8)
        offset = 192
        data[offset : offset + len(self.pubkey)] = self.pubkey  # [192:240]
        offset += 48 + len(self.pubkey)
        data[offset : offset + len(self.withdrawal_credentials)] = (
            self.withdrawal_credentials
        )  # [288:320]
        offset += 32 + len(self.withdrawal_credentials)
        data[offset : offset + 8] = (self.amount).to_bytes(
            8, byteorder="little"
        )  # [352:360]
        offset += 56 + 8
        data[offset : offset + len(self.signature)] = (
            self.signature
        )  # [416:512]
        offset += 32 + len(self.signature)
        data[offset : offset + 8] = (self.index).to_bytes(
            8, byteorder="little"
        )  # [544:552]
        return bytes(data)

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy."""
        del source_address
        return self.copy()

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a request from a sequential index."""
        return cls(
            pubkey=(index * 3),
            withdrawal_credentials=(index * 3) + 1,
            amount=1_000_000_000,
            signature=(index * 3) + 2,
            index=index,
        )


class EIP6110(BaseFork):
    """EIP-6110 class."""

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the beacon chain deposit contract."""
        return [DepositRequest.system_contract_address] + super(
            EIP6110, cls
        ).system_contracts()

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Never call the deposit contract; deposits are read from its logs."""
        return {
            DepositRequest.system_contract_address: SystemCallPhase.NONE,
            **super(EIP6110, cls).system_contract_call_phases(),
        }

    @classmethod
    def system_contract_request_types(
        cls,
    ) -> List[Type[SystemContractRequest]]:
        """Add the deposit request type."""
        return [DepositRequest] + super(
            EIP6110, cls
        ).system_contract_request_types()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the beacon chain deposit contract."""
        deposit_contract_tree_depth = 32
        storage = {}
        next_hash = sha256(b"\x00" * 64).digest()
        for i in range(
            deposit_contract_tree_depth + 2,
            deposit_contract_tree_depth * 2 + 1,
        ):
            storage[i] = next_hash
            next_hash = sha256(next_hash + next_hash).digest()

        return {
            DEPOSIT_CONTRACT_ADDRESS: {
                "nonce": 1,
                "code": DEPOSIT_CONTRACT_BYTECODE,
                "storage": storage,
            },
            **super(EIP6110, cls).pre_allocation_blockchain(),
        }
