"""Execution witness code validation tests."""

from typing import Callable

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
from execution_testing.test_types.execution_witness import ExecutionWitness
from execution_testing.test_types.execution_witness.modifiers import (
    add_code,
    remove_code,
    remove_code_at,
    reverse_codes,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8025

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


@pytest.mark.parametrize(
    "extcode_opcode,removed_code",
    [
        pytest.param("extcodesize", "caller", id="current_frame_code"),
        pytest.param("extcodecopy", "target", id="external_code_read_target"),
    ],
)
def test_validation_codes_missing_read_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    extcode_opcode: str,
    removed_code: str,
) -> None:
    """
    Removing the executing contract's code, or code it reads externally,
    should fail guest execution.
    """
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    if extcode_opcode == "extcodesize":
        access = Op.EXTCODESIZE(target) + Op.POP
    elif extcode_opcode == "extcodecopy":
        access = Op.EXTCODECOPY(target, 0, 0, 32)
    else:
        raise ValueError(f"unknown EXTCODE* opcode: {extcode_opcode}")
    caller_code = access + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)
    codes = {"caller": Bytes(caller_code), "target": Bytes(target_code)}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=list(codes.values()),
                    ).modify(remove_code(codes[removed_code]))
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


@pytest.mark.parametrize(
    "removed_code",
    [
        pytest.param("marker", id="delegation_marker"),
        pytest.param("delegate", id="delegated_target_code"),
    ],
)
def test_validation_codes_missing_7702_delegation_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    removed_code: str,
) -> None:
    """
    Removing a pre-state 7702 delegation marker, or the delegated target
    code, should fail.
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

    codes = {
        "marker": Bytes(Spec7702.delegation_designation(delegate)),
        "delegate": Bytes(delegate_code),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=list(codes.values()),
                    ).modify(remove_code(codes[removed_code]))
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

    delegate_code_bytes = Bytes(delegate_code)
    marker = Bytes(Spec7702.delegation_designation(delegate))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(caller_code),
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
                            Bytes(caller_code),
                            marker_alice,
                            marker_bob,
                        ],
                        codes_absent=[
                            Bytes(charlie_code),
                        ],
                    ).modify(remove_code(marker_bob))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={sender: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(
            add_code(Bytes(Op.PUSH1(0x99) + Op.PUSH1(0x01) + Op.STOP)),
            id="extra_unused_bytecode",
        ),
        pytest.param(reverse_codes(), id="unsorted_but_complete"),
    ],
)
def test_validation_codes_complete_witness_still_validates(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    modifier: Callable[[ExecutionWitness], ExecutionWitness],
) -> None:
    """
    Adding an unused bytecode preimage or reordering complete witness codes
    should still validate.
    """
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
                            Bytes(caller_code),
                            Bytes(target_code),
                        ],
                    ).modify(modifier)
                ),
                expected_stateless_validation_success=True,
            )
        ],
        post={sender: Account(nonce=1)},
    )
