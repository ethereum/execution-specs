"""
EVM trace implementation that fans out to many concrete trace implementations.
"""

from typing import Final

from typing_extensions import override

from ethereum.trace import EvmTracer, TraceEvent


class GroupTracer(EvmTracer):
    """
    EVM trace implementation that fans out to many concrete trace
    implementations.
    """

    tracers: Final[set[EvmTracer]]

    def __init__(self) -> None:
        self.tracers = set()

    def add(self, tracer: EvmTracer) -> None:
        """
        Insert a new tracer.
        """
        self.tracers.add(tracer)

    @override
    def __call__(
        self,
        evm: object,
        event: TraceEvent,
    ) -> None:
        """
        Record a trace event.
        """
        for tracer in self.tracers:
            tracer(evm, event)
