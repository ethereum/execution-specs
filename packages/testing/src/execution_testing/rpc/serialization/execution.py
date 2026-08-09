"""
Derive call-shaped expectations by executing a message against the chain.

Every other method in this package is a projection: the transition tool
already computed the answer and the code here reformats it. `eth_call` is
the first that is not. A call is a message run against the state at a
named block, which never happened on chain, so the expectation has to be
*executed* rather than read off.

The execution itself is not done here. `ethereum_spec_tools.evm_tools.call`
holds the tool, a sibling of `t8n` invoked the same way, and this module
supplies the two things a tool cannot know: which message to run, and
against which state. The specification is reached through exactly one
lazy import, for the same reason `client_clis.clis.execution_specs` uses
one — the `ethereum` package must not be imported while pytest is still
configuring.

## What a client actually does

`eth_call(message, "0x5")` resolves the state at the *end* of block 5 and
the block context of block 5's *own* header, so `NUMBER`, `TIMESTAMP`,
`BASEFEE` and `COINBASE` are that header's. Both halves are reproduced
here; getting only the state right would leave the two sides disagreeing
about every context opcode.

Clients also relax three admission checks a transaction faces — the
signature, the nonce, and the sender being an externally owned account.
The message emitted here is shaped so that relaxing them changes nothing,
rather than relying on the spec to relax them in the same way:

- The **signature** is absent, and the sender is asserted instead.
  `process_transaction` forwards an `asserted_sender` to
  `check_transaction`, which then skips both recovery and the
  externally-owned-account requirement, exactly as a client does. A
  message may therefore name any address: a contract, or the zero
  address, which is the commonest `from` in real usage and the one no
  test could ever hold a key for.
- The **nonce** is read from the state the call names, so the value the
  spec checks is the value it finds.
- The **fee** is the named block's own base fee, carried as an explicit
  `gasPrice`. A client given an explicit price runs the same balance
  arithmetic the spec does, so the two agree on whether the message is
  affordable instead of one waiving a check the other enforces. This is
  the one relaxation not taken; see `SENDER_MUST_BE_SOLVENT`.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Sequence

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.forks import Fork

if TYPE_CHECKING:
    from execution_testing.fixtures.blockchain import FixtureHeader
    from execution_testing.test_types import Alloc, Environment


logger = logging.getLogger(__name__)


SENDER_MUST_BE_SOLVENT = """\
A derived message states its price — the named block's base fee — so the
sender must hold `gas * gasPrice + value` at that block, and the spec's
own balance check is what enforces it.

This is the one admission check the derivation does not relax, and it is
deliberate rather than a leftover. A client waives it by pricing the
message at zero; matching that would have the two sides executing
different messages, and would silently change what a contract reading a
balance sees. An address the test holds no key for is fine — the sender
is asserted, not recovered — but an address holding nothing is not.
Fund it in the pre-alloc with `pre.fund_address`, which takes a bare
address."""


EXECUTED_METHODS = frozenset({"eth_call", "eth_createAccessList"})
"""
The declared methods whose answer comes from running a message.

Both need a state per block rather than only the chain's last one,
because a declared message names whichever block it likes. Collecting
those states costs a materialization per block, so a test that declares
neither method should not pay for them; naming the two here is what lets
the generator tell the difference.
"""


ACCESS_LIST_ROUNDS = 8
"""
The most times a message is re-run while its access list settles.

Attaching an access list changes what the message costs, so a message
whose control flow depends on `GAS` can touch something new on the second
run. The answer is the *fixed point*: re-run with what was found until a
run finds nothing further, which is what go-ethereum does and the only
definition under which the reported gas belongs to the reported list.

Convergence is not guaranteed — a contract can be written to oscillate —
so the loop is bounded and a message that does not settle derives nothing
rather than looping forever. Every case seen so far settles in two."""


CALL_GAS_LIMIT = 30_000_000
"""
The most gas a derived message is given, whatever the original asked for.

