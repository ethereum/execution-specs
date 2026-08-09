"""
Answer an `eth_call` by running one message against a named state.

Every other JSON-RPC expectation the testing package derives is a
*projection*: the transition tool already computed the answer and the
projection reformats it. `eth_call` is the first that needs execution
which never happened on chain, so it needs a tool rather than a view.

That tool is this module, a sibling of `t8n` and driven the same way —
handed a testing `Alloc`, `Environment` and `Transaction`, returning an
in-memory result. Two things make it a sibling rather than an option on
`t8n`:

- **No block is produced.** `t8n`'s contract is "block in, post-state and
  result out", and `TransitionToolOutput` has no place for a single
  frame's return data. Widening it for one RPC method would put an RPC
  concern in the transition tool's output type.
- **No system contracts run.** A call names a block whose system calls
  already happened, so re-running them would execute them twice against
  a state that already contains their effects.

What is *not* reimplemented here is the state transition. The message
runs through the fork's own `process_transaction`, so the answer comes
from the specification rather than from a second copy of it, and the
return data is read from the `vm.TransactionResult` that function now
returns.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Optional

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, Uint

from ethereum import trace
from ethereum.exceptions import EthereumException

from ..loaders.fixture_loader import Load
from ..loaders.transaction_loader import load_testing_transaction
from ..t8n.block_environment import build_block_environment
from ..utils import resolve_fork

if TYPE_CHECKING:
    from execution_testing.test_types import (
        Environment as TestingEnvironment,
    )
    from execution_testing.test_types import (
        Transaction as TestingTransaction,
    )


@dataclass
class CallResult:
    """
    What running one message produced.

    `eth_call` reports the return data and nothing else, but the error is
    carried too because it decides *how* the data is reported: a revert
    returns its data under an error object, while a successful call
    returns it as the result.
    """

    return_data: Bytes
    """The output of the message's top-level frame."""

    error: Optional[EthereumException]
    """The error the message halted with, if any."""

    @property
    def succeeded(self) -> bool:
        """Return whether the message ran to completion."""
        return self.error is None


class EthCall(Load):
    """
    Run a single message against a state, and report what it returned.

    Construction resolves the fork and stores the inputs; `run` performs
    the execution. The split mirrors `T8N`, and keeps a caller free to
    build the tool once and decide later whether it is needed.
    """

    alloc: Final[Any]
    env: Final["TestingEnvironment"]
    tx: Final["TestingTransaction"]
    chain_id: Final[U64]

    def __init__(
        self,
        *,
        fork_name: str,
        alloc: Any,
        env: "TestingEnvironment",
        tx: "TestingTransaction",
        chain_id: int,
    ) -> None:
        """
        Prepare a call of `tx` against `alloc` in the context of `env`.

        `env` describes the block the call *names*, not the block that
        contained any original transaction: a client resolves
        `eth_call(message, "0x5")` against the state at the end of block
        5 and the block context of block 5's own header, so `NUMBER`,
        `TIMESTAMP` and `BASEFEE` are that header's.

        BPO blob-schedule overrides are not threaded through, unlike
        `T8N`, so `BLOBBASEFEE` inside a call on a BPO fork would use the
        non-BPO ancestor's update fraction. Nothing derives such a call
        today; the parameter belongs here when something does.
        """
        super().__init__(resolve_fork(fork_name))
        self.alloc = alloc
        self.env = env
        self.tx = tx
        self.chain_id = U64(chain_id)

    def run(self) -> CallResult:
        """
        Execute the message and report its return data.

        An admission failure — an unaffordable message, a nonce that does
        not match — raises `EthereumException` out of
        `process_transaction` rather than being reported here. That is
        deliberate: a client answers such a request with an error object
        whose code no specification fixes, so there is no value to
        derive and the caller must decide what to do instead of being
        handed a plausible-looking empty result.
        """
        block_env = build_block_environment(
            fork=self.fork,
            env=self.env,
            pre_state=self.alloc,
            chain_id=self.chain_id,
            state_test=True,
        )
        block_output = self.fork.BlockOutput()
        fork_tx = load_testing_transaction(self.tx, self.fork)

        # Tracing is a process-global setting, and a fill run has an
        # opcode counter installed for the benchmark path. A call is not
        # part of any block, so letting it reach that counter would
        # attribute opcodes to a block that never executed them.
        previous_tracer = trace.set_evm_trace(trace.discard_evm_trace)
        try:
            result = self.fork.process_transaction(
                block_env, block_output, fork_tx, Uint(0)
            )
        finally:
            trace.set_evm_trace(previous_tracer)

        return CallResult(
            return_data=Bytes(result.return_data), error=result.error
        )


__all__ = ["CallResult", "EthCall"]
