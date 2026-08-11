"""
Answer a call-shaped request by running one message against a state.

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

The message carries no signature. Its sender is *asserted*:
`process_transaction` forwards `asserted_sender` to `check_transaction`,
which then skips signature recovery and, with it, the requirement that
the sender be an externally owned account -- both being properties of a
sender derived from a signature. A call may therefore name any address,
including a contract and the zero address, which is what a client allows
and what the tool could not express while it had to sign.

## The warm sets

`eth_createAccessList` needs more than the return data: it needs the
addresses and storage slots the message touched. The EVM already tracks
both, as `accessed_addresses` and `accessed_storage_keys` on the frame,
because warm-versus-cold pricing depends on them — so nothing is
re-tracked here. What is needed is a way to *read* them, and the
specification already publishes the settled top-level frame to a tracer
when it emits `TransactionEnd`. The tracer installed by `run` keeps that
frame instead of discarding it, which is why this needs no change to any
fork.

The same tracer answers the one question the warm sets cannot: which of
their members the message *created*, those being warm for free and so
not worth declaring. A frame running init code has no `code_address`,
which is how it is recognized as it goes past.
"""

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Final,
    List,
    Optional,
    Set,
    Tuple,
)

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


@dataclass(frozen=True)
class AccessListEntry:
    """
    One address, and the storage slots of it the message touched.

    The shape EIP-2930 gives an access-list entry, and the shape
    `eth_createAccessList` answers in.
    """

    address: Bytes
    """The account the entry declares."""

    storage_keys: Tuple[Bytes, ...]
    """Its touched slots, ascending; empty when only the account was."""


@dataclass
class CallResult:
    """
    What running one message produced.

    `eth_call` reports the return data and nothing else, but the error is
    carried too because it decides *how* the data is reported: a revert
    returns its data under an error object, while a successful call
    returns it as the result.

    The gas and the access list are for `eth_createAccessList`, which
    reports both. They are collected unconditionally rather than behind a
    flag, because the EVM tracks them whatever the caller asked for and
    reading them off the settled frame costs nothing.
    """

    return_data: Bytes
    """The output of the message's top-level frame."""

    error: Optional[EthereumException]
    """The error the message halted with, if any."""

    gas_used: Uint = Uint(0)
    """Gas charged to the sender, after refunds."""

    access_list: Tuple[AccessListEntry, ...] = ()
    """
    The entries an access list would have to declare; see
    `declarable_access_list`.
    """

    undeclared_created: Tuple[Bytes, ...] = ()
    """
    Addresses created by the message and left out of `access_list`.

    Reported because clients do not agree about them and a caller may
    want to say less about an answer that turns on one; see
    `declarable_access_list` for why they are left out, and
    `create_access_list` for what the derivation does with this.

    Empty for the great majority of messages, and empty in two cases
    that look as though they should populate it. A creation whose init
    code writes storage is declared for its slots, so nothing was left
    out. A message with no recipient at all has its created address left
    out, but that address is the recipient, which every client excludes
    by name and none of them argues about.
    """

    @property
    def succeeded(self) -> bool:
        """Return whether the message ran to completion."""
        return self.error is None


def _frame_attribute(evm: Any, name: str) -> Any:
    """
    Read a frame parameter, whichever shape the fork's frame has.

    A frame's parameters live directly on `Evm` in later forks and on the
    `Message` it holds in earlier ones. Both are the specification's own
    layout, so the reader accommodates them rather than picking one.
    """
    try:
        return getattr(evm, name)
    except AttributeError:
        return getattr(evm.message, name)


