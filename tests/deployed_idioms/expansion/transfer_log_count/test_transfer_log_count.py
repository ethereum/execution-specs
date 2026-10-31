"""
"My event is log 0" -- log counting and log-index arithmetic under EIP-7708.

EIP-7708 emits a `Transfer(address,address,uint256)` log from
SYSTEM_ADDRESS (0xff..fe) for every non-zero ETH movement. No gas rule moves;
this is a purely **semantic** break, which is why none of the gas-shaped
archetypes in this corpus can reach it.

Two deployed idioms break, and the reference implementation makes the reason
exact.

1. **Log-index arithmetic.** The transfer log is emitted inside
   `execute_code` BEFORE the frame's first opcode runs
   (amsterdam/vm/interpreter.py:418-430), so for a value-bearing call the
   callee's own event moves from index 0 to index 1. Anything that reads
   `receipt.logs[0]`, slices from a fixed offset, or asserts "exactly N
   logs" now sees different data for an unchanged transaction.

2. **The topic collides with ERC-20 exactly.** `TRANSFER_TOPIC =
   keccak256(b"Transfer(address,address,uint256)")`
   (amsterdam/vm/__init__.py:35) is byte-identical to the ERC-20 `Transfer`
   event signature every token on mainnet emits. A consumer filtering on
   topic0 alone -- the overwhelmingly common subscription shape -- now
   ingests ETH movements as token transfers. The only discriminator is the
   log's `address` field being SYSTEM_ADDRESS.

The exceptions matter as much as the rule, because they decide which
transactions change shape and which do not:

    value == 0            no log  (interpreter.py:418, `evm.value != 0`)
    caller == target      no log  (interpreter.py:425)
    DELEGATECALL          no log  (no value is moved)

A detail the mutation harness turned up rather than reading: "zero value,
no log" is enforced **twice**, at the call site (`evm.value != 0`,
interpreter.py:418) and again inside `emit_transfer_log`
(`if transfer_amount == 0: return`, vm/__init__.py:270). Removing either one
alone leaves the behaviour unchanged, because the other still blocks the log,
so no single-site mutation can falsify the zero-value arm. Both were measured
and both survive. The arm is therefore a control against a single-site
regression rather than a mutation-falsifiable assertion -- see README.

So the shape of a receipt now depends on whether the call carried ETH. A
zero-value ERC-20 `transfer()` is unchanged; the same contract called with
1 wei attached is not.

**Non-duplicative with the official suite, and the reason is structural.**
`tests/amsterdam/eip7708_eth_transfer_logs/` is 1,594 lines over 36 tests
and covers the emission side exhaustively -- ordering, zero value, self
transfer, SELFDESTRUCT, precompiles, every transaction type. It carries
`pytestmark = pytest.mark.valid_from("EIP7708")` (test_transfer_logs.py:41),
so it asserts **nothing about the forks the deployed consumers were written
against**. The invariant arm below is the half that cannot exist inside a
`valid_from` suite: it is `valid_until("Osaka")` by construction, and it
*would* fail if run on Amsterdam. That is the product, not a defect.

**Witness.** Protocol constant, no single address witness: a log consumer is
off-chain (indexers, subgraphs, `eth_getLogs` filters) and no opcode lets a
contract read a log, so there is no on-chain idiom to point an address at.
The honest population statement is the ERC-20 topic itself -- the collision
is with every token contract on mainnet by construction, since the topic is
the same 32 bytes. Labelled as such rather than dressed up as a measured
count.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    keccak256,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7708.md"
REFERENCE_SPEC_VERSION = "f7230c46a743313957d8f38a159bda934cc735b2"

SYSTEM_ADDRESS = Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)

# Written out rather than imported from the EIP-7708 spec module on purpose:
# the claim under test is that the protocol's topic IS the ERC-20 one, so
# both sides of that equality must be stated independently.
ERC20_TRANSFER_TOPIC = Hash(keccak256(b"Transfer(address,address,uint256)"))

OWN_TOPIC = Hash(0x1111)
PAYLOAD = Bytes((0xCAFE).to_bytes(32, "big"))

# A contract that emits exactly one event of its own.
EMITTER = Op.MSTORE(0, 0xCAFE) + Op.LOG1(0, 32, OWN_TOPIC) + Op.STOP


def _own_log(addr: Address) -> TransactionLog:
    """The callee's own event."""
    return TransactionLog(address=addr, topics=[OWN_TOPIC], data=PAYLOAD)


