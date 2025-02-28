"""
The module implements the raw EVM tracer for t8n.
"""
import json
import os
from contextlib import ExitStack
from dataclasses import asdict, dataclass, is_dataclass
from typing import (
    Any,
    List,
    Optional,
    Protocol,
    TextIO,
    Union,
    runtime_checkable,
)

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.trace import (
    EvmStop,
    GasAndRefund,
    OpEnd,
    OpException,
    OpStart,
    PrecompileEnd,
    PrecompileStart,
    TraceEvent,
    TransactionEnd,
    TransactionStart,
)

EXCLUDE_FROM_OUTPUT = ["gasCostTraced", "errorTraced", "precompile"]
OUTPUT_DIR = "."


@dataclass
class Trace:
    """
    The class implements the raw EVM trace.
    """

    pc: int
    op: Optional[Union[str, int]]
    gas: str
    gasCost: str
    memory: Optional[str]
    memSize: int
    stack: Optional[List[str]]
    returnData: Optional[str]
    depth: int
    refund: int
    opName: str
    gasCostTraced: bool = False
    errorTraced: bool = False
    precompile: bool = False
    error: Optional[str] = None


@dataclass
class FinalTrace:
    """
    The class implements final trace for a tx.
    """

    output: str
    gasUsed: str
    error: Optional[str] = None

    def __init__(
        self, gas_used: int, output: bytes, error: Optional[Exception]
    ) -> None:
        self.output = output.hex()
        self.gasUsed = hex(gas_used)
        if error:
            self.error = type(error).__name__


@runtime_checkable
class TransactionEnvironment(Protocol):
    """
    The class implements the tx_env interface for trace.
    """

    index_in_block: Optional[Uint]
    tx_hash: Optional[Bytes]
    traces: List[Union["Trace", "FinalTrace"]]


@runtime_checkable
class Message(Protocol):
    """
    The class implements the message interface for trace.
    """

    depth: int
    tx_env: TransactionEnvironment
    parent_evm: Optional["Evm"]


@runtime_checkable
class EvmWithoutReturnData(Protocol):
    """
    The class implements the EVM interface for pre-byzantium forks trace.
    """

    pc: Uint
    stack: List[U256]
    memory: bytearray
    code: Bytes
    gas_left: Uint
    refund_counter: int
    running: bool
    message: Message


@runtime_checkable
class EvmWithReturnData(Protocol):
    """
    The class implements the EVM interface for post-byzantium forks trace.
    """

    pc: Uint
    stack: List[U256]
    memory: bytearray
    code: Bytes
    gas_left: Uint
    refund_counter: int
    running: bool
    message: Message
    return_data: Bytes


Evm = Union[EvmWithoutReturnData, EvmWithReturnData]