A client applies its own ceiling to `eth_call` and *silently lowers* a
larger request to it — go-ethereum's `--rpc.gascap` defaults to fifty
million — so a message naming more gas than that is not the message the
client executes. Under Amsterdam's two-pool accounting that is not a
harmless difference: the state gas reservoir is whatever the gas limit
exceeds `TX_MAX_GAS_LIMIT` by, so a capped limit yields a smaller
reservoir and a message that creates an account can run out of state gas
on one side and not the other.

Thirty million sits below every ceiling in circulation and well above
`TX_MAX_GAS_LIMIT` (2^24), so the reservoir is comfortably non-empty. A
transaction asking for less keeps its own limit, since the point of that
is usually the limit itself.
"""

REVERT_ERROR_CODE = 3
"""
The JSON-RPC code under which a reverted call is reported.

Not a transport error: execution-apis defines `3` as "execution reverted"
and hangs the revert data off the error object. A call that reverts is
therefore an error response rather than a result, which is why a
reverting message derives an `error_code` and not a return value. Only
the code is asserted, as everywhere else here.
"""


class UnrunnableCallError(ValueError):
    """
    Raised when a message cannot be executed, so no value can be derived.

    Distinct from a message that runs and *fails*: a revert is an answer,
    and is derived as one. This is the case where execution never starts,
    which would assert nothing about the EVM.
    """


@dataclass(frozen=True)
class CallSite:
    """
    A state, and the block context a client pairs with it.

    One per block the chain produced, naming the block whose end state a
    call would see.
    """

    number: int
    """The block a call names, and whose end state it runs against."""

    state: "Alloc"
    """The state at the end of that block."""

    environment: "Environment"
    """The block context, taken from that block's own header."""

    fork: Fork
    """
    The fork active at that block, already resolved.

    Resolved rather than the fixture's own fork, because a transition
    chain ends on a different fork from the one it started on and a call
    naming an early block must run under the rules of that block.
    """

    chain_id: int
    """The chain the fixture asks a consumer to configure."""

    @property
    def gas_price(self) -> int:
        """
        Return the price a message at this site is priced at.

        The block's own base fee, so the fee check passes on both sides
        with nothing waived. A fork with no base fee prices at zero,
        where the check does not exist.
        """
        base_fee = self.environment.base_fee_per_gas
        return 0 if base_fee is None else int(base_fee)


@dataclass(frozen=True)
class CallOutcome:
    """What the specification answers for one message."""

    return_data: str
    """Hex-encoded output of the top-level frame."""

    reverted: bool
    """
    Whether the message halted with a revert.

    A revert is reported as an error rather than a result, so this
    decides which of the two the expectation becomes.
    """


@dataclass(frozen=True)
class AccessListOutcome:
    """What the specification answers for `eth_createAccessList`."""

    access_list: List[Dict[str, Any]]
    """The entries a client is expected to report."""

    gas_used: int
    """What the message costs with those entries attached."""

    reverted: bool
    """
    Whether the message halted with a revert.

    A client reports the halt as an `error` string alongside the list
    rather than as a JSON-RPC error, and the wording is its own, so this
    decides the tier the expectation is stored at rather than its shape.
    """

    @property
    def result(self) -> Dict[str, Any]:
        """Return the response body a client is expected to produce."""
        return {
            "accessList": self.access_list,
            "gasUsed": hex(self.gas_used),
        }

    @property
    def assertion(self) -> str:
        """Return the tier this outcome can honestly be stored at."""
        return "partial" if self.reverted else "exact"


@dataclass(frozen=True)
class CallReplay:
    """
    A message to run as a call, and the state to run it against.

    Assembled during generation, where the executed transactions and the
    per-block states are both still in hand. A finished fixture has
    neither: it stores only the state the chain ended on.
    """

    site: CallSite
    """The block the call names."""

    sender: Address
    """The account the message is sent from, asserted rather than signed."""

    to: Address | None
    """The recipient, or None for a creation."""

    data: Bytes
    """The message's calldata."""

    value: int
    """The wei the message carries."""

    gas: int
    """The gas the message is given."""


