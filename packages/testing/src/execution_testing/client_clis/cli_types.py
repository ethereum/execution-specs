"""Types used in the transition tool interactions."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Dict,
    Generic,
    List,
    NamedTuple,
    Self,
    TypeVar,
)

from pydantic import Field, PlainSerializer, PlainValidator

from execution_testing.base_types import (
    Bloom,
    Bytes,
    CamelModel,
    EthereumTestRootModel,
    Hash,
    HexNumber,
)
from execution_testing.base_types.composite_types import (
    ForkBlobSchedule,
)
from execution_testing.exceptions import (
    BlockException,
    ExceptionMapperValidator,
    ExceptionWithMessage,
    TransactionException,
    UndefinedException,
)
from execution_testing.logging import (
    get_logger,
)
from execution_testing.test_types import (
    Alloc,
    Environment,
    Transaction,
    TransactionReceipt,
)
from execution_testing.vm import Opcode, Opcodes

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
    hash: Hash | None = None


class TraceLine(CamelModel):
    """Single trace line contained in the traces output."""

    model_config = CamelModel.model_config | {"extra": "ignore"}

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
    return_data: str | None = None

    _DEFAULT_EXCLUDE: set[str] = {"gas", "gas_cost"}

    def compare(
        self,
        other: Self,
        exclude_fields: set[str] | None = None,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """
        Compare two trace lines field-by-field.

        Return (baseline_fields, current_fields) dicts containing only
        the fields that differ. Both dicts are empty when lines match.
        """
        if exclude_fields is None:
            exclude_fields = self._DEFAULT_EXCLUDE
        self_dict = self.model_dump(mode="json", exclude=exclude_fields)
        other_dict = other.model_dump(mode="json", exclude=exclude_fields)
        baseline_diff: dict[str, str] = {}
        current_diff: dict[str, str] = {}
        for k in self_dict:
            if self_dict[k] != other_dict[k]:
                baseline_diff[k] = str(self_dict[k])
                current_diff[k] = str(other_dict[k])
        return baseline_diff, current_diff

    def are_equivalent(
        self,
        other: Self,
        exclude_fields: set[str] | None = None,
    ) -> bool:
        """Return True if the only difference is in excluded fields."""
        baseline_diff, _ = self.compare(other, exclude_fields)
        if baseline_diff:
            logger.debug(
                f"Trace lines are not equivalent: "
                f"differing fields: {list(baseline_diff.keys())}."
            )
            return False
        return True


class TraceFieldDiff(NamedTuple):
    """
    A single diff entry from TransactionTraces.compare().

    line_index is None for structural diffs (trace_length, output,
    gas_used). Field dicts map field name to string value.
    """

    line_index: int | None
    baseline_fields: dict[str, str]
    current_fields: dict[str, str]


class TransactionTraces(CamelModel):
    """Traces of a single transaction."""

    model_config = CamelModel.model_config | {"extra": "ignore"}

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

    def compare(
        self,
        other: Self,
        exclude_fields: set[str] | None = None,
        enable_post_processing: bool = False,
    ) -> List[TraceFieldDiff]:
        """
        Compare traces and return per-line differing fields.

        Return a list of TraceFieldDiff entries. line_index is None for
        structural diffs (trace_length, output, gas_used). Field dicts
        map field name to string value.

        When exclude_fields is None, no fields are excluded. Pass an
        explicit set to skip fields (e.g. {"gas", "gas_cost"}).
        """
        line_exclude = exclude_fields or set()
        diffs: List[TraceFieldDiff] = []

        if len(self.traces) != len(other.traces):
            diffs.append(
                TraceFieldDiff(
                    None,
                    {"trace_length": str(len(self.traces))},
                    {"trace_length": str(len(other.traces))},
                )
            )
            return diffs

        if self.output != other.output:
            diffs.append(
                TraceFieldDiff(
                    None,
                    {"output": str(self.output)},
                    {"output": str(other.output)},
                )
            )

        if not enable_post_processing and self.gas_used != other.gas_used:
            diffs.append(
                TraceFieldDiff(
                    None,
                    {"gas_used": str(self.gas_used)},
                    {"gas_used": str(other.gas_used)},
                )
            )

        own_traces = self.traces.copy()
        other_traces = other.traces.copy()
        if enable_post_processing:
            TransactionTraces.remove_gas(own_traces)
            TransactionTraces.remove_gas(other_traces)

        for i, (b_line, c_line) in enumerate(
            zip(own_traces, other_traces, strict=False)
        ):
            baseline_diff, current_diff = b_line.compare(c_line, line_exclude)
            if baseline_diff:
                diffs.append(TraceFieldDiff(i, baseline_diff, current_diff))

        return diffs

    def are_equivalent(
        self, other: Self, enable_post_processing: bool
    ) -> bool:
        """Return True if the only difference is the gas counter."""
        diffs = self.compare(
            other,
            exclude_fields={"gas", "gas_cost"},
            enable_post_processing=enable_post_processing,
        )
        for diff in diffs:
            if diff.line_index is None:
                for field_name in diff.baseline_fields:
                    logger.debug(
                        f"Traces have different {field_name}: "
                        f"{diff.baseline_fields[field_name]} != "
                        f"{diff.current_fields[field_name]}."
                    )
            else:
                logger.debug(
                    f"Trace line {diff.line_index} is not equivalent."
                )
        return len(diffs) == 0

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
    "DIFFICULTY": "PREVRANDAO",
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
    block_access_list: Bytes | None = None
    block_access_list_hash: Hash | None = None
    block_exception: Annotated[
        BlockExceptionWithMessage | UndefinedException | None,
        ExceptionMapperValidator,
    ] = None
    traces: Traces | None = None
    opcode_count: OpcodeCount | None = None


TRaw = TypeVar("TRaw")


@dataclass(kw_only=True)
class LazyAlloc(Generic[TRaw]):
    """
    Allocation that is lazily loaded from the transition tool response.
    """

    raw: TRaw
    _state_root: Hash
    alloc: Alloc | None = None

    def validate(self) -> Alloc:
        """Validate the alloc."""
        raise NotImplementedError("validate method not implemented.")

    def get(self) -> Alloc:
        """Model validate the allocation and return it."""
        if self.alloc is None:
            self.alloc = self.validate()
        return self.alloc

    def state_root(self) -> Hash:
        """Return state root of the allocation."""
        return self._state_root


JSONDict = Dict[str, Any]


class LazyAllocJson(LazyAlloc[JSONDict]):
    """
    Lazy allocation backed by a JSON dict cache.

    Uses Alloc.model_validate on the dict.
    """

    def validate(self) -> Alloc:
        """Validate the alloc."""
        return Alloc.model_validate(self.raw)


class LazyAllocStr(LazyAlloc[str]):
    """
    Lazy allocation backed by a str cache.

    Uses Alloc.model_validate_json on the string.
    """

    def validate(self) -> Alloc:
        """Validate the alloc."""
        return Alloc.model_validate_json(self.raw)


@dataclass
class TransitionToolInput:
    """Transition tool input."""

    alloc: Alloc | LazyAlloc
    txs: List[Transaction]
    env: Environment
    blob_params: ForkBlobSchedule | None = None

    def to_files(
        self, directory_path: Path, **model_dump_config: Any
    ) -> Dict[str, str]:
        """
        Prepare the input in a directory path in the file system for
        consumption by the t8n tool.
        """
        if isinstance(self.alloc, Alloc):
            alloc_contents = self.alloc.model_dump_json(**model_dump_config)
        elif isinstance(self.alloc, LazyAllocStr):
            alloc_contents = self.alloc.raw
        else:
            raise Exception(f"Invalid alloc type: {type(self.alloc)}")

        env_contents = self.env.model_dump_json(**model_dump_config)
        txs_contents = (
            "["
            + ",".join(
                tx.model_dump_json(**model_dump_config) for tx in self.txs
            )
            + "]"
        )
        input_contents: Dict[str, str] = {
            "alloc": alloc_contents,
            "env": env_contents,
            "txs": txs_contents,
        }
        if self.blob_params is not None:
            input_contents["blobParams"] = self.blob_params.model_dump_json(
                **model_dump_config
            )

        input_paths: Dict[str, str] = {}
        for content_type, contents in input_contents.items():
            file_path = directory_path / f"{content_type}.json"
            file_path.write_text(contents)
            input_paths[content_type] = str(file_path)

        return input_paths

    def model_dump_json(self, **model_dump_config: Any) -> str:
        """Dump the model in string JSON format."""
        if isinstance(self.alloc, Alloc):
            alloc_contents = self.alloc.model_dump_json(**model_dump_config)
        elif isinstance(self.alloc, LazyAllocStr):
            alloc_contents = self.alloc.raw
        else:
            raise Exception(f"Invalid alloc type: {type(self.alloc)}")

        env_contents = self.env.model_dump_json(**model_dump_config)
        txs_contents = (
            "["
            + ",".join(
                tx.model_dump_json(**model_dump_config) for tx in self.txs
            )
            + "]"
        )
        input_contents: Dict[str, str] = {
            "alloc": alloc_contents,
            "env": env_contents,
            "txs": txs_contents,
        }
        if self.blob_params is not None:
            input_contents["blobParams"] = self.blob_params.model_dump_json(
                **model_dump_config
            )
        contents: List[str] = []
        for content_type, type_contents in input_contents.items():
            contents.append(f'"{content_type}": {type_contents}')
        return "{" + ",".join(contents) + "}"

    def model_dump(self, mode: str, **model_dump_config: Any) -> Any:
        """Return the validated model."""
        assert mode == "json", f"Mode {mode} not supported."
        if isinstance(self.alloc, Alloc):
            alloc_contents = self.alloc.model_dump(
                mode=mode, **model_dump_config
            )
        elif isinstance(self.alloc, LazyAllocJson):
            alloc_contents = self.alloc.raw
        else:
            raise Exception(f"Invalid alloc type: {type(self.alloc)}")

        env_contents = self.env.model_dump(mode=mode, **model_dump_config)
        txs_contents = [
            tx.model_dump(mode=mode, **model_dump_config) for tx in self.txs
        ]
        input_contents: Dict[str, Any] = {
            "alloc": alloc_contents,
            "env": env_contents,
            "txs": txs_contents,
        }
        if self.blob_params is not None:
            input_contents["blobParams"] = self.blob_params.model_dump(
                mode=mode, **model_dump_config
            )

        return input_contents


@dataclass
class TransitionToolOutput:
    """Transition tool output."""

    alloc: LazyAlloc
    result: Result
    body: Bytes | None = None

    @classmethod
    def model_validate_files(
        cls, directory_path: Path, *, context: Any | None = None
    ) -> "Self":
        """
        Validate the model from the file system where each key is a
        different JSON file.
        """
        alloc_data = (directory_path / "alloc.json").read_text()
        result_data = (directory_path / "result.json").read_text()
        result = Result.model_validate_json(
            json_data=result_data, context=context
        )
        alloc = LazyAllocStr(raw=alloc_data, _state_root=result.state_root)
        output = cls(result=result, alloc=alloc)
        return output

    @classmethod
    def model_validate(
        cls, response_json: Dict, *, context: Any | None = None
    ) -> "Self":
        """
        Validate the model from the file system where each key is a
        different JSON file.
        """
        result = Result.model_validate(
            obj=response_json["result"], context=context
        )
        alloc = LazyAllocJson(
            raw=response_json["alloc"], _state_root=result.state_root
        )
        output = cls(result=result, alloc=alloc)
        return output

    @classmethod
    def model_validate_json(
        cls, response_json: str | bytes, *, context: Any | None = None
    ) -> "Self":
        """
        Validate the model from a JSON string.
        """
        # Manually parsing from a JSON string is tricky.
        # We parse using json.loads and then validate.
        parsed_json = json.loads(response_json)
        result = Result.model_validate(
            obj=parsed_json["result"], context=context
        )
        alloc = LazyAllocStr(
            raw=json.dumps(parsed_json["alloc"]), _state_root=result.state_root
        )
        output = cls(result=result, alloc=alloc)
        return output


class TransitionToolContext(CamelModel):
    """Transition tool context."""

    fork: str
    chain_id: int = Field(..., alias="chainid")
    reward: int


@dataclass(kw_only=True)
class TransitionToolRequest:
    """Transition tool server request data."""

    state: TransitionToolContext
    input: TransitionToolInput

    def model_dump(self, mode: str, **model_dump_config: Any) -> Any:
        """Return the validated model."""
        assert mode == "json", f"Mode {mode} not supported."
        return {
            "state": self.state.model_dump(mode=mode, **model_dump_config),
            "input": self.input.model_dump(mode=mode, **model_dump_config),
        }
