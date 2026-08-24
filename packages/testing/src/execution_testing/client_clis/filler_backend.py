"""
Backend protocol used by ``BlockchainTest`` to fill block data.

``FillerBackend`` abstracts the "thing that fills a block" so fill's spec
loop (``BlockchainTest.generate_block_data``) can dispatch to either:

- a classical ``TransitionTool`` (t8n CLI/server — deterministic compute
  path, the historical default), or
- a live EL client (``ClientBackend`` — drives ``testing_buildBlockV1`` to
  produce stateful fixtures against a warm datadir snapshot).

The two concrete backends cover distinct territory — t8n is a state-
transition function, a client is a stateful chain — but both return the
same ``TransitionToolOutput`` shape so they are interchangeable from
fill's perspective.

``TransitionTool`` itself structurally satisfies this protocol, so existing
callers continue to work unchanged.
"""

from typing import ClassVar, List, Protocol, runtime_checkable

from execution_testing.exceptions import ExceptionMapper

from .cli_types import Traces
from .transition_tool import TransitionTool, TransitionToolOutput


@runtime_checkable
class FillerBackend(Protocol):
    """
    Minimal interface required by ``BlockchainTest.generate_block_data``.

    Implementations:
    - ``TransitionTool`` (classical t8n path) — fill's default.
    - ``ClientBackend`` — drives ``testing_buildBlockV1`` against a live EL
      client to produce stateful fixtures without t8n.
    """

    exception_mapper: ExceptionMapper
    """
    Maps backend-specific errors to EEST transaction/block exceptions.
    ``exception_mapper.reliable`` indicates whether the mapping is trusted
    for test assertions (t8n: True; live-client: typically False).
    """

    attests_block_access_list_hash: ClassVar[bool]
    """
    Whether ``Result.block_access_list_hash`` is computed by the backend
    rather than derived by EEST from the BAL body the backend returned
    (t8n: True; live-client: False, since an engine ``ExecutionPayload``
    carries the body but no hash).
    """

    def evaluate(
        self,
        *,
        transition_tool_data: "TransitionTool.TransitionToolData",
        slow_request: bool = False,
    ) -> TransitionToolOutput:
        """Build a block and return the result."""
        ...

    def get_traces(self) -> List[Traces] | None:
        """Return per-transaction traces if available, ``None`` otherwise."""
        ...