def environment_at(
    header: "FixtureHeader",
    block_hashes: Mapping[int, Hash],
) -> "Environment":
    """
    Return the block context a client builds for a call naming `header`.

    Every field is the header's own. The `parent_*` family is left unset
    because each value it exists to reconstruct — the base fee, the
    excess blob gas, the difficulty — is stated outright here.
    """
    from execution_testing.test_types import Environment

    return Environment(
        fee_recipient=header.fee_recipient,
        gas_limit=header.gas_limit,
        number=header.number,
        timestamp=header.timestamp,
        difficulty=header.difficulty,
        prev_randao=(
            None
            if header.prev_randao is None
            else int.from_bytes(header.prev_randao, "big")
        ),
        base_fee_per_gas=header.base_fee_per_gas,
        excess_blob_gas=header.excess_blob_gas,
        block_hashes={
            number: value
            for number, value in block_hashes.items()
            if number < int(header.number)
        },
    )


def call_message(
    *,
    sender: Address,
    to: Address | None,
    data: Bytes,
    value: int,
    gas: int,
    gas_price: int,
) -> Dict[str, Any]:
    """
    Return the message object a client is asked to execute.

    Every field is stated rather than left to a default. A client
    defaulting `gas` picks its own RPC gas cap and a client defaulting
    `gasPrice` picks zero and waives the fee check with it, either of
    which would have the two sides executing different messages.
    """
    message: Dict[str, Any] = {
        "from": str(sender),
        "input": str(data),
        "value": hex(value),
        "gas": hex(gas),
        "gasPrice": hex(gas_price),
    }
    if to is not None:
        # A creation names no recipient. The key is omitted rather than
        # set to null, because the schema types `to` as an address.
        message["to"] = str(to)
    return message


def _account(state: "Alloc", address: Address) -> Any:
    """Return an account from a post-state, or None if unallocated."""
    accounts = getattr(state, "root", state)
    return accounts.get(address)


@dataclass(frozen=True)
class MessageResult:
    """Everything one execution of a message produced."""

    return_data: str
    """Hex-encoded output of the top-level frame."""

    reverted: bool
    """Whether the message halted with a revert."""

    gas_used: int
    """Gas charged to the sender, after refunds."""

    access_list: List[Dict[str, Any]]
    """
    The entries an access list would declare, in the shape a client
    answers in. Sorted, and sorted within each entry.
    """


