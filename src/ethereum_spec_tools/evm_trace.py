"""
The module implements the raw EVM tracer for t8n.
"""
import json
import os
from dataclasses import dataclass, fields
from typing import Any, List, Optional

EXCLUDE_FROM_OUTPUT = ["gasCostTraced", "errorTraced", "precompile"]


@dataclass
class Trace:
    """
    The class implements the raw EVM trace.
    """

    pc: int
    op: str
    gas: str
    gasCost: str
    memSize: int
    stack: List[str]
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

    def __init__(self, gas_used: int, output: bytes, has_erred: bool) -> None:
        self.output = output.hex()
        self.gasUsed = hex(gas_used)
        if has_erred:
            self.error = ""


def capture_tx_start(env: Any) -> None:
    """
    Capture the state at the beginning of a transaction.
    """
    pass


def capture_tx_end(
    env: Any, gas_used: int, output: bytes, has_erred: bool
) -> None:
    """
    Capture the state at the end of a transaction.
    """
    final_trace = FinalTrace(gas_used, output, has_erred)
    env.traces.append(final_trace)


def capture_precompile_start(evm: Any, address: Any) -> None:
    """
    Create a new trace instance before precompile execution.
    """
    new_trace = Trace(
        pc=evm.pc,
        op="0x" + address.hex().lstrip("0"),
        gas=hex(evm.gas_left),
        gasCost="0x0",
        memSize=len(evm.memory),
        stack=[hex(i) for i in evm.stack],
        depth=evm.message.depth + 1,
        refund=evm.refund_counter,
        opName="0x" + address.hex().lstrip("0"),
        precompile=True,
    )

    evm.env.traces.append(new_trace)


def capture_precompile_end(evm: Any) -> None:
    """Capture the state at the end of a precompile execution."""
    last_trace = evm.env.traces[-1]

    last_trace.gasCostTraced = True
    last_trace.errorTraced = True


def capture_op_start(evm: Any, op: Any) -> None:
    """
    Create a new trace instance before opcode execution.
    """
    new_trace = Trace(
        pc=evm.pc,
        op=op.value,
        gas=hex(evm.gas_left),
        gasCost="0x0",
        memSize=len(evm.memory),
        stack=[hex(i) for i in evm.stack],
        depth=evm.message.depth + 1,
        refund=evm.refund_counter,
        opName=str(op).split(".")[-1],
    )

    evm.env.traces.append(new_trace)


def capture_op_end(evm: Any) -> None:
    """Capture the state at the end of an opcode execution."""
    last_trace = evm.env.traces[-1]

    last_trace.gasCostTraced = True
    last_trace.errorTraced = True


def capture_op_exception(evm: Any) -> None:
    """Capture the state in case of exceptions."""
    if any(evm.env.traces):
        last_trace = evm.env.traces[-1]
    if (
        not any(evm.env.traces)
        or last_trace.errorTraced
        or last_trace.depth == evm.message.depth
    ):
        new_trace = Trace(
            pc=evm.pc,
            op="InvalidOpcode",
            gas=hex(evm.gas_left),
            gasCost="0x0",
            memSize=len(evm.memory),
            stack=[hex(i) for i in evm.stack],
            depth=evm.message.depth + 1,
            refund=evm.refund_counter,
            opName="InvalidOpcode",
            gasCostTraced=True,
            errorTraced=True,
            error="",
        )

        evm.env.traces.append(new_trace)
    elif not last_trace.errorTraced:
        last_trace.error = ""
        last_trace.errorTraced = True


def output_op_trace(trace: Any, json_file: Any) -> None:
    """
    Output a single trace to a json file.
    """
    dict_trace = {
        field.name: getattr(trace, field.name)
        for field in fields(trace)
        if field.name not in EXCLUDE_FROM_OUTPUT
        and getattr(trace, field.name) is not None
    }

    json.dump(dict_trace, json_file, separators=(",", ":"))
    json_file.write("\n")


def output_traces(
    traces: Any, tx_hash: bytes, output_basedir: str = "."
) -> None:
    """
    Output the traces to a json file.
    """
    tx_hash_str = "0x" + tx_hash.hex()
    output_path = os.path.join(
        output_basedir, f"spec-trace-{tx_hash_str}.json"
    )
    with open(output_path, "w") as json_file:
        for trace in traces:

            if getattr(trace, "precompile", False):
                # Traces related to pre-compile are not output.
                continue
            output_op_trace(trace, json_file)


def capture_evm_stop(evm: Any, op: Any) -> None:
    """
    Capture the state at the end of an EVM execution.
    A stop opcode is captured.
    """
    if not evm.running:
        return
    elif len(evm.code) == 0:
        return
    else:
        capture_op_start(evm, op)


def capture_gas_and_refund(evm: Any, gas_cost: Any) -> None:
    """
    Capture the gas cost and refund during opcode execution.
    """
    if not any(evm.env.traces):
        # In contract creation transactions, there may not be any traces
        return
    else:
        last_trace = evm.env.traces[-1]

    if not last_trace.gasCostTraced:
        last_trace.gasCost = hex(gas_cost)
        last_trace.refund = evm.refund_counter
        last_trace.gasCostTraced = True
