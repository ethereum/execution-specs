"""Helpers for the EIP-6110 deposit tests."""

from dataclasses import dataclass, field
from functools import cached_property
from hashlib import sha256 as sha256_hashlib
from typing import Callable, ClassVar, List

from ethereum_test_tools import EOA, Address, Alloc, Bytecode, Hash, Transaction
from ethereum_test_tools import DepositRequest as DepositRequestBase
from ethereum_test_tools import Opcodes as Op

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

    def write_uint256(value: int):
        nonlocal offset
        result[offset : offset + 32] = value.to_bytes(32, byteorder="big")
        offset += 32

    def write_bytes(data: bytes, size: int):
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


class DepositRequest(DepositRequestBase):
    """Deposit request descriptor."""

    valid: bool = True
    """
    Whether the deposit request is valid or not.
    """
    gas_limit: int = 1_000_000
    """
    Gas limit for the call.
    """
    calldata_modifier: Callable[[bytes], bytes] = lambda x: x
    """
    Calldata modifier function.
    """
    extra_wei: int = 0
    """
    Extra amount in wei to be sent with the deposit.
    If this value modulo 10**9 is not zero, the deposit will be invalid.
    The value can be negative but if the total value is negative, an exception will be raised.
    """

    interaction_contract_address: ClassVar[Address] = Address(Spec.DEPOSIT_CONTRACT_ADDRESS)

    @cached_property
    def value(self) -> int:
        """
        Return the value of the deposit transaction, equal to the amount in gwei plus the
        extra amount in wei.
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
            sha256(self.signature[:64]), sha256(self.signature[64:], b"\x00" * 32)
        )
        pubkey_withdrawal_root = sha256(pubkey_root, self.withdrawal_credentials)
        amount_bytes = (self.amount).to_bytes(32, byteorder="little")
        amount_signature_root = sha256(amount_bytes, signature_root)
        return Hash(sha256(pubkey_withdrawal_root, amount_signature_root))

    @cached_property
    def calldata(self) -> bytes:
        """
        Return the calldata needed to call the beacon chain deposit contract and make the deposit.

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
        signature_offset = withdrawal_offset + offset_length + len(self.withdrawal_credentials)
        return self.calldata_modifier(
            b"\x22\x89\x51\x18"
            + pubkey_offset.to_bytes(offset_length, byteorder="big")
            + withdrawal_offset.to_bytes(offset_length, byteorder="big")
            + signature_offset.to_bytes(offset_length, byteorder="big")
            + self.deposit_data_root
            + len(self.pubkey).to_bytes(offset_length, byteorder="big")
            + self.pubkey
            + len(self.withdrawal_credentials).to_bytes(offset_length, byteorder="big")
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
        data[offset : offset + 8] = (self.amount).to_bytes(8, byteorder="little")  # [352:360]
        offset += 56 + 8
        data[offset : offset + len(self.signature)] = self.signature  # [416:512]
        offset += 32 + len(self.signature)
        data[offset : offset + 8] = (self.index).to_bytes(8, byteorder="little")  # [544:552]
        return bytes(data)

    def with_source_address(self, source_address: Address) -> "DepositRequest":
        """Return a copy."""
        return self.copy()


@dataclass(kw_only=True)
class DepositInteractionBase:
    """Base class for all types of deposit transactions we want to test."""

    sender_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the account that sends the transaction.
    """
    sender_account: EOA | None = None
    """
    Account that sends the transaction.
    """
    requests: List[DepositRequest]
    """
    Deposit request to be included in the block.
    """

    def transactions(self) -> List[Transaction]:
        """Return a transaction for the deposit request."""
        raise NotImplementedError

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        raise NotImplementedError

    def valid_requests(self, current_minimum_fee: int) -> List[DepositRequest]:
        """Return the list of deposit requests that should be included in the block."""
        raise NotImplementedError


@dataclass(kw_only=True)
class DepositTransaction(DepositInteractionBase):
    """Class used to describe a deposit originated from an externally owned account."""

    def transactions(self) -> List[Transaction]:
        """Return a transaction for the deposit request."""
        assert self.sender_account is not None, "Sender account not initialized"
        return [
            Transaction(
                gas_limit=request.gas_limit,
                gas_price=0x07,
                to=request.interaction_contract_address,
                value=request.value,
                data=request.calldata,
                sender=self.sender_account,
            )
            for request in self.requests
        ]

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        self.sender_account = pre.fund_eoa(self.sender_balance)

    def valid_requests(self, current_minimum_fee: int) -> List[DepositRequest]:
        """Return the list of deposit requests that should be included in the block."""
        return [
            request
            for request in self.requests
            if request.valid and request.value >= current_minimum_fee
        ]


@dataclass(kw_only=True)
class DepositContract(DepositInteractionBase):
    """Class used to describe a deposit originated from a contract."""

    tx_gas_limit: int = 1_000_000
    """
    Gas limit for the transaction.
    """
    tx_value: int = 0
    """
    Value to send with the transaction.
    """

    contract_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the contract that sends the deposit requests.
    """
    contract_address: Address | None = None
    """
    Address of the contract that sends the deposit requests.
    """
    entry_address: Address | None = None
    """
    Address to send the transaction to.
    """

    call_type: Op = field(default_factory=lambda: Op.CALL)
    """
    Type of call to be made to the deposit contract.
    """
    call_depth: int = 2
    """
    Frame depth of the beacon chain deposit contract when it executes the deposit requests.
    """
    extra_code: Bytecode = field(default_factory=Bytecode)
    """
    Extra code to be included in the contract that sends the deposit requests.
    """

    @property
    def contract_code(self) -> Bytecode:
        """Contract code used by the relay contract."""
        code = Bytecode()
        current_offset = 0
        for r in self.requests:
            value_arg = [r.value] if self.call_type in (Op.CALL, Op.CALLCODE) else []
            code += Op.CALLDATACOPY(0, current_offset, len(r.calldata)) + Op.POP(
                self.call_type(
                    Op.GAS if r.gas_limit == -1 else r.gas_limit,
                    r.interaction_contract_address,
                    *value_arg,
                    0,
                    len(r.calldata),
                    0,
                    0,
                )
            )
            current_offset += len(r.calldata)
        return code + self.extra_code

    def transactions(self) -> List[Transaction]:
        """Return a transaction for the deposit request."""
        return [
            Transaction(
                gas_limit=self.tx_gas_limit,
                gas_price=0x07,
                to=self.entry_address,
                value=self.tx_value,
                data=b"".join(r.calldata for r in self.requests),
                sender=self.sender_account,
            )
        ]

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        required_balance = self.sender_balance
        if self.tx_value > 0:
            required_balance = max(required_balance, self.tx_value + self.tx_gas_limit * 7)
        self.sender_account = pre.fund_eoa(required_balance)
        self.contract_address = pre.deploy_contract(
            code=self.contract_code, balance=self.contract_balance
        )
        self.entry_address = self.contract_address
        if self.call_depth > 2:
            for _ in range(1, self.call_depth - 1):
                self.entry_address = pre.deploy_contract(
                    code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                    + Op.POP(
                        Op.CALL(
                            Op.GAS,
                            self.entry_address,
                            0,
                            0,
                            Op.CALLDATASIZE,
                            0,
                            0,
                        )
                    ),
                )

    def valid_requests(self, current_minimum_fee: int) -> List[DepositRequest]:
        """Return the list of deposit requests that should be included in the block."""
        return [d for d in self.requests if d.valid and d.value >= current_minimum_fee]
