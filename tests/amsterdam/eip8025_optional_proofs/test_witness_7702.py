"""Witness bytecode scenarios for EIP-7702 delegation."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Fork,
    Op,
    RecipientType,
    Transaction,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8025

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.STATICCALL, id="staticcall"),
    ],
)
def test_witness_codes_delegated_eoa(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    call_opcode: Op,
) -> None:
    """
    Call-type opcode targeting an EOA with pre-state delegation.

    Both the delegation marker code and the delegated contract's
    bytecode appear in executionWitness.codes.
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_eoa = pre.fund_eoa(delegation=delegate)

    caller_code = call_opcode(address=delegated_eoa) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    marker = Spec7702.delegation_designation(delegate)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(caller_code),
                            Bytes(marker),
                            Bytes(delegate_code),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
    ],
)
def test_witness_codes_delegated_eoa_insufficient_balance(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    call_opcode: Op,
) -> None:
    """
    CALL/CALLCODE to a delegated EOA with value greater than caller balance.

    The call must fail and return 0, but delegation resolution still reads
    both the marker code and the delegated bytecode into the witness before
    the insufficient-balance early return.
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_eoa = pre.fund_eoa(amount=0, delegation=delegate)

    caller_balance = 100
    transfer_value = 1_000
    caller_code = (
        Op.SSTORE(
            0,
            call_opcode(
                Op.GAS,
                delegated_eoa,
                transfer_value,
                0,
                0,
                0,
                0,
            ),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(
        code=caller_code,
        balance=caller_balance,
        storage={0: 1},
    )

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    marker = Spec7702.delegation_designation(delegate)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(caller_code),
                            Bytes(marker),
                            Bytes(delegate_code),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            caller: Account(balance=caller_balance, storage={0: 0}),
        },
    )


def test_witness_codes_sender_delegation_marker_included(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Transaction sent from an EOA with pre-state delegation.

    The sender's delegation marker code appears in
    executionWitness.codes because transaction validation reads
    the sender code .
    """
    delegate_code = Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_sender = pre.fund_eoa(delegation=delegate)

    recipient = pre.fund_eoa()
    tx = Transaction(
        sender=delegated_sender,
        to=recipient,
        gas_limit=500_000,
    )

    marker = Spec7702.delegation_designation(delegate)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(marker),
                        ],
                    )
                ),
            )
        ],
        post={
            delegated_sender: Account(nonce=2),
        },
    )


def test_witness_codes_top_level_tx_to_delegated_eoa(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Top-level transaction targeting a delegated EOA directly.

    Both the delegation marker and the delegated contract's code
    appear in executionWitness.codes. This is a distinct path from
    opcode-driven CALL tests because the delegation is resolved at
    the top-level message-call.
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_eoa = pre.fund_eoa(delegation=delegate)

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=delegated_eoa,
        gas_limit=500_000,
    )

    marker = Spec7702.delegation_designation(delegate)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(marker),
                            Bytes(delegate_code),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_codes_delegation_set_in_same_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Auth list sets delegation in tx1, then tx2 calls the EOA.

    The delegation marker is NOT in executionWitness.codes because
    it was written in tx1. The delegated contract's
    bytecode IS in codes because it is a pre-state read.

    Pre-state:
        alice (plain EOA, no code)
        delegate (contract with code)

    tx1 (type-4, auth list):
        set_delegation(alice -> delegate)
        => writes marker to alice (runtime creation of marker)

    tx2:
        caller --CALL--> alice
        => reads alice's marker  (NOT from pre-state since created in tx1)
        => reads delegate's code (pre-state => code_reads)

    Witness codes:
        delegate_code  IN  codes (pre-state read)
        marker        NOT IN codes (written in tx1)
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    alice = pre.fund_eoa(amount=0)

    caller_code = Op.CALL(address=alice) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    relayer = pre.fund_eoa()
    sender2 = pre.fund_eoa()

    marker = Spec7702.delegation_designation(delegate)

    tx1 = Transaction(
        sender=relayer,
        to=alice,
        gas_limit=500_000,
        authorization_list=[
            AuthorizationTuple(
                address=delegate,
                nonce=0,
                signer=alice,
            )
        ],
    )
    tx2 = Transaction(
        sender=sender2,
        to=caller,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(caller_code),
                            Bytes(delegate_code),
                        ],
                        codes_absent=[
                            Bytes(marker),
                        ],
                    )
                ),
            )
        ],
        post={
            alice: Account(
                nonce=1,
                code=marker,
            ),
        },
    )