def _run_message(
    site: CallSite,
    *,
    sender: Address,
    to: Address | None,
    data: Bytes,
    value: int,
    gas: int,
    access_list: Sequence[Mapping[str, Any]] = (),
) -> MessageResult:
    """
    Run one message at `site` and report everything it produced.

    `sender` is any address at all. The message is unsigned and the
    address is asserted through `process_transaction`, so a contract and
    the zero address are as valid here as a key-bearing account.

    The nonce is read from the state the call names rather than carried
    over from any original transaction, so this holds for a message the
    chain never contained as well as for one it did.

    A message that cannot be admitted, or that halts for any reason other
    than a revert, raises `UnrunnableCallError`. Neither has an
    expectation worth storing: the first never reaches the EVM, and the
    second is reported by a code — `-32000` in go-ethereum — that no
    specification fixes, so pinning it would enshrine one client's
    choice.

    `access_list` is what the message carries, not what it produced. It
    is empty for a call, and for an access-list derivation it is the list
    the previous round found; see `create_access_list`.
    """
    from execution_testing.base_types import AccessList
    from execution_testing.test_types import Transaction

    gas_price = site.gas_price
    account = _account(site.state, sender)
    nonce = 0 if account is None else int(account.nonce or 0)
    balance = 0 if account is None else int(account.balance or 0)
    if balance < gas * gas_price + value:
        raise UnrunnableCallError(
            f"{sender} cannot afford a call of {gas} gas at {gas_price} "
            f"wei carrying {value} wei: it holds {balance} wei at the end "
            f"of block {site.number}. {SENDER_MUST_BE_SOLVENT}"
        )

    fees: Dict[str, Any] = (
        # A legacy transaction encodes its chain id in `v`, and an
        # unsigned message has no signature to encode one in. 27 is the
        # pre-EIP-155 form, which names no chain, so the spec skips the
        # chain-id check rather than reading a nonsense id out of a
        # zeroed `v` — which it rejects outright as a bad `v`.
        {"gas_price": gas_price, "v": 27}
        if site.environment.base_fee_per_gas is None
        else {
            "ty": 2,
            "max_fee_per_gas": gas_price,
            "max_priority_fee_per_gas": gas_price,
        }
    )
    transaction = Transaction(
        chain_id=site.chain_id,
        nonce=nonce,
        gas_limit=gas,
        to=to,
        value=value,
        data=data,
        access_list=[
            AccessList(
                address=Address(entry["address"]),
                storage_keys=[Hash(key) for key in entry["storageKeys"]],
            )
            for entry in access_list
        ]
        or None,
        **fees,
    )

    # Lazy, and the only place the testing package reaches the spec's own
    # machinery for these methods. See the module docstring.
    from ethereum.exceptions import EthereumException
    from ethereum_spec_tools.evm_tools.call import EthCall

    try:
        result = EthCall(
            fork_name=site.fork.transition_tool_name(),
            alloc=site.state,
            env=site.environment,
            tx=transaction,
            sender=str(sender),
            chain_id=site.chain_id,
        ).run()
    except EthereumException as rejected:
        raise UnrunnableCallError(
            f"a call from {sender} at block {site.number} was not "
            f"admitted: {rejected!r}"
        ) from rejected

    if result.error is not None and type(result.error).__name__ != "Revert":
        raise UnrunnableCallError(
            f"a call from {sender} at block {site.number} halted with "
            f"{result.error!r}, which clients report under a code no "
            f"specification fixes"
        )

    return MessageResult(
        return_data=str(Bytes(result.return_data)),
        reverted=result.error is not None,
        gas_used=int(result.gas_used),
        access_list=[
            {
                "address": str(Address(entry.address)),
                "storageKeys": [str(Hash(key)) for key in entry.storage_keys],
            }
            for entry in result.access_list
        ],
    )


def run_call(
    site: CallSite,
    *,
    sender: Address,
    to: Address | None,
    data: Bytes,
    value: int,
    gas: int,
) -> CallOutcome:
    """Run one message at `site` and report what `eth_call` answers."""
    result = _run_message(
        site, sender=sender, to=to, data=data, value=value, gas=gas
    )
    return CallOutcome(
        return_data=result.return_data, reverted=result.reverted
    )


DELEGATION_MARKER = bytes.fromhex("ef0100")
"""
The prefix of the code a delegated account carries.

Read here only to *refuse* a derivation; see `create_access_list`.
"""


def _is_delegated(state: "Alloc", address: Address | None) -> bool:
    """Return whether `address` holds a delegation designator."""
    if address is None:
        return False
    account = _account(state, address)
    code = bytes(getattr(account, "code", b"") or b"")
    return code.startswith(DELEGATION_MARKER)


