"""
Derive `eth_call` expectations by executing a message against the chain.

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

- The **signature** is supplied. The message names an account whose key
  the test holds, so the synthesized transaction is genuinely signed and
  `recover_sender` yields the address the message named. See
  `SENDER_MUST_BE_SIGNABLE` for what that costs.
- The **nonce** is read from the state the call names, so the value the
  spec checks is the value it finds.
- The **fee** is the named block's own base fee, carried as an explicit
  `gasPrice`. A client given an explicit price runs the same balance
  arithmetic the spec does, so the two agree on whether the message is
  affordable instead of one waiving a check the other enforces.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Mapping

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.forks import Fork

if TYPE_CHECKING:
    from execution_testing.fixtures.blockchain import FixtureHeader
    from execution_testing.test_types import Alloc, Environment


logger = logging.getLogger(__name__)


SENDER_MUST_BE_SIGNABLE = """\
A derived `eth_call` runs its message through the fork's own
`process_transaction`, which recovers the sender from a signature, so the
message can only name a sender the test can sign for.

This is a limitation of the tool rather than of the specification. A
sender can be asserted instead of recovered — `check_transaction` takes
`asserted_sender` for exactly that — but `process_transaction` does not
forward the keyword, and going around it would mean reimplementing the
transition function once per fork, since the steps between admission and
the top-level frame are named differently in each. Forwarding that one
keyword would lift the restriction and let a call name any address,
including a contract and the zero address."""


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
class CallReplay:
    """
    A message to run as a call, and the state to run it against.

    Assembled during generation, where the signed transactions and the
    per-block states are both still in hand. A finished fixture has
    neither: its transactions carry no key and it stores only the state
    the chain ended on.
    """

    site: CallSite
    """The block the call names."""

    sender: Address
    """The account the message is sent from."""

    signing_key: Hash
    """The key that signs for `sender`; see `SENDER_MUST_BE_SIGNABLE`."""

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


def run_call(
    site: CallSite,
    *,
    sender: Address,
    signing_key: Hash,
    to: Address | None,
    data: Bytes,
    value: int,
    gas: int,
) -> CallOutcome:
    """
    Run one message at `site` and report what the specification answers.

    The nonce is read from the state the call names rather than carried
    over from any original transaction, so this holds for a message the
    chain never contained as well as for one it did.

    A message that cannot be admitted, or that halts for any reason other
    than a revert, raises `UnrunnableCallError`. Neither has an
    expectation worth storing: the first never reaches the EVM, and the
    second is reported by a code — `-32000` in go-ethereum — that no
    specification fixes, so pinning it would enshrine one client's
    choice.
    """
    from execution_testing.test_types import Transaction

    gas_price = site.gas_price
    account = _account(site.state, sender)
    nonce = 0 if account is None else int(account.nonce or 0)
    balance = 0 if account is None else int(account.balance or 0)
    if balance < gas * gas_price + value:
        raise UnrunnableCallError(
            f"{sender} cannot afford a call of {gas} gas at {gas_price} "
            f"wei carrying {value} wei: it holds {balance} wei at the end "
            f"of block {site.number}"
        )

    fees: Dict[str, Any] = (
        {"gas_price": gas_price}
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
        secret_key=signing_key,
        **fees,
    ).with_signature_and_sender()

    # Lazy, and the only place the testing package reaches the spec's own
    # machinery for this method. See the module docstring.
    from ethereum.exceptions import EthereumException
    from ethereum_spec_tools.evm_tools.call import EthCall

    try:
        result = EthCall(
            fork_name=site.fork.transition_tool_name(),
            alloc=site.state,
            env=site.environment,
            tx=transaction,
            chain_id=site.chain_id,
        ).run()
    except EthereumException as rejected:
        raise UnrunnableCallError(
            f"a call from {sender} at block {site.number} was not "
            f"admitted: {rejected!r}"
        ) from rejected

    return_data = str(Bytes(result.return_data))
    if result.error is None:
        return CallOutcome(return_data=return_data, reverted=False)
    if type(result.error).__name__ == "Revert":
        return CallOutcome(return_data=return_data, reverted=True)
    raise UnrunnableCallError(
        f"a call from {sender} at block {site.number} halted with "
        f"{result.error!r}, which clients report under a code no "
        f"specification fixes"
    )


__all__ = [
    "CALL_GAS_LIMIT",
    "REVERT_ERROR_CODE",
    "SENDER_MUST_BE_SIGNABLE",
    "CallOutcome",
    "CallReplay",
    "CallSite",
    "UnrunnableCallError",
    "call_message",
    "environment_at",
    "run_call",
]
