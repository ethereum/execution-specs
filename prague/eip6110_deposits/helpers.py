"""
Helpers for the EIP-6110 deposit tests.
"""
from dataclasses import dataclass, field
from functools import cached_property
from hashlib import sha256 as sha256_hashlib
from typing import Callable, ClassVar, List

from ethereum_test_tools import EOA, Address, Alloc, Bytecode
from ethereum_test_tools import DepositRequest as DepositRequestBase
from ethereum_test_tools import Hash
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import Transaction

from .spec import Spec


def sha256(*args: bytes) -> bytes:
    """
    Returns the sha256 hash of the input.
    """
    return sha256_hashlib(b"".join(args)).digest()


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

    interaction_contract_address: ClassVar[Address] = Address(Spec.DEPOSIT_CONTRACT_ADDRESS)

    @cached_property
    def value(self) -> int:
        """
        Returns the value of the deposit transaction.
        """
        return self.amount * 10**9

    @cached_property
    def deposit_data_root(self) -> Hash:
        """
        Returns the deposit data root of the deposit.
        """
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
        Returns the calldata needed to call the beacon chain deposit contract and make the deposit.

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

    def with_source_address(self, source_address: Address) -> "DepositRequest":
        """
        Return a copy.
        """
        return self.copy()


@dataclass(kw_only=True)
class DepositInteractionBase:
    """
    Base class for all types of deposit transactions we want to test.
    """

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
                value=0,
                data=b"".join(r.calldata for r in self.requests),
                sender=self.sender_account,
            )
        ]

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        self.sender_account = pre.fund_eoa(self.sender_balance)
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