def create_access_list(
    site: CallSite,
    *,
    sender: Address,
    to: Address | None,
    data: Bytes,
    value: int,
    gas: int,
) -> AccessListOutcome:
    """
    Run one message at `site` and report what `eth_createAccessList` says.

    The touched set is not read off a single run. Attaching a list makes
    its entries warm and charges for them up front, so the gas the method
    reports — the gas the message would need *with the list attached* —
    can only come from a run that carried it. The message is therefore
    re-run with what the previous round found until a round finds nothing
    new, and the gas reported is that last round's; see
    `ACCESS_LIST_ROUNDS`.

    A reverting message still has an answer, unlike `eth_call`: a client
    reports the failure as a string field beside a perfectly good access
    list rather than as a JSON-RPC error. The string is client wording and
    is not derived, which is what drops a reverting expectation to the
    `partial` tier.

    **A message to a delegated account derives nothing.** Resolving a
    delegation reads the target's account, and the specification charges
    a cold access for it and warms it — so declaring the target saves
    exactly that, and the target belongs in the list. go-ethereum builds
    its list by watching opcodes, and no opcode names a delegation
    target, so it omits one and reports the higher gas that follows. This
    is the one disagreement in the method where the specification is the
    side that is right, and asserting it would fail every client rather
    than catch one. It is refused rather than weakened: a list missing an
    entry is not a partial answer, it is a wrong one.
    """
    if _is_delegated(site.state, to):
        raise UnrunnableCallError(
            f"{to} is delegated at block {site.number}, and clients omit "
            f"the delegation target from the access list where the "
            f"specification declares it; no expectation here would hold"
        )
    declared: List[Dict[str, Any]] = []
    for _ in range(ACCESS_LIST_ROUNDS):
        result = _run_message(
            site,
            sender=sender,
            to=to,
            data=data,
            value=value,
            gas=gas,
            access_list=declared,
        )
        if result.access_list == declared:
            return AccessListOutcome(
                access_list=declared,
                gas_used=result.gas_used,
                reverted=result.reverted,
            )
        declared = result.access_list
    raise UnrunnableCallError(
        f"the access list for a call from {sender} at block {site.number} "
        f"did not settle in {ACCESS_LIST_ROUNDS} rounds, so no gas figure "
        f"belongs to any of the lists found"
    )


def _resolve_site(
    method: str, reference: Any, sites: Sequence[CallSite]
) -> CallSite:
    """
    Return the site a declared call's block parameter names.

    Numbers and the two tags a chain determines are resolved; `safe` and
    `finalized` are not, because no chain determines them — a consumer is
    told what they are, and a value derived here would be guessing at the
    harness rather than reading the chain.
    """
    if not sites:
        raise UnrunnableCallError(
            f"{method} has no state to run against: the chain produced no "
            "block whose end state could be named"
        )
    by_number = {site.number: site for site in sites}
    named = str(reference).lower()
    if named == "latest":
        return max(sites, key=lambda site: site.number)
    if named == "earliest":
        return min(sites, key=lambda site: site.number)
    if named in BLOCK_TAGS_NO_CHAIN_DETERMINES:
        raise UnrunnableCallError(
            f"{method} at {named!r} names a block no chain determines, so "
            "there is no state to derive an answer from; name a number"
        )
    try:
        number = int(named, 16)
    except ValueError as malformed:
        raise UnrunnableCallError(
            f"{method} block parameter {reference!r} is neither a "
            f"quantity nor a tag this chain can resolve"
        ) from malformed
    if number not in by_number:
        raise UnrunnableCallError(
            f"{method} names block {number}, which this chain does not "
            f"have; it runs from {min(by_number)} to {max(by_number)}"
        )
    return by_number[number]


BLOCK_TAGS_NO_CHAIN_DETERMINES = frozenset({"safe", "finalized", "pending"})
"""
Tags whose block a chain does not fix, so no state here can be named.

`safe` and `finalized` are declared by a consensus layer and `pending` is
a client's own view of what it might build next.
"""


@dataclass(frozen=True)
class DeclaredMessage:
    """
    A declared call's completed parameters, and where to run them.

    The parameters are kept alongside the site because they are not the
    ones the author wrote; see `_declared_message`.
    """

    params: List[Any]
    """The parameters as they must be stored, not as they were written."""

    site: CallSite
    """The block the message names."""

    sender: Address
    """The account the message is sent from, asserted rather than signed."""

    to: Address | None
    """The recipient, or None for a creation."""

    data: Bytes
    """The message's calldata."""

    value: int
    """The wei the message carries."""

    gas: int
    """The gas the message is given."""