def declarable_access_list(
    evm: Any,
    precompiles: AbstractSet[Any],
    created: AbstractSet[Any] = frozenset(),
) -> Tuple[AccessListEntry, ...]:
    """
    Return the entries an access list for `evm`'s message would declare.

    The warm sets are read off the settled top-level frame; the work here
    is deciding which of their members are worth declaring, and the answer
    follows from what an access list is *for*. Declaring an entry costs
    gas and buys warmth, so an address that is already warm by rule buys
    nothing and is left out:

    - **the precompiles**, warmed at the start of every transaction;
    - **the sender**, likewise;
    - **the recipient** — for a creation, the address being created;
    - **an address created during the message**, warmed by the `CREATE`
      that made it;
    - **the fee recipient**, on the forks that warm it.

    The first four are excluded on the strength of the specification
    rather than on any client's convention. Storage slots have no such
    rule — the recipient's own slots start cold, and so does every slot
    of a freshly created account — so all of them are declared, which is
    why an excluded address can still appear here carrying slots.

    The fee recipient is excluded unconditionally, including on the forks
    that do not warm it. The two cases differ only for a message whose
    opcodes *name* the fee recipient, which is then dropped from a list it
    belongs in; a warming fork would drop it from a list it does not
    belong in either way, so one exotic shape is mis-answered rather than
    two rules maintained.

    A created address is excluded on the same footing as the recipient
    and for a sharper reason than symmetry. `CREATE` adds the address it
    computes to `accessed_addresses` in the *calling* frame, before the
    child is dispatched and without rolling it back, so there is no
    execution in which declaring it saves a cold access — while declaring
    it costs the caller `TX_ACCESS_LIST_ADDRESS`, and on the forks that
    charge for access-list bytes rather more than that. An entry that can
    only ever raise the price of the message it advises on does not
    belong in the answer, whatever else the answer is taken to mean.

    Two further cases the specification and go-ethereum answer
    differently, documented rather than reconciled:

    - **A delegation target.** Resolving a delegation reads the target's
      account and warms it, so declaring the target saves a cold access
      and it belongs here; go-ethereum's tracer watches opcodes, no
      opcode names a delegation target, and so it omits one. This is the
      case where the specification is right, and the derivation refuses
      such a message rather than asserting an answer no client gives.
    - **A frame that reverted.** The specification discards a failed
      child's warm sets, as the pricing rules require; go-ethereum's
      tracer keeps them. Declaring what a reverted frame touched *would*
      pay off if the frame is retried, so go-ethereum is arguably right
      here too.

    A fork predating warm-and-cold accounting has no sets to read and
    yields nothing.

    Both levels are sorted ascending. An access list is a set and no
    specification fixes an order for one, so an order is chosen here only
    to make the derived value reproducible from run to run.
    """
    warm_addresses = getattr(evm, "accessed_addresses", None)
    if warm_addresses is None:
        return ()
    warm_slots = evm.accessed_storage_keys

    rule_warmed = set(precompiles) | set(created)
    rule_warmed.add(_frame_attribute(evm, "tx_env").origin)
    rule_warmed.add(_frame_attribute(evm, "current_target"))
    rule_warmed.add(_frame_attribute(evm, "block_env").coinbase)

    slots_by_address: Dict[Any, Set[Any]] = {}
    for address, key in warm_slots:
        slots_by_address.setdefault(address, set()).add(key)

    declared = set(warm_addresses) - rule_warmed | set(slots_by_address)
    return tuple(
        AccessListEntry(
            address=Bytes(address),
            storage_keys=tuple(
                Bytes(key) for key in sorted(slots_by_address.get(address, ()))
            ),
        )
        for address in sorted(declared)
    )


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
    sender: Final[str]
    chain_id: Final[U64]

    def __init__(
        self,
        *,
        fork_name: str,
        alloc: Any,
        env: "TestingEnvironment",
        tx: "TestingTransaction",
        sender: str,
        chain_id: int,
    ) -> None:
        """
        Prepare a call of `tx` against `alloc` in the context of `env`.

        `sender` is stated rather than read off `tx`, because `tx` carries
        no signature to read it from. Any address will do, including one
        no key exists for; see the module docstring.

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
        self.sender = sender
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
        # attribute opcodes to a block that never executed them. The
        # tracer installed instead keeps two things and discards the rest.
        #
        # The frame handed to `TransactionEnd` is the settled top-level
        # frame, and its warm sets are what an access list is derived
        # from. Every frame the tracer sees is also inspected for whether
        # it is a *creation* frame — a frame executing init code rather
        # than an account's code has no `code_address` — because a
        # created address is warm for free and must not be declared; see
        # `declarable_access_list`. Reading it here rather than from the
        # state keeps this working on the forks that predate a
        # created-account set, and needs no change to any fork.
        settled: List[Any] = []
        created: Set[Any] = set()

        def keep_what_the_access_list_needs(
            evm: object, event: trace.TraceEvent
        ) -> None:
            if _frame_attribute(evm, "code_address") is None:
                created.add(_frame_attribute(evm, "current_target"))
            if isinstance(event, trace.TransactionEnd):
                settled.append(evm)

        previous_tracer = trace.set_evm_trace(keep_what_the_access_list_needs)
        try:
            result = self.fork.process_transaction(
                block_env,
                block_output,
                fork_tx,
                Uint(0),
                asserted_sender=self.fork.hex_to_address(self.sender),
            )
        finally:
            trace.set_evm_trace(previous_tracer)

        # A message rejected before its frame was built emits no
        # `TransactionEnd`, having no frame to report; it touched nothing.
        # The precompiles come off the environment the message ran in
        # rather than off the fork, so a message that rearranged them
        # is measured against the arrangement it actually saw.
        access_list = (
            declarable_access_list(
                settled[-1], set(block_env.precompiles), created
            )
            if settled
            else ()
        )
        # A creation the *message itself* performed is left out by
        # everyone: the address is the message's own recipient, warmed
        # at the start of the transaction like any other, and named as
        # such by every client that excludes anything. Only a creation
        # performed by an opcode is contested, so only that one is
        # reported.
        uncontested = {entry.address for entry in access_list}
        if settled:
            uncontested.add(
                Bytes(_frame_attribute(settled[-1], "current_target"))
            )
        return CallResult(
            return_data=Bytes(result.return_data),
            error=result.error,
            gas_used=result.gas_used,
            access_list=access_list,
            undeclared_created=tuple(
                sorted(
                    Bytes(address)
                    for address in created
                    if Bytes(address) not in uncontested
                )
            ),
        )


__all__ = [
    "AccessListEntry",
    "CallResult",
    "EthCall",
    "declarable_access_list",
]
