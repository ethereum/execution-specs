"""Helpers for the EIP-6110 deposit tests."""

from functools import cached_property
from hashlib import sha256 as sha256_hashlib
from typing import ClassVar, Dict, Self, Tuple

from execution_testing import (
    Address,
    Bytecode,
    Fork,
    Hash,
    Op,
    Opcode,
    SystemContractRequest,
)
from execution_testing import DepositRequest as DepositRequestBase

from .spec import Spec


def sha256(*args: bytes) -> bytes:
    """Return sha256 hash of the input."""
    return sha256_hashlib(b"".join(args)).digest()


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


class DepositRequest(DepositRequestBase, SystemContractRequest):
    """Deposit request descriptor."""

    extra_wei: int = 0
    """
    Extra amount in wei to be sent with the deposit. If this value modulo 10**9
    is not zero, the deposit will be invalid. The value can be negative but if
    the total value is negative, an exception will be raised.
    """

    interaction_contract_address: ClassVar[Address] = Address(
        Spec.DEPOSIT_CONTRACT_ADDRESS
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
        pubkey_root = sha256(self.pubkey, b"\x00" * 16)
        signature_root = sha256(
            sha256(self.signature[:64]),
            sha256(self.signature[64:], b"\x00" * 32),
        )
        pubkey_withdrawal_root = sha256(
            pubkey_root, self.withdrawal_credentials
        )
        amount_bytes = (self.amount).to_bytes(32, byteorder="little")
        amount_signature_root = sha256(amount_bytes, signature_root)
        return Hash(sha256(pubkey_withdrawal_root, amount_signature_root))

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

    def with_source_address(self, source_address: Address) -> "DepositRequest":
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


# The deposit contract is a compiled predeploy, so the gas it charges cannot
# be read off its source. The tables below are the opcodes it executes for one
# deposit, counted from an EVM trace, so that the fork's own gas schedule
# prices them and the estimate follows repricings. Regenerate them by filling
# `test_deposit_high_count` with `--traces --evm-dump-dir <dir>` and counting
# the `opName` of the depth-2 steps of one call frame.

_DEPOSIT_CALL_OPCODES: Dict[Opcode, int] = {
    Op.PUSH1: 270,
    Op.ADD: 177,
    Op.SWAP1: 175,
    Op.POP: 164,
    Op.DUP2: 142,
    Op.PUSH2: 123,
    Op.DUP1: 117,
    Op.SWAP2: 110,
    Op.JUMPDEST: 104,
    Op.MLOAD: 104,
    Op.DUP3: 97,
    Op.DUP4: 91,
    Op.JUMPI: 86,
    Op.MSTORE: 66,
    Op.SWAP3: 61,
    Op.LT: 54,
    Op.ISZERO: 46,
    Op.AND: 43,
    Op.SUB: 40,
    Op.DUP5: 37,
    Op.BYTE: 32,
    Op.NOT: 28,
    Op.JUMP: 27,
    Op.PUSH32: 27,
    Op.SWAP4: 26,
    Op.SHL: 19,
    Op.GT: 18,
    Op.DUP6: 17,
    Op.MSTORE8: 16,
    Op.PUSH31: 16,
    Op.SWAP5: 13,
    Op.OR: 11,
    Op.DUP10: 10,
    Op.CALLDATALOAD: 8,
    Op.DUP7: 8,
    Op.EQ: 7,
    Op.GAS: 7,
    Op.RETURNDATASIZE: 7,
    Op.DUP13: 6,
    Op.PUSH5: 6,
    Op.DUP11: 5,
    Op.DUP9: 5,
    Op.PUSH4: 5,
    Op.CALLDATASIZE: 4,
    Op.PUSH8: 4,
    Op.CALLVALUE: 3,
    Op.DUP15: 3,
    Op.MUL: 3,
    Op.DUP16: 2,
    Op.DUP8: 2,
    Op.SWAP6: 2,
    Op.DIV: 1,
    Op.DUP12: 1,
    Op.DUP14: 1,
    Op.MOD: 1,
    Op.SHR: 1,
    Op.STOP: 1,
    Op.SWAP14: 1,
}
"""
Fixed-cost opcodes a deposit call executes, excluding the Merkle branch loop
(`_BRANCH_UPDATE_OPCODES`) and the opcodes whose cost depends on their
operands, which are added with the metadata seen in the trace.
"""

_BRANCH_UPDATE_OPCODES: Dict[Opcode, int] = {
    Op.PUSH1: 26,
    Op.ADD: 14,
    Op.PUSH2: 12,
    Op.POP: 12,
    Op.MLOAD: 11,
    Op.DUP2: 10,
    Op.SWAP2: 10,
    Op.DUP1: 9,
    Op.JUMPDEST: 9,
    Op.JUMPI: 8,
    Op.SWAP1: 8,
    Op.DUP3: 8,
    Op.DUP4: 8,
    Op.MSTORE: 6,
    Op.LT: 6,
    Op.SWAP3: 6,
    Op.ISZERO: 5,
    Op.SUB: 4,
    Op.JUMP: 3,
    Op.AND: 3,
    Op.PUSH32: 3,
    Op.DUP5: 2,
    Op.SWAP4: 2,
    Op.EQ: 1,
    Op.OR: 1,
    Op.DIV: 1,
    Op.NOT: 1,
    Op.DUP6: 1,
    Op.SWAP5: 1,
    Op.GAS: 1,
    Op.RETURNDATASIZE: 1,
}
"""
Fixed-cost opcodes added by one iteration of the deposit contract's Merkle
branch loop, which hashes a sibling node into the accumulated deposit root.
"""

_DEPOSIT_CALL_CALLDATACOPY_SIZES: Tuple[int, ...] = (
    8,
    8,
    48,
    32,
    96,
    48,
    64,
    32,
    32,
)
"""Bytes copied by each `CALLDATACOPY` of a deposit call."""

_DEPOSIT_CALL_EXP_COUNT = 10
"""`EXP` operations of a deposit call, all with a single-byte exponent."""

_DEPOSIT_CALL_SLOAD_COUNT = 3
"""Storage slots a deposit call reads, all warm after the first deposit."""

_DEPOSIT_CALL_SSTORE_COUNT = 2
"""Storage slots a deposit call writes: the deposit count and a branch node."""

_DEPOSIT_CALL_SHA256_COUNT = 7
"""`sha256` calls a deposit call makes outside the Merkle branch loop."""

_SHA256_INPUT_WORDS = 2
"""Words of input of every `sha256` call the deposit contract makes."""

_DEPOSIT_LOG_DATA_SIZE = 576
"""Bytes of log data the deposit event carries."""

_DEPOSIT_CALL_MEMORY_SIZE = 1024
"""Bytes of memory a deposit call expands to."""

_BRANCH_UPDATE_MEMORY_SIZE = 1120
"""Bytes of memory a deposit call expands to for each branch loop iteration."""

_DIRTIED_SSTORE = Op.SSTORE.with_metadata(
    key_warm=True, original_value=1, current_value=2, new_value=3
)
"""
An `SSTORE` to a slot already written earlier in the same transaction, which
is what every deposit but the first of a transaction pays.
"""


def _counted(opcode_counts: Dict[Opcode, int]) -> Bytecode:
    """Return the opcodes of a count table concatenated into one bytecode."""
    code = Bytecode()
    for opcode, count in opcode_counts.items():
        code += opcode * count
    return code


def _sha256_call(fork: Fork) -> Bytecode:
    """
    Return the `STATICCALL` the deposit contract makes to the `sha256`
    precompile, charged with the precompile's own gas.
    """
    gas_costs = fork.gas_costs()
    return Op.STATICCALL.with_metadata(
        address_warm=True,
        inner_call_cost=(
            gas_costs.PRECOMPILE_SHA256_BASE
            + gas_costs.PRECOMPILE_SHA256_PER_WORD * _SHA256_INPUT_WORDS
        ),
    )


def deposit_contract_execution_gas(fork: Fork, *, branch_updates: int) -> int:
    """
    Return the gas the deposit contract consumes to process one deposit.

    `branch_updates` is the number of Merkle branch loop iterations to
    account for; the loop runs once per trailing zero bit of the new deposit
    count.
    """
    deposit_call = (
        _counted(_DEPOSIT_CALL_OPCODES)
        + Op.EXP.with_metadata(exponent=0xFF) * _DEPOSIT_CALL_EXP_COUNT
        + Op.SLOAD.with_metadata(key_warm=True) * _DEPOSIT_CALL_SLOAD_COUNT
        + _DIRTIED_SSTORE * _DEPOSIT_CALL_SSTORE_COUNT
        + Op.LOG1.with_metadata(data_size=_DEPOSIT_LOG_DATA_SIZE)
        + _sha256_call(fork) * _DEPOSIT_CALL_SHA256_COUNT
        + Op.MSTORE.with_metadata(new_memory_size=_DEPOSIT_CALL_MEMORY_SIZE)
    )
    for size in _DEPOSIT_CALL_CALLDATACOPY_SIZES:
        deposit_call += Op.CALLDATACOPY.with_metadata(data_size=size)
    branch_update = (
        _counted(_BRANCH_UPDATE_OPCODES)
        + Op.EXP.with_metadata(exponent=0xFF)
        + Op.SLOAD.with_metadata(key_warm=True)
        + _sha256_call(fork)
        + Op.MSTORE.with_metadata(
            old_memory_size=_DEPOSIT_CALL_MEMORY_SIZE,
            new_memory_size=_BRANCH_UPDATE_MEMORY_SIZE,
        )
    )
    return (deposit_call + branch_update * branch_updates).gas_cost(fork)
