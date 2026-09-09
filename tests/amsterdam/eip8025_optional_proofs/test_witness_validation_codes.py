"""Execution witness code validation tests."""

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
from execution_testing.test_types.execution_witness.modifiers import (
    add_code,
    remove_code,
    remove_code_at,
    reverse_codes,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_validation_codes_missing_current_frame_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the currently executing contract's code should fail."""
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    caller_code = Op.EXTCODESIZE(target) + Op.POP + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)
    caller_code_bytes = Bytes(bytes(caller_code))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            caller_code_bytes,
                            Bytes(bytes(target_code)),
                        ],
                    ).modify(remove_code(caller_code_bytes))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={sender: Account(nonce=1)},
    )


def test_validation_codes_missing_external_code_read_target(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing externally read code should fail guest execution."""
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    caller_code = Op.EXTCODECOPY(target, 0, 0, 32) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)
    target_code_bytes = Bytes(bytes(target_code))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(caller_code)),
                            target_code_bytes,
                        ],
                    ).modify(remove_code(target_code_bytes))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={sender: Account(nonce=1)},
    )


def test_validation_codes_missing_implicit_system_contract_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Removing implicit system-contract code from an empty block should fail.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation().modify(
                        remove_code_at(0)
                    )
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={},
    )


def test_validation_codes_missing_7702_delegation_marker(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing a pre-state 7702 delegation marker should fail."""
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_eoa = pre.fund_eoa(delegation=delegate)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=delegated_eoa,
        gas_limit=500_000,
    )

    marker = Bytes(Spec7702.delegation_designation(delegate))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            marker,
                            Bytes(bytes(delegate_code)),
                        ],
                    ).modify(remove_code(marker))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={sender: Account(nonce=1)},
    )


def test_validation_codes_missing_7702_delegated_target_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing delegated target code from a 7702 flow should fail."""
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    delegated_eoa = pre.fund_eoa(delegation=delegate)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=delegated_eoa,
        gas_limit=500_000,
    )

    delegate_code_bytes = Bytes(bytes(delegate_code))
    marker = Bytes(Spec7702.delegation_designation(delegate))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            marker,
                            delegate_code_bytes,
                        ],
                    ).modify(remove_code(delegate_code_bytes))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={sender: Account(nonce=1)},
    )


def test_validation_codes_missing_sender_delegation_marker(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the sender's delegation marker should fail."""
    delegate = pre.deploy_contract(code=Op.STOP)
    delegated_sender = pre.fund_eoa(delegation=delegate)

    recipient = pre.fund_eoa()
    tx = Transaction(
        sender=delegated_sender,
        to=recipient,
        gas_limit=500_000,
    )

    marker = Bytes(Spec7702.delegation_designation(delegate))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[marker],
                    ).modify(remove_code(marker))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={delegated_sender: Account(nonce=2)},
    )


def test_validation_codes_missing_redelegation_old_marker(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the old marker read during re-delegation should fail."""
    delegate_old = pre.deploy_contract(code=Op.PUSH1(0x01) + Op.POP + Op.STOP)
    delegate_new = pre.deploy_contract(code=Op.PUSH1(0x02) + Op.POP + Op.STOP)

    alice = pre.fund_eoa(delegation=delegate_old)
    relayer = pre.fund_eoa()
    recipient = pre.fund_eoa()

    old_marker = Bytes(Spec7702.delegation_designation(delegate_old))
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
                        codes_present=[old_marker],
                        codes_absent=[Bytes(new_marker)],
                    ).modify(remove_code(old_marker))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            alice: Account(
                nonce=2,
                code=new_marker,
            ),
        },
    )


def test_validation_codes_missing_delegated_code_on_insufficient_balance_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing delegated code on an insufficient-balance CALL should fail."""
    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)
    delegated_eoa = pre.fund_eoa(amount=0, delegation=delegate)

    caller_balance = 100
    transfer_value = 1_000
    caller_code = (
        Op.SSTORE(
            0,
            Op.CALL(
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

    delegate_code_bytes = Bytes(bytes(delegate_code))
    marker = Bytes(Spec7702.delegation_designation(delegate))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(caller_code)),
                            marker,
                            delegate_code_bytes,
                        ],
                    ).modify(remove_code(delegate_code_bytes))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            caller: Account(balance=caller_balance, storage={0: 0}),
        },
    )


def test_validation_codes_missing_second_marker_in_delegation_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the second marker in a delegation chain should fail."""
    charlie_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    charlie = pre.deploy_contract(code=charlie_code)

    bob = pre.fund_eoa(delegation=charlie)
    alice = pre.fund_eoa(delegation=bob)

    caller_code = Op.CALL(address=alice) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    marker_alice = Bytes(Spec7702.delegation_designation(bob))
    marker_bob = Bytes(Spec7702.delegation_designation(charlie))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(caller_code)),
                            marker_alice,
                            marker_bob,
                        ],
                        codes_absent=[
                            Bytes(bytes(charlie_code)),
                        ],
                    ).modify(remove_code(marker_bob))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={sender: Account(nonce=1)},
    )


def test_validation_codes_extra_unused_bytecode(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Adding an unused bytecode preimage should still validate."""
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    caller_code = Op.EXTCODECOPY(target, 0, 0, 32) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    unused_code = Bytes(bytes(Op.PUSH1(0x99) + Op.PUSH1(0x01) + Op.STOP))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(caller_code)),
                            Bytes(bytes(target_code)),
                        ],
                    ).modify(add_code(unused_code))
                ),
                expected_stateless_validation_success=True,
            )
        ],
        post={sender: Account(nonce=1)},
    )


def test_validation_codes_unsorted_but_complete(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Reordering complete witness codes should still validate."""
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    caller_code = Op.EXTCODECOPY(target, 0, 0, 32) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(caller_code)),
                            Bytes(bytes(target_code)),
                        ],
                    ).modify(reverse_codes())
                ),
                expected_stateless_validation_success=True,
            )
        ],
        post={sender: Account(nonce=1)},
    )
