"""Execution witness code soundness tests."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Op,
    Transaction,
)
from execution_testing.test_types.execution_witness.modifiers import (
    remove_code,
    remove_code_at,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_soundness_codes_missing_current_frame_code(
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


def test_soundness_codes_missing_external_code_read_target(
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


def test_soundness_codes_missing_implicit_system_contract_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing implicit system-contract code from an empty block should fail."""
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


def test_soundness_codes_missing_7702_delegation_marker(
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


def test_soundness_codes_missing_7702_delegated_target_code(
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
