"""Tests for collecting the EIP-3155 traces of the EELS t8n tool."""

from pathlib import Path
from typing import List

from execution_testing.base_types import Address, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.client_clis.cli_types import (
    TransactionTraces,
    TransitionToolOutput,
)
from execution_testing.client_clis.clis.execution_specs import (
    ExecutionSpecsTransitionTool,
)
from execution_testing.evm_tools.t8n.evm_trace.eip3155 import (
    Eip3155Tracer,
)
from execution_testing.forks import Cancun
from execution_testing.test_types import (
    EOA,
    Account,
    Alloc,
    Environment,
    Transaction,
    TransactionReceipt,
)
from execution_testing.vm import Op

SENDER_KEY = 0x1111111111111111111111111111111111111111111111111111111111111111
CONTRACT = Address(0x1000000000000000000000000000000000000001)
CODE = Op.SSTORE(0, 1) + Op.STOP


def _tx(nonce: int) -> Transaction:
    """Return a signed call to the contract."""
    return Transaction(
        nonce=nonce,
        gas_limit=100_000,
        to=CONTRACT,
        protected=False,
        secret_key=SENDER_KEY,
    ).with_signature_and_sender()


def _run(
    tool: ExecutionSpecsTransitionTool, txs: List[Transaction]
) -> TransitionToolOutput:
    """Run the transactions in a single Cancun block."""
    alloc = Alloc(
        {
            **Cancun.pre_allocation_blockchain(),
            EOA(key=SENDER_KEY): Account(balance=10**18),
            CONTRACT: Account(code=CODE),
        }
    )
    env = Environment(
        fee_recipient=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        gas_limit=10_000_000,
        number=1,
        timestamp=1000,
        prev_randao=0,
        base_fee_per_gas=7,
        excess_blob_gas=0,
        parent_beacon_block_root=0,
        block_hashes={0: Hash(0)},
    )
    tool.reset_traces()
    return tool.evaluate(
        transition_tool_data=TransitionTool.TransitionToolData(
            alloc=alloc,
            txs=txs,
            env=env,
            fork=Cancun,
            chain_id=1,
            reward=0,
            blob_schedule=Cancun.blob_schedule(),
        ),
    )


def test_traces_are_collected_without_dump_dir() -> None:
    """The traces are collected without writing any files."""
    tool = ExecutionSpecsTransitionTool(trace=True)

    output = _run(tool, [_tx(0)])

    traces = tool.get_traces()
    assert traces is not None and len(traces) == 1
    assert output.result.traces == traces[0]
    (tx_traces,) = traces[0].root
    assert [line.op_name for line in tx_traces.traces] == [
        "PUSH1",
        "PUSH1",
        "SSTORE",
        "STOP",
    ]
    assert tx_traces.gas_used is not None


def test_traces_are_written_to_dump_dir(tmp_path: Path) -> None:
    """The dump directory gets a trace file with the collected traces."""
    tool = ExecutionSpecsTransitionTool(trace=True)
    tool.debug_dump_dir = tmp_path

    _run(tool, [_tx(0)])

    (trace_file,) = tmp_path.rglob("trace-0-0x*.jsonl")
    traces = tool.get_traces()
    assert traces is not None
    assert TransactionTraces.from_file(trace_file) == traces[0].root[0]


def test_rejected_tx_does_not_drop_other_traces() -> None:
    """Accepted transactions keep their traces around a rejected one."""
    tool = ExecutionSpecsTransitionTool(trace=True)
    rejected = Transaction(
        nonce=9,
        gas_limit=100_000,
        to=CONTRACT,
        protected=False,
        secret_key=SENDER_KEY,
    ).with_signature_and_sender()

    output = _run(tool, [_tx(0), rejected, _tx(1)])

    assert [r.index for r in output.result.rejected_transactions] == [1]
    traces = tool.get_traces()
    assert traces is not None
    assert [len(tx.traces) for tx in traces[0].root] == [4, 4]


def test_tx_without_trace_writes_empty_file(tmp_path: Path) -> None:
    """
    A tx with a receipt but no trace gets an empty trace and an empty file
    in the dump directory, so `--verify-traces` loads the same shape.
    """
    tool = ExecutionSpecsTransitionTool(trace=True)
    tool.reset_traces()
    tracer = Eip3155Tracer(output_basedir=None)
    receipt = TransactionReceipt(transaction_hash=Hash(1))

    traces = tool.collect_in_memory_traces([receipt], tracer, tmp_path)

    assert traces.root == [TransactionTraces(traces=[])]
    trace_file = tmp_path / f"trace-0-{receipt.transaction_hash}.jsonl"
    assert trace_file.read_text() == ""
