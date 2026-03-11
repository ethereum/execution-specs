"""Witness bytecode scenarios for EIP-7702 delegation."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Op,
    Transaction,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


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

    caller_code = (
        call_opcode(address=delegated_eoa) + Op.STOP
    )
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
                            Bytes(marker),
                            Bytes(bytes(delegate_code)),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
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
                            Bytes(bytes(delegate_code)),
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
                            Bytes(bytes(delegate_code)),
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

