"""Types used in the transition tool interactions."""

import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Self

from pydantic import Field, PlainSerializer, PlainValidator

from ethereum_test_base_types import (
    Bloom,
    Bytes,
    CamelModel,
    EthereumTestRootModel,
    Hash,
    HexNumber,
)
from ethereum_test_base_types.composite_types import ForkBlobSchedule
from ethereum_test_exceptions import (
    BlockException,
    ExceptionMapperValidator,
    ExceptionWithMessage,
    TransactionException,
    UndefinedException,
)
from ethereum_test_types import (
    Alloc,
    BlockAccessList,
    Environment,
    Transaction,
    TransactionReceipt,
)
from ethereum_test_vm import Opcode, Opcodes
from pytest_plugins.custom_logging import get_logger

logger = get_logger(__name__)


class TransactionExceptionWithMessage(
    ExceptionWithMessage[TransactionException]
):
    """Transaction exception with message."""

    pass


class BlockExceptionWithMessage(ExceptionWithMessage[BlockException]):
    """Block exception with message."""

    pass


class RejectedTransaction(CamelModel):
    """Rejected transaction."""

    index: HexNumber
    error: Annotated[
        TransactionExceptionWithMessage | UndefinedException,
        ExceptionMapperValidator,
    ]


class TraceLine(CamelModel):
    """Single trace line contained in the traces output."""

    pc: int
    op: int
    gas: HexNumber
    gas_cost: HexNumber | None = None
    mem_size: int
    stack: List[HexNumber | None]
    depth: int
    refund: int
    op_name: str
    error: str | None = None

    def are_equivalent(self, other: Self) -> bool:
        """Return True if the only difference is the gas counter."""
        self_dict = self.model_dump(mode="python", exclude={"gas", "gas_cost"})
        other_dict = other.model_dump(
            mode="python", exclude={"gas", "gas_cost"}
        )
        if self_dict != other_dict:
            logger.debug(
                f"Trace lines are not equivalent: {self_dict} != {other_dict}."
            )
            return False
        return True


class TransactionTraces(CamelModel):
    """Traces of a single transaction."""

    traces: List[TraceLine]
    output: str | None = None
    gas_used: HexNumber | None = None

    @classmethod
    def from_file(cls, trace_file_path: Path) -> Self:
        """Read a single transaction's traces from a .jsonl file."""
        trace_lines = trace_file_path.read_text().splitlines()
        trace_dict: Dict[str, Any] = {}
        if "gasUsed" in trace_lines[-1] and "output" in trace_lines[-1]:
            trace_dict |= json.loads(trace_lines.pop())
        trace_dict["traces"] = [
            TraceLine.model_validate_json(line) for line in trace_lines
        ]
        return cls.model_validate(trace_dict)

    @staticmethod
    def remove_gas(traces: List[TraceLine]) -> None:
        """
        Remove the GAS operation opcode result from the stack to make
        comparison possible even if the gas has been pushed to the stack.
        """
        for i in range(1, len(traces)):
            trace = traces[i]
            previous_trace = traces[i - 1]
            if (
                previous_trace.op_name == "GAS"
                and trace.depth == previous_trace.depth
            ):
                # Remove the result of calling `Op.GAS` from the stack.
                trace.stack[-1] = None

    def are_equivalent(
        self, other: Self, enable_post_processing: bool
    ) -> bool:
        """Return True if the only difference is the gas counter."""
        if len(self.traces) != len(other.traces):
            logger.debug(
                f"Traces have different lengths: {len(self.traces)} != {len(other.traces)}."
            )
            return False
        if self.output != other.output:
            logger.debug(
                f"Traces have different outputs: {self.output} != {other.output}."
            )
            return False
        if self.gas_used != other.gas_used and not enable_post_processing:
            logger.debug(
                f"Traces have different gas used: {self.gas_used} != {other.gas_used}."
            )
            return False
        own_traces = self.traces.copy()
        other_traces = other.traces.copy()
        if enable_post_processing:
            logger.debug(
                "Removing gas from traces (enable_post_processing=True)."
            )
            TransactionTraces.remove_gas(own_traces)
            TransactionTraces.remove_gas(other_traces)
        for i in range(len(self.traces)):
            if not own_traces[i].are_equivalent(other_traces[i]):
                logger.debug(f"Trace line {i} is not equivalent.")
                return False
        return True

    def print(self) -> None:
        """Print the traces in a readable format."""
        for exec_step, trace in enumerate(self.traces):
            print(f"Step {exec_step}:")
            print(trace.model_dump_json(indent=2))
            print()


