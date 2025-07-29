"""
The module implements the raw EVM tracer for t8n.
"""

import json
import os
from contextlib import ExitStack
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, List, Optional, TextIO, Union

from ethereum.exceptions import EthereumException
from ethereum.trace import (
    EvmStop,
    EvmTracer,
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

from .protocols import Evm, EvmWithReturnData, TransactionEnvironment

EXCLUDE_FROM_OUTPUT = ["gasCostTraced", "errorTraced", "precompile"]


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
        self, gas_used: int, output: bytes, error: Optional[EthereumException]
    ) -> None:
        self.output = output.hex()
        self.gasUsed = hex(gas_used)
        if error:
            self.error = type(error).__name__


class Eip3155Tracer(EvmTracer):
    """
    EVM trace implementation compatible with EIP-3155.
    """

    transaction_environment: TransactionEnvironment | None
    active_traces: list[Trace | FinalTrace]
    trace_memory: bool
    trace_stack: bool
    trace_return_data: bool
    output_basedir: str | TextIO

    def __init__(
        self,
        /,
        trace_memory: bool = False,
        trace_stack: bool = True,
        trace_return_data: bool = False,
        output_basedir: str | TextIO = ".",
    ):
        self.transaction_environment = None
        self.active_traces = []
        self.trace_memory = trace_memory
        self.trace_stack = trace_stack
        self.trace_return_data = trace_return_data
        self.output_basedir = output_basedir

    def __call__(self, evm: Any, event: TraceEvent) -> None:
        """
        Create a trace of the event.
        """
        # System Transaction do not have a tx_hash or index
        if (
            evm.message.tx_env.index_in_block is None
            or evm.message.tx_env.tx_hash is None
        ):
            return

        assert isinstance(evm, Evm)

        if self.transaction_environment is not evm.message.tx_env:
            self.active_traces = []
            self.transaction_environment = evm.message.tx_env

        last_trace = None
        if self.active_traces:
            last_trace = self.active_traces[-1]

        refund_counter = evm.refund_counter
        parent_evm = evm.message.parent_evm
        while parent_evm is not None:
            refund_counter += parent_evm.refund_counter
            parent_evm = parent_evm.message.parent_evm

        len_memory = len(evm.memory)

        return_data = None
        if isinstance(evm, EvmWithReturnData) and self.trace_return_data:
            return_data = "0x" + evm.return_data.hex()

        memory = None
        if self.trace_memory and len_memory > 0:
            memory = "0x" + evm.memory.hex()

        stack = None
        if self.trace_stack:
            stack = [hex(i) for i in evm.stack]

        if isinstance(event, TransactionStart):
            pass
        elif isinstance(event, TransactionEnd):
            final_trace = FinalTrace(event.gas_used, event.output, event.error)
            self.active_traces.append(final_trace)

            output_traces(
                self.active_traces,
                evm.message.tx_env.index_in_block,
                evm.message.tx_env.tx_hash,
                self.output_basedir,
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

            self.active_traces.append(new_trace)
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

            self.active_traces.append(new_trace)
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
                        f"OpException event error type `{name}` does not "
                        "have code"
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

                self.active_traces.append(new_trace)
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
                self(
                    evm,
                    OpStart(event.op),
                )
        elif isinstance(event, GasAndRefund):
            if len(self.active_traces) == 0:
                # In contract creation transactions, there may not be any
                # traces
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
    output_basedir: str | TextIO,
) -> None:
    """
    Output the traces to a json file.
    """
    with ExitStack() as stack:
        json_file: TextIO

        if isinstance(output_basedir, str):
            tx_hash_str = "0x" + tx_hash.hex()
            output_path = os.path.join(
                output_basedir, f"trace-{index_in_block}-{tx_hash_str}.jsonl"
            )
            json_file = open(output_path, "w")
            stack.push(json_file)
        else:
            json_file = output_basedir

        for trace in traces:
            if getattr(trace, "precompile", False):
                # Traces related to pre-compile are not output.
                continue
            output_op_trace(trace, json_file)