def evm_trace(
    evm: Any,
    event: TraceEvent,
    trace_memory: bool = False,
    trace_stack: bool = True,
    trace_return_data: bool = False,
) -> None:
    """
    Create a trace of the event.
    """
    # System Transaction do not have a tx_hash or index
    if (
        evm.message.tx_env.index_in_block is None
        or evm.message.tx_env.tx_hash is None
    ):
        return

    assert isinstance(evm, (EvmWithoutReturnData, EvmWithReturnData))

    traces = evm.message.tx_env.traces
    last_trace = None
    if traces:
        last_trace = traces[-1]

    refund_counter = evm.refund_counter
    parent_evm = evm.message.parent_evm
    while parent_evm is not None:
        refund_counter += parent_evm.refund_counter
        parent_evm = parent_evm.message.parent_evm

    len_memory = len(evm.memory)

    return_data = None
    if isinstance(evm, EvmWithReturnData) and trace_return_data:
        return_data = "0x" + evm.return_data.hex()

    memory = None
    if trace_memory and len_memory > 0:
        memory = "0x" + evm.memory.hex()

    stack = None
    if trace_stack:
        stack = [hex(i) for i in evm.stack]

    if isinstance(event, TransactionStart):
        pass
    elif isinstance(event, TransactionEnd):
        final_trace = FinalTrace(event.gas_used, event.output, event.error)
        traces.append(final_trace)

        output_traces(
            traces,
            evm.message.tx_env.index_in_block,
            evm.message.tx_env.tx_hash,
        )
    elif isinstance(event, PrecompileStart):
        new_trace = Trace(
            pc=int(evm.pc),
            op="0x" + event.address.hex().lstrip("0"),
            gas=hex(evm.gas_left),
            gasCost="0x0",
            memory=memory,
            memSize=len_memory,
            stack=stack,
            returnData=return_data,
            depth=int(evm.message.depth) + 1,
            refund=refund_counter,
            opName="0x" + event.address.hex().lstrip("0"),
            precompile=True,
        )

        traces.append(new_trace)
    elif isinstance(event, PrecompileEnd):
        assert isinstance(last_trace, Trace)

        last_trace.gasCostTraced = True
        last_trace.errorTraced = True
    elif isinstance(event, OpStart):
        op = event.op.value
        if op == "InvalidOpcode":
            op = "Invalid"
        new_trace = Trace(
            pc=int(evm.pc),
            op=op,
            gas=hex(evm.gas_left),
            gasCost="0x0",
            memory=memory,
            memSize=len_memory,
            stack=stack,
            returnData=return_data,
            depth=int(evm.message.depth) + 1,
            refund=refund_counter,
            opName=str(event.op).split(".")[-1],
        )

        traces.append(new_trace)
    elif isinstance(event, OpEnd):
        assert isinstance(last_trace, Trace)

        last_trace.gasCostTraced = True
        last_trace.errorTraced = True
    elif isinstance(event, OpException):
        if last_trace is not None:
            assert isinstance(last_trace, Trace)
        if (
            # The first opcode in the code is an InvalidOpcode.
            # So we add a new trace with InvalidOpcode as op.
            not last_trace
            # The current opcode is an InvalidOpcode. This condition
            # is true if an InvalidOpcode is found in any location
            # other than the first opcode.
            or last_trace.errorTraced
            # The first opcode in a child message is an InvalidOpcode.
            # This case has to be explicitly handled since the first
            # two conditions do not cover it.
            or last_trace.depth == evm.message.depth
        ):
            if not hasattr(event.error, "code"):
                name = event.error.__class__.__name__
                raise TypeError(
                    f"OpException event error type `{name}` does not have code"
                ) from event.error

            new_trace = Trace(
                pc=int(evm.pc),
                op=event.error.code,
                gas=hex(evm.gas_left),
                gasCost="0x0",
                memory=memory,
                memSize=len_memory,
                stack=stack,
                returnData=return_data,
                depth=int(evm.message.depth) + 1,
                refund=refund_counter,
                opName="InvalidOpcode",
                gasCostTraced=True,
                errorTraced=True,
                error=type(event.error).__name__,
            )

            traces.append(new_trace)
        elif not last_trace.errorTraced:
            # If the error for the last trace is not covered
            # the exception is attributed to the last trace.
            last_trace.error = type(event.error).__name__
            last_trace.errorTraced = True
    elif isinstance(event, EvmStop):
        if not evm.running:
            return
        elif len(evm.code) == 0:
            return
        else:
            evm_trace(
                evm,
                OpStart(event.op),
                trace_memory,
                trace_stack,
                trace_return_data,
            )
    elif isinstance(event, GasAndRefund):
        if len(traces) == 0:
            # In contract creation transactions, there may not be any traces
            return

        assert isinstance(last_trace, Trace)

        if not last_trace.gasCostTraced:
            last_trace.gasCost = hex(event.gas_cost)
            last_trace.refund = refund_counter
            last_trace.gasCostTraced = True


class _TraceJsonEncoder(json.JSONEncoder):
    @staticmethod
    def retain(k: str, v: Optional[object]) -> bool:
        if v is None:
            return False

        if k in EXCLUDE_FROM_OUTPUT:
            return False

        if k in ("pc", "gas", "gasCost", "refund"):
            if isinstance(v, str) and int(v, 0).bit_length() > 64:
                return False

        return True

    def default(self, obj: object) -> object:
        if not is_dataclass(obj) or isinstance(obj, type):
            return super().default(obj)

        trace = {
            k: v
            for k, v in asdict(obj).items()
            if _TraceJsonEncoder.retain(k, v)
        }

        return trace


def output_op_trace(
    trace: Union[Trace, FinalTrace], json_file: TextIO
) -> None:
    """
    Output a single trace to a json file.
    """
    json.dump(trace, json_file, separators=(",", ":"), cls=_TraceJsonEncoder)
    json_file.write("\n")


def output_traces(
    traces: List[Union[Trace, FinalTrace]],
    index_in_block: int,
    tx_hash: bytes,
) -> None:
    """
    Output the traces to a json file.
    """
    with ExitStack() as stack:
        json_file: TextIO

        if isinstance(OUTPUT_DIR, str):
            tx_hash_str = "0x" + tx_hash.hex()
            output_path = os.path.join(
                OUTPUT_DIR, f"trace-{index_in_block}-{tx_hash_str}.jsonl"
            )
            json_file = open(output_path, "w")
            stack.push(json_file)
        else:
            json_file = OUTPUT_DIR

        for trace in traces:
            if getattr(trace, "precompile", False):
                # Traces related to pre-compile are not output.
                continue
            output_op_trace(trace, json_file)