class Traces(EthereumTestRootModel):
    """
    Traces returned from the transition tool for all transactions executed.
    """

    root: List[TransactionTraces]

    def append(self, item: TransactionTraces) -> None:
        """Append the transaction traces to the current list."""
        self.root.append(item)

    def are_equivalent(
        self, other: Self | None, enable_post_processing: bool
    ) -> bool:
        """Return True if the only difference is the gas counter."""
        if other is None:
            return False
        if len(self.root) != len(other.root):
            return False
        for i in range(len(self.root)):
            if not self.root[i].are_equivalent(
                other.root[i], enable_post_processing
            ):
                logger.debug(f"Trace file {i} is not equivalent.")
                return False
            else:
                logger.debug(f"Trace file {i} is equivalent.")
        logger.debug("All traces are equivalent.")
        return True

    def print(self) -> None:
        """Print the traces in a readable format."""
        for tx_number, tx in enumerate(self.root):
            print(f"Transaction {tx_number}:")
            tx.print()


_opcode_synonyms = {
    "KECCAK256": "SHA3",
}


class UndefinedOpcode(HexNumber):
    """Undefined opcode."""

    pass


def validate_opcode(obj: Any) -> Opcodes | Opcode | UndefinedOpcode:
    """Validate an opcode from a string."""
    if isinstance(obj, (Opcode, Opcodes, UndefinedOpcode)):
        return obj
    if isinstance(obj, str):
        if obj.startswith("0x"):
            return UndefinedOpcode(obj)
        if obj in _opcode_synonyms:
            obj = _opcode_synonyms[obj]
        for op in Opcodes:
            if str(op) == obj:
                return op
    raise Exception(f"Unable to validate {obj} (type={type(obj)})")


class OpcodeCount(EthereumTestRootModel):
    """Opcode count returned from the evm tool."""

    root: Dict[
        Annotated[
            Opcodes | UndefinedOpcode,
            PlainValidator(validate_opcode),
            PlainSerializer(lambda o: str(o)),
        ],
        int,
    ]

    def __add__(self, other: Self) -> Self:
        """Add two instances of opcode count dictionaries."""
        assert isinstance(other, OpcodeCount), (
            f"Incompatible type {type(other)}"
        )
        new_dict = self.model_dump() | other.model_dump()
        for match_key in self.root.keys() & other.root.keys():
            new_dict[match_key] = self.root[match_key] + other.root[match_key]
        return self.__class__(new_dict)


class Result(CamelModel):
    """Result of a transition tool output."""

    state_root: Hash
    ommers_hash: Hash | None = Field(None, validation_alias="sha3Uncles")
    transactions_trie: Hash = Field(..., alias="txRoot")
    receipts_root: Hash
    logs_hash: Hash
    logs_bloom: Bloom
    receipts: List[TransactionReceipt]
    rejected_transactions: List[RejectedTransaction] = Field(
        default_factory=list, alias="rejected"
    )
    difficulty: HexNumber | None = Field(None, alias="currentDifficulty")
    gas_used: HexNumber
    base_fee_per_gas: HexNumber | None = Field(None, alias="currentBaseFee")
    withdrawals_root: Hash | None = None
    excess_blob_gas: HexNumber | None = Field(
        None, alias="currentExcessBlobGas"
    )
    blob_gas_used: HexNumber | None = None
    requests_hash: Hash | None = None
    requests: List[Bytes] | None = None
    block_access_list: BlockAccessList | None = None
    block_access_list_hash: Hash | None = None
    block_exception: Annotated[
        BlockExceptionWithMessage | UndefinedException | None,
        ExceptionMapperValidator,
    ] = None
    traces: Traces | None = None
    opcode_count: OpcodeCount | None = None


class TransitionToolInput(CamelModel):
    """Transition tool input."""

    alloc: Alloc
    txs: List[Transaction]
    env: Environment
    blob_params: ForkBlobSchedule | None = None


class TransitionToolOutput(CamelModel):
    """Transition tool output."""

    alloc: Alloc
    result: Result
    body: Bytes | None = None


class TransitionToolContext(CamelModel):
    """Transition tool context."""

    fork: str
    chain_id: int = Field(..., alias="chainid")
    reward: int


class TransitionToolRequest(CamelModel):
    """Transition tool server request data."""

    state: TransitionToolContext
    input: TransitionToolInput