def test_witness_codes_redelegation_old_marker_included_new_marker_excluded(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Re-delegate an EOA that already had delegation in pre-state.

    The OLD marker IS in executionWitness.codes because
    set_delegation() reads it via get_code() before overwriting.
    The NEW marker is NOT in codes because it is written via
    set_code().

    Pre-state:
        alice (delegated to delegate_old, marker in pre-state)
        delegate_old, delegate_new (contracts with code)

    tx (type-4, auth list):
        set_delegation(alice -> delegate_new)
        => reads alice's old marker via get_code() (pre-state)
        => writes new marker to alice via set_code()

    Witness codes:
        old_marker  IN  codes (pre-state read)
        new_marker NOT IN codes (written in this tx)
    """
    delegate_old_code = Op.PUSH1(0x01) + Op.POP + Op.STOP
    delegate_old = pre.deploy_contract(code=delegate_old_code)

    delegate_new_code = Op.PUSH1(0x02) + Op.POP + Op.STOP
    delegate_new = pre.deploy_contract(code=delegate_new_code)

    alice = pre.fund_eoa(delegation=delegate_old)

    relayer = pre.fund_eoa()
    recipient = pre.fund_eoa()

    old_marker = Spec7702.delegation_designation(delegate_old)
    new_marker = Spec7702.delegation_designation(delegate_new)

    tx = Transaction(
        sender=relayer,
        to=recipient,
        gas_limit=500_000,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_new,
                nonce=1,
                signer=alice,
            )
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(old_marker),
                        ],
                        codes_absent=[
                            Bytes(new_marker),
                        ],
                    )
                ),
            )
        ],
        post={
            alice: Account(
                nonce=2,
                code=new_marker,
            ),
        },
    )


@pytest.mark.parametrize(
    "extcode_opcode",
    [
        pytest.param("extcodesize", id="extcodesize"),
        pytest.param("extcodecopy", id="extcodecopy"),
        pytest.param("extcodehash", id="extcodehash"),
    ],
)
def test_witness_codes_extcode_delegated_eoa(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    extcode_opcode: str,
) -> None:
    """
    EXTCODE* opcode targeting a delegated EOA.

    Unlike CALL (which resolves delegation), EXTCODE* opcodes
    operate on the account's own code:

    EXTCODESIZE/EXTCODECOPY:
        Call get_code() on the account directly, returning the
        23-byte marker.  Marker IS in witness, delegate code
        is NOT.

    EXTCODEHASH:
        Read code_hash from the account leaf — no get_code()
        call.  Neither marker nor delegate code appear in
        witness.
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_eoa = pre.fund_eoa(delegation=delegate)

    if extcode_opcode == "extcodesize":
        op = Op.EXTCODESIZE(delegated_eoa) + Op.POP
    elif extcode_opcode == "extcodecopy":
        op = Op.EXTCODECOPY(delegated_eoa, 0, 0, 23)
    else:
        op = Op.EXTCODEHASH(delegated_eoa) + Op.POP

    caller_code = op + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    marker = Spec7702.delegation_designation(delegate)

    if extcode_opcode in ("extcodesize", "extcodecopy"):
        codes_present = [
            Bytes(caller_code),
            Bytes(marker),
        ]
        codes_absent = [Bytes(delegate_code)]
    else:
        codes_present = [Bytes(caller_code)]
        codes_absent = [
            Bytes(marker),
            Bytes(delegate_code),
        ]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=codes_present,
                        codes_absent=codes_absent,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_codes_delegation_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Delegation pointing to another delegated account (chain).

    The EIP-7702 spec says "clients must retrieve only the first
    code and then stop following the delegation chain."

    Pre-state:
        alice  --delegated-->  bob  --delegated-->  charlie

    CALL alice:
        calculate_delegation_cost() reads alice's marker
            => get_code(alice) => marker_alice (pre-state)
        Resolves to bob, then get_code(bob) => marker_bob
            (pre-state, but NOT followed further)

    Witness codes:
        marker_alice  IN  codes (pre-state read)
        marker_bob    IN  codes (pre-state read)
        charlie_code  NOT IN codes (never reached)
    """
    charlie_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    charlie = pre.deploy_contract(code=charlie_code)

    bob = pre.fund_eoa(delegation=charlie)
    alice = pre.fund_eoa(delegation=bob)

    caller_code = Op.CALL(address=alice) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    marker_alice = Spec7702.delegation_designation(bob)
    marker_bob = Spec7702.delegation_designation(charlie)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(caller_code),
                            Bytes(marker_alice),
                            Bytes(marker_bob),
                        ],
                        codes_absent=[
                            Bytes(charlie_code),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_codes_reset_delegation(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Reset delegation by setting address to zero.

    The EIP-7702 spec says setting address to 0x00..00 clears
    the code.  set_delegation() reads the authority's current
    code via get_code() to check the existing delegation is
    valid, so the old marker appears in witness.

    Pre-state:
        alice (delegated to delegate)

    tx (type-4, auth list address=0x00..00):
        set_delegation(alice -> 0x00..00)
        => reads old marker via get_code() (pre-state)
        => writes empty code via set_code()

    Witness codes:
        old_marker  IN  codes (pre-state read)
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    alice = pre.fund_eoa(delegation=delegate)

    relayer = pre.fund_eoa()
    recipient = pre.fund_eoa()

    old_marker = Spec7702.delegation_designation(delegate)

    tx = Transaction(
        sender=relayer,
        to=recipient,
        gas_limit=500_000,
        authorization_list=[
            AuthorizationTuple(
                address=Address(0),
                nonce=1,
                signer=alice,
            )
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(old_marker)],
                    )
                ),
            )
        ],
        post={
            alice: Account(
                nonce=2,
                code=b"",
            ),
        },
    )


def test_witness_codes_delegation_to_empty_account(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Delegation target has no code (empty account).

    The marker is read via get_code() and appears in witness.
    When resolving delegation, the target's code is fetched but
    has EMPTY_CODE_HASH, so get_code() returns early without
    recording a code_reads entry.

    Pre-state:
        alice  --delegated-->  empty_target (EOA, no code)

    tx to alice:
        Reads alice's marker via get_code() (pre-state)
        Resolves to empty_target, get_code(empty_target)
            => EMPTY_CODE_HASH => returns early, no witness

    Witness codes:
        marker  IN  codes (pre-state read)
    """
    empty_target = pre.fund_eoa()

    alice = pre.fund_eoa(delegation=empty_target)

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=alice,
        gas_limit=500_000,
    )

    marker = Spec7702.delegation_designation(empty_target)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(marker)],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_codes_auth_nonce_mismatch(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Auth tuple rejected due to nonce mismatch.

    The authority nonce check happens after validating the current
    authority code, so the marker must appear in the witness.
    """
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    alice = pre.fund_eoa(delegation=delegate)

    delegate_new_code = Op.PUSH1(0x99) + Op.POP + Op.STOP
    delegate_new = pre.deploy_contract(code=delegate_new_code)

    relayer = pre.fund_eoa()
    recipient = pre.fund_eoa()

    old_marker = Spec7702.delegation_designation(delegate)

    tx = Transaction(
        sender=relayer,
        to=recipient,
        gas_limit=500_000,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_new,
                nonce=99,  # Just hardcode a wrong nonce to trigger the failure
                signer=alice,
            )
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(old_marker)],
                    )
                ),
            )
        ],
        post={
            alice: Account(
                nonce=1,
                code=old_marker,
            ),
        },
    )


# Code of the contract bob delegates to in the shared-marker tests below.
# Running it through bob sets bob's slot 0, which proves that a read
# followed bob's delegation.
SHARED_DELEGATE_CODE = Op.SSTORE(0, 1) + Op.STOP

MARKER_READS = [
    "sender",
    "top_level",
    "call",
    "extcodesize",
    "extcodecopy",
    "authorization",
]


def _read_marker(
    pre: Alloc,
    read: str,
    bob: Address,
    marker: Bytes,
    authorization_list: list[AuthorizationTuple] | None = None,
) -> tuple[Transaction, list[Bytes], dict[Address, Account]]:
    """
    Return a transaction that reads bob's delegation `marker` via `read`.

    bob must have nonce 1 and delegate to a contract running
    `SHARED_DELEGATE_CODE`. The transaction applies `authorization_list`
    before its own read; the `sender` read happens in validation, before
    any authorization applies. Also return the codes the read adds to
    executionWitness.codes and the post-state that proves it happened.
    """
    authorization_list = list(authorization_list or [])
    sender = bob if read == "sender" else pre.fund_eoa()
    to: Address
    codes: list[Bytes] = []
    post: dict[Address, Account] = {}
    if read == "sender":
        to = pre.fund_eoa()
        post[bob] = Account(nonce=2, code=marker)
    elif read == "top_level":
        to = bob
        codes.append(Bytes(SHARED_DELEGATE_CODE))
        post[bob] = Account(storage={0: 1})
    elif read == "call":
        caller_code = Op.CALL(address=bob) + Op.STOP
        to = pre.deploy_contract(code=caller_code)
        codes += [Bytes(caller_code), Bytes(SHARED_DELEGATE_CODE)]
        post[bob] = Account(storage={0: 1})
    elif read == "extcodesize":
        caller_code = Op.SSTORE(0, Op.EXTCODESIZE(bob)) + Op.STOP
        to = pre.deploy_contract(code=caller_code)
        codes.append(Bytes(caller_code))
        post[to] = Account(storage={0: len(marker)})
    elif read == "extcodecopy":
        caller_code = (
            Op.EXTCODECOPY(bob, 0, 0, len(marker))
            + Op.SSTORE(0, Op.MLOAD(0))
            + Op.STOP
        )
        to = pre.deploy_contract(code=caller_code)
        codes.append(Bytes(caller_code))
        marker_word = int.from_bytes(marker.ljust(32, b"\0"), "big")
        post[to] = Account(storage={0: marker_word})
    elif read == "authorization":
        # Clearing bob's delegation validates and reads his marker first.
        to = pre.fund_eoa()
        authorization_list.append(
            AuthorizationTuple(address=Address(0), nonce=1, signer=bob)
        )
        post[bob] = Account(nonce=2, code=b"")
    else:
        raise ValueError(f"unknown read: {read}")

    tx = Transaction(
        sender=sender,
        to=to,
        authorization_list=authorization_list or None,
    )
    return tx, codes, post


@pytest.mark.parametrize("read", MARKER_READS)
def test_witness_codes_delegation_same_marker_then_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    read: str,
) -> None:
    """
    tx1 delegates alice to bob's target; tx2 reads bob's pre-state marker.

    Reading bob's marker would normally put it in executionWitness.codes,
    since it is pre-state code. Here tx1 first writes the same bytes, and
    code is keyed by hash, so tx2's read is served from the block's code
    writes and the marker is NOT in codes. This is the delegation
    counterpart of test_witness_codes_create_same_hash_then_read.
    """
    delegate = pre.deploy_contract(code=SHARED_DELEGATE_CODE)
    marker = Spec7702.delegation_designation(delegate)
    alice = pre.fund_eoa(amount=0)
    bob = pre.fund_eoa(delegation=delegate)

    # tx1 does not call alice, so only tx2 can put the delegate's code in
    # the witness.
    tx1 = Transaction(
        sender=pre.fund_eoa(),
        to=pre.fund_eoa(),
        authorization_list=[
            AuthorizationTuple(address=delegate, nonce=0, signer=alice)
        ],
    )
    tx2, codes_present, post = _read_marker(pre, read, bob, marker)
    post[alice] = Account(nonce=1, code=marker)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=codes_present,
                        codes_absent=[marker],
                    )
                ),
            )
        ],
        post=post,
    )


# bob as the sender is read in validation, before any authorization
# applies; test_witness_codes_marker_read_before_same_delegation_is_set
# covers that order.
@pytest.mark.parametrize(
    "read", [read for read in MARKER_READS if read != "sender"]
)
def test_witness_codes_delegation_same_marker_then_read_same_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    read: str,
) -> None:
    """
    One type-4 tx delegates alice to bob's target, then reads bob's marker.

    Reading bob's marker would normally put it in executionWitness.codes,
    since it is pre-state code. Here alice's authorization first writes
    the same bytes, so the read is served from the transaction's code
    writes and the marker is NOT in codes. This is the delegation
    counterpart of test_witness_codes_create_same_hash_then_read_same_tx.
    """
    delegate = pre.deploy_contract(code=SHARED_DELEGATE_CODE)
    marker = Spec7702.delegation_designation(delegate)
    alice = pre.fund_eoa(amount=0)
    bob = pre.fund_eoa(delegation=delegate)

    tx, codes_present, post = _read_marker(
        pre,
        read,
        bob,
        marker,
        authorization_list=[
            AuthorizationTuple(address=delegate, nonce=0, signer=alice)
        ],
    )
    post[alice] = Account(nonce=1, code=marker)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=codes_present,
                        codes_absent=[marker],
                    )
                ),
            )
        ],
        post=post,
    )


@pytest.mark.parametrize(
    "order",
    ["earlier_tx", "same_tx_sender", "same_tx_authorization"],
)
def test_witness_codes_marker_read_before_same_delegation_is_set(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    order: str,
) -> None:
    """
    Bob's pre-state marker is read before alice gets the same marker.

    A write cannot serve an earlier read, so the marker IS in
    executionWitness.codes although the block later writes the same
    bytes. This is the delegation counterpart of
    test_witness_keeps_prestate_code_read_even_if_later_created_with_same_hash.
    """
    delegate = pre.deploy_contract(code=SHARED_DELEGATE_CODE)
    marker = Spec7702.delegation_designation(delegate)
    alice = pre.fund_eoa(amount=0)
    bob = pre.fund_eoa(delegation=delegate)
    alice_auth = AuthorizationTuple(address=delegate, nonce=0, signer=alice)

    if order == "earlier_tx":
        txs = [
            Transaction(sender=bob, to=pre.fund_eoa()),
            Transaction(
                sender=pre.fund_eoa(),
                to=pre.fund_eoa(),
                authorization_list=[alice_auth],
            ),
        ]
        bob_post = Account(nonce=2, code=marker)
    elif order == "same_tx_sender":
        # Validation reads the sender's code before authorizations apply.
        txs = [
            Transaction(
                sender=bob,
                to=pre.fund_eoa(),
                authorization_list=[alice_auth],
            )
        ]
        bob_post = Account(nonce=2, code=marker)
    elif order == "same_tx_authorization":
        # Clearing bob's delegation reads his marker before alice's
        # authorization writes the same bytes.
        txs = [
            Transaction(
                sender=pre.fund_eoa(),
                to=pre.fund_eoa(),
                authorization_list=[
                    AuthorizationTuple(
                        address=Address(0), nonce=1, signer=bob
                    ),
                    alice_auth,
                ],
            )
        ]
        bob_post = Account(nonce=2, code=b"")
    else:
        raise ValueError(f"unknown order: {order}")

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[marker],
                    )
                ),
            )
        ],
        post={
            alice: Account(nonce=1, code=marker),
            bob: bob_post,
        },
    )


@pytest.mark.parametrize(
    "outcome",
    [
        "invalid_authorization",
        "preparation_out_of_gas",
        "preparation_exact_gas",
        "execution_reverts",
    ],
)
def test_witness_codes_delegation_same_marker_tx_outcome(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    outcome: str,
) -> None:
    """
    tx1's authorization delegating alice to bob's target may not stick.

    tx2 then reads bob's marker. Only a delegation that tx1 keeps serves
    that read: an invalid authorization writes nothing, and running out
    of gas in the top-frame preparation rolls the applied delegation
    back, so the marker IS in executionWitness.codes. A delegation
    survives a reverted execution, so the marker is NOT in codes. This is
    the delegation counterpart of
    test_witness_codes_reverted_create_same_hash_then_read.
    """
    delegate = pre.deploy_contract(code=SHARED_DELEGATE_CODE)
    marker = Spec7702.delegation_designation(delegate)
    # alice exists, so her authorization charges no NEW_ACCOUNT.
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(delegation=delegate)
    alice_auth = AuthorizationTuple(address=delegate, nonce=0, signer=alice)

    tx1_codes: list[Bytes] = []
    post: dict[Address, Account | None] = {}
    if outcome == "invalid_authorization":
        # alice's nonce is 0, so the authorization is skipped.
        tx1 = Transaction(
            sender=pre.fund_eoa(),
            to=pre.fund_eoa(),
            authorization_list=[
                AuthorizationTuple(address=delegate, nonce=1, signer=alice)
            ],
        )
        kept = False
    elif outcome in ("preparation_out_of_gas", "preparation_exact_gas"):
        # set_delegation applies alice's authorization, then the value
        # transfer to an empty recipient charges NEW_ACCOUNT. One gas
        # short, that charge runs out and the preparation rollback drops
        # the delegation; with exact gas the delegation sticks.
        recipient = pre.fund_eoa(amount=0)
        gas_limit = fork.transaction_intrinsic_cost_calculator()(
            recipient_type=RecipientType.EMPTY_ACCOUNT,
            sends_value=True,
            authorization_list_or_count=[alice_auth],
            return_cost_deducted_prior_execution=True,
        ) + fork.transaction_top_frame_gas_calculator()(
            recipient_type=RecipientType.EMPTY_ACCOUNT,
            sends_value=True,
            authorizations=[alice_auth],
        )
        kept = outcome == "preparation_exact_gas"
        if not kept:
            gas_limit -= 1
        tx1 = Transaction(
            sender=pre.fund_eoa(),
            to=recipient,
            value=1,
            gas_limit=gas_limit,
            authorization_list=[alice_auth],
        )
        post[recipient] = Account(balance=1) if kept else None
    elif outcome == "execution_reverts":
        reverter_code = Op.REVERT(0, 0)
        tx1 = Transaction(
            sender=pre.fund_eoa(),
            to=pre.deploy_contract(code=reverter_code),
            authorization_list=[alice_auth],
        )
        tx1_codes.append(Bytes(reverter_code))
        kept = True
    else:
        raise ValueError(f"unknown outcome: {outcome}")

    tx2, tx2_codes, tx2_post = _read_marker(pre, "sender", bob, marker)
    post.update(tx2_post)
    if kept:
        post[alice] = Account(nonce=1, code=marker)
        witness_codes = ExecutionWitnessCodesExpectation(
            codes_present=tx1_codes + tx2_codes,
            codes_absent=[marker],
        )
    else:
        post[alice] = Account(nonce=0, code=b"")
        witness_codes = ExecutionWitnessCodesExpectation(
            codes_present=tx1_codes + tx2_codes + [marker],
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                expected_execution_witness_codes=witness_codes,
            )
        ],
        post=post,
    )


@pytest.mark.parametrize("clear_in", ["same_tx", "later_tx"])
def test_witness_codes_delegation_same_marker_cleared_then_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    clear_in: str,
) -> None:
    """
    Alice is delegated to bob's target and cleared before bob is read.

    No account holds the written marker when bob's marker is read, but
    clearing a delegation does not drop the block's code writes, which
    are keyed by hash. bob's marker is therefore NOT in
    executionWitness.codes.
    """
    delegate = pre.deploy_contract(code=SHARED_DELEGATE_CODE)
    marker = Spec7702.delegation_designation(delegate)
    alice = pre.fund_eoa(amount=0)
    bob = pre.fund_eoa(delegation=delegate)
    set_auth = AuthorizationTuple(address=delegate, nonce=0, signer=alice)
    clear_auth = AuthorizationTuple(address=Address(0), nonce=1, signer=alice)

    if clear_in == "same_tx":
        authorization_lists = [[set_auth, clear_auth]]
    elif clear_in == "later_tx":
        authorization_lists = [[set_auth], [clear_auth]]
    else:
        raise ValueError(f"unknown clear_in: {clear_in}")
    txs = [
        Transaction(
            sender=pre.fund_eoa(),
            to=pre.fund_eoa(),
            authorization_list=authorization_list,
        )
        for authorization_list in authorization_lists
    ]
    read_tx, codes_present, post = _read_marker(pre, "sender", bob, marker)
    txs.append(read_tx)
    post[alice] = Account(nonce=2, code=b"")

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=codes_present,
                        codes_absent=[marker],
                    )
                ),
            )
        ],
        post=post,
    )
