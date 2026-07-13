"""Benchmark target accounts of various kinds for creation and location.."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, Self

from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    Bytecode,
    Create2PreimageLayout,
    Hash,
    Op,
    SequentialAddressLayout,
    keccak256,
)
from execution_testing.forks import Osaka

DEFAULT_CODE_SIZE = Osaka.max_code_size()


class AccountMode(Enum):
    """Benchmark target account variant."""

    # Minimal contract: single STOP byte.
    EXISTING_CONTRACT_MINIMAL = auto()

    # Max-size contract: byte-identical across copies.
    EXISTING_CONTRACT_SAME_MAX = auto()

    # Max-size contract: ADDRESS-embedded, each copy unique.
    EXISTING_CONTRACT_DIFF_MAX = auto()

    # Max-size contract: exercises JUMPDEST analysis. The code is unique.
    EXISTING_CONTRACT_JUMPDEST = auto()

    # EOA with balance.
    EXISTING_EOA = auto()

    # Empty account
    NON_EXISTING_ACCOUNT = auto()


class ContractInitcode(Bytecode):
    """Initcode for target contract receiver."""

    @property
    def runtime_size(self) -> int:
        """Size in bytes of the deployed runtime."""
        raise NotImplementedError

    @property
    def execution_code(self) -> Bytecode:
        """Model of the code executed when the contract is called."""
        raise NotImplementedError


class MinimalContractInitcode(ContractInitcode):
    """Initcode whose deployed runtime is a single STOP opcode."""

    def __new__(cls) -> Self:
        """Assemble the initcode."""
        return super().__new__(cls, Op.RETURN(Op.PUSH1(0), Op.PUSH1(1)))

    @property
    def runtime_size(self) -> int:
        """Size in bytes of the deployed runtime."""
        return len(Op.STOP)

    @property
    def execution_code(self) -> Bytecode:
        """A single STOP halts the call immediately."""
        return Op.STOP


class StopJumpdestInitcode(ContractInitcode):
    """
    Initcode for a JUMPDEST-filled runtime contract starting with STOP.

    If `code_size` is not supplied, Osaka max code size will
    be used, resulting in:

        offset    size   contents
        ------    ----   --------------------------------
        0x0000       1   STOP                 <- a call halts here
        0x0001      11   00 padding           <- diff=True only
        0x000C      20   contract ADDRESS     <- diff=True only
        0x0020   24544   JUMPDEST             <- fills up to 0x6000

    *diff* embeds ADDRESS (bytes 12-31), making each copy unique.
    Without it, all copies are identical (JUMPDEST bytes 1-31)
    """

    code_size: int

    def __new__(
        cls, *, code_size: int = DEFAULT_CODE_SIZE, diff: bool = False
    ) -> Self:
        """Assemble the initcode."""
        # Each MCOPY doubles the JUMPDEST-filled span (the first copy is
        # MCOPY(32, 0, 32), since 1 << 5 = 32) until it covers code_size.
        code = Op.MSTORE(0, bytes(Op.JUMPDEST * 32))
        for size in (1 << s for s in range(5, (code_size - 1).bit_length())):
            code += Op.MCOPY(size, 0, size)

        if diff:
            # Embeds ADDRESS in the runtime to make each copy unique
            code += Op.MSTORE(0, Op.ADDRESS)
        else:
            # Without embedding, all copies are byte-identical;
            code += Op.MSTORE8(0, 0)
        code += Op.RETURN(0, code_size)
        instance = super().__new__(cls, code)
        instance.code_size = code_size
        return instance

    @property
    def runtime_size(self) -> int:
        """Size in bytes of the deployed runtime."""
        return self.code_size

    @property
    def execution_code(self) -> Bytecode:
        """The leading STOP halts the call immediately."""
        return Op.STOP


class JochemnetPredeployContractInitcode(ContractInitcode):
    """
    Initcode whose deployed runtime embeds its own contract ADDRESS.

        offset    size   contents
        ------    ----   --------------------------------
        0x0000       4   PUSH2 0x5FFF; JUMP   <- entry
        0x0004      28   JUMPDEST padding
        0x0020      12   JUMPDEST padding
        0x002C      20   contract ADDRESS     <- unique
        0x0040   24512   JUMPDEST             <- 0x5FFF lands here

    Embedded ADDRESS makes the runtime unique per contract; initcode and
    its CREATE2 hash are shared across all salts.
    """

    code_size: int

    def __new__(cls, *, code_size: int = DEFAULT_CODE_SIZE) -> Self:
        """Assemble the initcode."""
        # Each MCOPY doubles the JUMPDEST-filled span (the first copy is
        # MCOPY(32, 0, 32), since 1 << 5 = 32) until it covers code_size.
        code = Op.MSTORE(0, bytes(Op.JUMPDEST * 32))
        for size in (1 << s for s in range(5, (code_size - 1).bit_length())):
            code += Op.MCOPY(size, 0, size)

        # Runtime entry: JUMP to final JUMPDEST, then STOP.
        entry = Op.JUMP(code_size - 1)
        entry += Op.JUMPDEST * (32 - len(entry))  # Padding

        code += Op.MSTORE(0, bytes(entry))

        # Mask ADDRESS into a JUMPDEST template via OR:
        #                  bytes 0..12   bytes 12..32
        #                  -----------   ------------
        #     ADDRESS      00 .. 00      <20-byte address>
        #     addr_slot    5b .. 5b      00 .. 00
        #     OR result    5b .. 5b      <20-byte address>
        addr_slot = Op.JUMPDEST * 12 + Op.STOP * 20
        code += Op.MSTORE(0x20, Op.OR(Op.ADDRESS, bytes(addr_slot)))

        code += Op.RETURN(0, code_size)
        instance = super().__new__(cls, code)
        instance.code_size = code_size
        return instance

    @property
    def runtime_size(self) -> int:
        """Size in bytes of the deployed runtime."""
        return self.code_size

    @property
    def execution_code(self) -> Bytecode:
        """Jump to the final JUMPDEST, then halt."""
        # Entry jumps to the final JUMPDEST, then halts.
        return Op.JUMP(Op.PUSH2(self.code_size - 1)) + Op.JUMPDEST


class AddressSource(ABC):
    """
    Locates and iterates over target addresses.

    Provides a unified interface for layout initialization,
    reading the current target, and advancing to the next one.
    """

    @property
    @abstractmethod
    def setup(self) -> Bytecode:
        """Bytecode that initializes the in-memory address layout."""

    @property
    @abstractmethod
    def memory_size(self) -> int:
        """Bytes of memory occupied by the address layout."""

    @abstractmethod
    def address_op(self) -> Bytecode:
        """Bytecode that reads the current target address."""

    @abstractmethod
    def next_op(self) -> Bytecode:
        """Bytecode that advances to the next target address."""


class Create2AddressSource(AddressSource):
    """Targets derived from a CREATE2 factory deployment."""

    def __init__(self, *, init_code: bytes, index_op: Bytecode) -> None:
        """Build the CREATE2 preimage layout for *init_code*."""
        self._layout = Create2PreimageLayout(
            factory_address=DETERMINISTIC_FACTORY_ADDRESS,
            salt=index_op,
            init_code_hash=keccak256(init_code),
        )

    @property
    def setup(self) -> Bytecode:
        """Bytecode that initializes the in-memory address layout."""
        return self._layout

    @property
    def memory_size(self) -> int:
        """Bytes of memory occupied by the CREATE2 preimage layout."""
        return self._layout.offset + 96

    def address_op(self) -> Bytecode:
        """Bytecode that reads the current target address."""
        return self._layout.address_op()

    def next_op(self) -> Bytecode:
        """Bytecode that advances to the next target address."""
        return self._layout.increment_salt_op()


class SequentialAddressSource(AddressSource):
    """Targets at a contiguous address range starting from a base."""

    def __init__(self, *, base_addr: Hash, index_op: Bytecode) -> None:
        """Build a sequential layout starting at *base_addr*."""
        self._layout = SequentialAddressLayout(
            starting_address=Op.ADD(base_addr, index_op),
            increment=1,
        )

    @property
    def setup(self) -> Bytecode:
        """Bytecode that initializes the in-memory address layout."""
        return self._layout

    @property
    def memory_size(self) -> int:
        """Bytes of memory occupied by the sequential address layout."""
        return self._layout.offset + 32

    def address_op(self) -> Bytecode:
        """Bytecode that reads the current target address."""
        return self._layout.address_op()

    def next_op(self) -> Bytecode:
        """Bytecode that advances to the next target address."""
        return self._layout.increment_address_op()


@dataclass(frozen=True)
class AccountCreator:
    """Account creation and location helper with address iteration."""

    # Modes whose target is a CREATE2-deployed contract.
    contract_modes: ClassVar[frozenset[AccountMode]] = frozenset(
        {
            AccountMode.EXISTING_CONTRACT_MINIMAL,
            AccountMode.EXISTING_CONTRACT_SAME_MAX,
            AccountMode.EXISTING_CONTRACT_DIFF_MAX,
            AccountMode.EXISTING_CONTRACT_JUMPDEST,
        }
    )

    mode: AccountMode
    code_size: int = DEFAULT_CODE_SIZE

    def __post_init__(self) -> None:
        """Reject anything that is not a known `AccountMode`."""
        if not isinstance(self.mode, AccountMode):
            raise ValueError(f"unknown account mode: {self.mode!r}")

    @property
    def derives_address_via_create2(self) -> bool:
        """Whether the target address is derived via CREATE2."""
        return self.mode in self.contract_modes

    @property
    def contract_initcode(self) -> ContractInitcode:
        """Return the initcode generator that deploys this account."""
        match self.mode:
            case AccountMode.EXISTING_CONTRACT_MINIMAL:
                return MinimalContractInitcode()
            case AccountMode.EXISTING_CONTRACT_SAME_MAX:
                return StopJumpdestInitcode(
                    code_size=self.code_size, diff=False
                )
            case AccountMode.EXISTING_CONTRACT_DIFF_MAX:
                return StopJumpdestInitcode(
                    code_size=self.code_size, diff=True
                )
            case AccountMode.EXISTING_CONTRACT_JUMPDEST:
                return JochemnetPredeployContractInitcode(
                    code_size=self.code_size
                )
            case _:
                raise ValueError(f"{self.mode.name} is not a contract")

    @property
    def initcode(self) -> bytes:
        """Return the CREATE2 initcode that deploys this account."""
        return bytes(self.contract_initcode)

    @property
    def runtime_size(self) -> int:
        """Return the deployed runtime size in bytes."""
        return self.contract_initcode.runtime_size

    @property
    def has_execution_code(self) -> bool:
        """Whether a call into this account executes deployed code."""
        return self.mode in self.contract_modes

    @property
    def execution_code(self) -> Bytecode:
        """Return the code executed when this account is called."""
        return self.contract_initcode.execution_code

    def address_source(self, index_op: Bytecode) -> AddressSource:
        """Return the source that yields successive target addresses."""
        if self.derives_address_via_create2:
            return Create2AddressSource(
                init_code=self.initcode, index_op=index_op
            )
        match self.mode:
            case AccountMode.EXISTING_EOA:
                # Spamoor EOA creator starts created accounts at 0x1000.
                # https://github.com/CPerezz/spamoor/pull/12
                base_addr = Hash(0x1000)
            case AccountMode.NON_EXISTING_ACCOUNT:
                # An address range that is never funded.
                base_addr = keccak256(b"random")
            case _:
                raise ValueError(f"{self.mode.name} has no address source")
        return SequentialAddressSource(base_addr=base_addr, index_op=index_op)