def _declared_message(
    method: str, params: Sequence[Any], sites: Sequence[CallSite]
) -> DeclaredMessage:
    """
    Read a declared message, and complete the fields it left out.

    The author supplies the question — enumeration cannot invent a
    message — and the answer is still computed by the caller, which is the
    rule every declared check in this package follows.

    **The stored message is not the written one.** An author writes the
    part that carries meaning — sender, recipient, calldata, value — and
    the fields that only have to *agree* are filled in here: `gas` and
    `gasPrice`, which a client would otherwise default to its own gas cap
    and to zero, executing a different message from the one whose answer
    was derived. Completing them at derivation is the only point where
    both sides are known, and it keeps the authoring burden to the part a
    test actually means.

    **The sender may be any address.** An `EOA`, a contract, or the zero
    address: the message is unsigned and its sender asserted, so nothing
    here needs a key. It reaches the fixture as a plain hex string in
    every case, because `FixtureRPCCall` renders byte-like parameters as
    hex before storing them. What the sender does still need is a balance;
    see `SENDER_MUST_BE_SOLVENT`.
    """
    if len(params) < 2 or not isinstance(params[0], Mapping):
        raise UnrunnableCallError(
            f"{method} needs a message object and a block to compute a result"
        )
    message, reference = params[0], params[1]
    site = _resolve_site(method, reference, sites)

    declared_sender = message.get("from")
    if declared_sender is None:
        raise UnrunnableCallError(
            f"{method} names no sender; a message must state `from`, which "
            "a client would otherwise default to the zero address"
        )

    declared_to = message.get("to")
    sender = Address(declared_sender)
    to = None if declared_to is None else Address(declared_to)
    data = Bytes(message.get("input", message.get("data", b"")))
    value = int(message.get("value", 0))
    gas = int(message.get("gas", CALL_GAS_LIMIT))
    return DeclaredMessage(
        params=[
            call_message(
                sender=sender,
                to=to,
                data=data,
                value=value,
                gas=gas,
                gas_price=site.gas_price,
            ),
            reference,
        ],
        site=site,
        sender=sender,
        to=to,
        data=data,
        value=value,
        gas=gas,
    )


@dataclass(frozen=True)
class DeclaredCall:
    """A declared `eth_call`'s completed parameters, and its answer."""

    params: List[Any]
    """The parameters as they must be stored, not as they were written."""

    outcome: CallOutcome
    """What the specification answers for them."""


@dataclass(frozen=True)
class DeclaredAccessList:
    """A declared access list's completed parameters, and its answer."""

    params: List[Any]
    """The parameters as they must be stored, not as they were written."""

    outcome: AccessListOutcome
    """What the specification answers for them."""


def compute_declared_call(
    params: Sequence[Any], sites: Sequence[CallSite]
) -> DeclaredCall:
    """Return the specification's answer to a call a test declared."""
    message = _declared_message("eth_call", params, sites)
    return DeclaredCall(
        params=message.params,
        outcome=run_call(
            message.site,
            sender=message.sender,
            to=message.to,
            data=message.data,
            value=message.value,
            gas=message.gas,
        ),
    )


def compute_declared_access_list(
    params: Sequence[Any], sites: Sequence[CallSite]
) -> DeclaredAccessList:
    """Return the access list the spec derives for a declared message."""
    message = _declared_message("eth_createAccessList", params, sites)
    return DeclaredAccessList(
        params=message.params,
        outcome=create_access_list(
            message.site,
            sender=message.sender,
            to=message.to,
            data=message.data,
            value=message.value,
            gas=message.gas,
        ),
    )


__all__ = [
    "ACCESS_LIST_ROUNDS",
    "EXECUTED_METHODS",
    "BLOCK_TAGS_NO_CHAIN_DETERMINES",
    "CALL_GAS_LIMIT",
    "REVERT_ERROR_CODE",
    "SENDER_MUST_BE_SOLVENT",
    "AccessListOutcome",
    "CallOutcome",
    "CallReplay",
    "CallSite",
    "DeclaredAccessList",
    "DeclaredCall",
    "MessageResult",
    "UnrunnableCallError",
    "call_message",
    "compute_declared_access_list",
    "compute_declared_call",
    "create_access_list",
    "environment_at",
    "run_call",
]