def _system_transfer_log(
    sender: Address, recipient: Address, amount: int
) -> TransactionLog:
    """The EIP-7708 log, built from the ERC-20 topic and SYSTEM_ADDRESS."""
    return TransactionLog(
        address=SYSTEM_ADDRESS,
        topics=[
            ERC20_TRANSFER_TOPIC,
            Hash(bytes(sender).rjust(32, b"\x00")),
            Hash(bytes(recipient).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )


def _erc20_style_log(
    token: Address, frm: Address, to: Address, amount: int
) -> TransactionLog:
    """What a token contract emits: the same topic0, its own address."""
    return TransactionLog(
        address=token,
        topics=[
            ERC20_TRANSFER_TOPIC,
            Hash(bytes(frm).rjust(32, b"\x00")),
            Hash(bytes(to).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )


def _token(pre: Alloc, frm: Address, to: Address, amount: int) -> Address:
    """A contract whose single event is ERC-20-shaped."""
    return pre.deploy_contract(
        Op.MSTORE(0, amount)
        + Op.LOG3(
            0,
            32,
            ERC20_TRANSFER_TOPIC,
            int.from_bytes(bytes(frm), "big"),
            int.from_bytes(bytes(to), "big"),
        )
        + Op.STOP
    )


# ---------------------------------------------------------------------------
# Arm 1: the invariant. A value-bearing call produces the callee's log only.
# ---------------------------------------------------------------------------
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_value_bearing_call_emits_only_the_callees_log(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a value-bearing call yields exactly one log, the callee's, at index 0.

    This is the whole of "assert exactly N logs" and of every fixed log
    offset in deployed consumer code. It holds on six forks and is asserted
    on none of them, because the official EIP-7708 suite is `valid_from` the
    fork that breaks it.
    """
    sender: EOA = pre.fund_eoa(amount=10**18)
    emitter = pre.deploy_contract(EMITTER)
    tx = Transaction(
        to=emitter,
        value=1,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(logs=[_own_log(emitter)]),
    )
    state_test(pre=pre, post={emitter: Account(balance=1)}, tx=tx)


# ---------------------------------------------------------------------------
# Arm 2: the violation. The system log takes index 0 and shifts the callee's.
# ---------------------------------------------------------------------------
@pytest.mark.valid_from("EIP7708")
def test_system_log_takes_index_zero_from_eip7708(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the identical transaction now yields two logs, the callee's second.

    Same shape as arm 1, two logs instead of one, and the callee's event at
    index 1. A consumer indexing by position reads the system log where it
    expected the contract's, and `logs.length == 1` is now false.
    """
    sender: EOA = pre.fund_eoa(amount=10**18)
    emitter = pre.deploy_contract(EMITTER)
    tx = Transaction(
        to=emitter,
        value=1,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(
            logs=[
                _system_transfer_log(sender, emitter, 1),
                _own_log(emitter),
            ]
        ),
    )
    state_test(pre=pre, post={emitter: Account(balance=1)}, tx=tx)


# ---------------------------------------------------------------------------
# Arm 3: the control that keeps the claim honest. Zero value, no extra log.
# ---------------------------------------------------------------------------
@pytest.mark.valid_from("EIP7708")
def test_zero_value_call_still_emits_only_the_callees_log(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a zero-value call is unchanged, so the hazard is value-dependent.

    The call site guards on `evm.value != 0` before any log is built
    (amsterdam/vm/interpreter.py:418), and `emit_transfer_log` guards the
    amount again (vm/__init__.py:270). Without this arm the archetype
    would read as "every call gained a log", which is false and would make
    the index shift look unconditional. It is conditional on the call
    carrying ETH -- which is exactly why it is easy to miss in testing and
    then meet in production.
    """
    sender: EOA = pre.fund_eoa(amount=10**18)
    emitter = pre.deploy_contract(EMITTER)
    tx = Transaction(
        to=emitter,
        value=0,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(logs=[_own_log(emitter)]),
    )
    state_test(pre=pre, post={emitter: Account(balance=0)}, tx=tx)


# ---------------------------------------------------------------------------
# Arm 4: the topic collision, stated from both sides.
# ---------------------------------------------------------------------------
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_only_tokens_emit_the_erc20_transfer_topic(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a topic0 filter on the ERC-20 Transfer signature sees only the token.

    One log, carrying the ERC-20 topic, emitted by the token's own address.
    This is the invariant behind every `eth_getLogs` subscription that
    filters on topic0 and not on address.
    """
    sender: EOA = pre.fund_eoa(amount=10**18)
    holder = Address(0xBEEF)
    token = _token(pre, sender, holder, 7)
    tx = Transaction(
        to=token,
        value=1,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(
            logs=[_erc20_style_log(token, sender, holder, 7)]
        ),
    )
    state_test(pre=pre, post={token: Account(balance=1)}, tx=tx)


@pytest.mark.valid_from("EIP7708")
def test_eth_movements_now_carry_the_erc20_transfer_topic(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the receipt now holds two logs with the SAME topic0.

    The protocol's log and the token's log are indistinguishable on topics:
    both carry `keccak256("Transfer(address,address,uint256)")` and both are
    `(from, to)`-indexed with a uint256 amount. They differ only in the
    `address` field -- SYSTEM_ADDRESS versus the token. A topic0-only
    subscription now counts ETH as a token transfer, and the amounts are in
    different units.

    Pinning the equality from this side also means a later fork that
    *disambiguates* the topic fails this test rather than silently changing
    every indexer's results again.
    """
    sender: EOA = pre.fund_eoa(amount=10**18)
    holder = Address(0xBEEF)
    token = _token(pre, sender, holder, 7)
    tx = Transaction(
        to=token,
        value=1,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(
            logs=[
                _system_transfer_log(sender, token, 1),
                _erc20_style_log(token, sender, holder, 7),
            ]
        ),
    )
    state_test(pre=pre, post={token: Account(balance=1)}, tx=tx)
