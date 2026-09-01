"""
EVM trace implementation that counts how many times each opcode is executed.
"""

from collections import defaultdict

from ethereum.trace import EvmTracer, OpStart, TraceEvent


class CountTracer(EvmTracer):
    """
    EVM trace implementation that counts how many times each opcode is
    executed.

    Counts accumulate over every execution in the run, including system
    transactions; consumers create one tracer per t8n run.
    """

    active_traces: defaultdict[str, int]

    def __init__(self) -> None:
        self.active_traces = defaultdict(lambda: 0)

    def __call__(self, evm: object, event: TraceEvent) -> None:
        """
        Create a trace of the event.
        """
        del evm  # Counting needs only the event, not the EVM state.
        if not isinstance(event, OpStart):
            return

        self.active_traces[event.op.name] += 1

    def results(self) -> dict[str, int]:
        """
        Return and clear the current opcode counts.
        """
        results = self.active_traces
        self.active_traces = defaultdict(lambda: 0)
        return results
