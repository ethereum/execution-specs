"""Witness bytecode collection for SELFDESTRUCT."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_codes_selfdestruct(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Contract executing SELFDESTRUCT has its code in witness.

    The beneficiary is a contract whose code must NOT appear in the
    witness because SELFDESTRUCT does not call get_code on the
    beneficiary.
    """
    sender = pre.fund_eoa()

    beneficiary_code = Op.PUSH1(0xAA) + Op.POP + Op.STOP
    beneficiary = pre.deploy_contract(code=beneficiary_code)

    target_balance = 1
    target_code = Op.PUSH20(beneficiary) + Op.SELFDESTRUCT
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    caller_code = Op.CALL(Op.GAS, target, 0, 0, 0, 0, 0) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

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
                        codes_absent=[Bytes(bytes(beneficiary_code))],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            beneficiary: Account(balance=target_balance),
            target: Account(balance=0, code=target_code),
        },
    )


def test_witness_codes_selfdestruct_top_level_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Top-level transaction to a selfdestructing contract.

    The target bytecode should appear in the witness, the beneficiary's
    bytecode should not, and the beneficiary must receive the target's
    balance to prove SELFDESTRUCT actually executed.
    """
    sender = pre.fund_eoa()

    beneficiary_code = Op.PUSH1(0xBB) + Op.POP + Op.STOP
    beneficiary = pre.deploy_contract(code=beneficiary_code)

    target_balance = 1
    target_code = Op.PUSH20(beneficiary) + Op.SELFDESTRUCT
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    tx = Transaction(sender=sender, to=target, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(target_code)),
                        ],
                        codes_absent=[Bytes(bytes(beneficiary_code))],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            beneficiary: Account(balance=target_balance),
            target: Account(balance=0, code=target_code),
        },
    )


def test_witness_codes_create_then_selfdestruct_same_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Factory CREATEs a contract then CALLs it; created contract SELFDESTRUCTs.

    The created contract was added to created_accounts by CREATE, so
    SELFDESTRUCT actually deletes the account (EIP-6780). Its runtime
    code should NOT appear in executionWitness.codes because get_code()
    returned it from tx-local code_writes, never from pre-state.
    The factory's code IS in the witness.
    """
    runtime_code = bytes(Op.PUSH0 + Op.SELFDESTRUCT)
    initcode = Initcode(deploy_code=runtime_code)
    initcode_bytes = bytes(initcode)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(initcode_bytes))
        + Op.SSTORE(
            0,
            Op.CREATE(
                offset=32 - len(initcode_bytes),
                size=len(initcode_bytes),
            ),
        )
        + Op.CALL(address=Op.SLOAD(0))
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code, balance=10**18)
    sender = pre.fund_eoa()

    created = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=sender, to=factory, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(factory_code)),
                        ],
                        codes_absent=[
                            Bytes(runtime_code),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            created: Account.NONEXISTENT,
            factory: Account(storage={0: created}),
        },
    )


def test_witness_codes_selfdestruct_in_initcode(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Initcode that executes SELFDESTRUCT during contract creation.

    The initcode comes from tx data and must not appear in the witness.
    The beneficiary's code must also stay out of the witness, while the
    beneficiary balance change proves SELFDESTRUCT executed.
    """
    creator = pre.fund_eoa()

    beneficiary_code = Op.PUSH1(0xCC) + Op.POP + Op.STOP
    beneficiary = pre.deploy_contract(code=beneficiary_code)

    tx_value = 7
    initcode = bytes(Op.PUSH20(beneficiary) + Op.SELFDESTRUCT)
    created = compute_create_address(address=creator, nonce=0)

    tx = Transaction(
        sender=creator,
        to=None,
        data=initcode,
        value=tx_value,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_absent=[
                            Bytes(initcode),
                            Bytes(bytes(beneficiary_code)),
                        ],
                    )
                ),
            )
        ],
        post={
            creator: Account(nonce=1),
            beneficiary: Account(balance=tx_value),
            created: Account.NONEXISTENT,
        },
    )


def test_witness_codes_selfdestruct_beneficiary_delegated_eoa(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    SELFDESTRUCT with a 7702 delegated EOA as beneficiary.

    SELFDESTRUCT does not call get_code() on the beneficiary, so the
    delegation marker and the delegate's bytecode must NOT appear in
    executionWitness.codes.
    """
    sender = pre.fund_eoa()

    delegate_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    delegate = pre.deploy_contract(code=delegate_code)

    beneficiary_initial_balance = 1
    beneficiary = pre.fund_eoa(
        amount=beneficiary_initial_balance,
        delegation=delegate,
    )
    marker = Spec7702.delegation_designation(delegate)

    target_balance = 1
    target_code = Op.PUSH20(beneficiary) + Op.SELFDESTRUCT
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    caller_code = Op.CALL(Op.GAS, target, 0, 0, 0, 0, 0) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

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
                        codes_absent=[
                            Bytes(marker),
                            Bytes(bytes(delegate_code)),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            beneficiary: Account(
                balance=beneficiary_initial_balance + target_balance
            ),
            target: Account(balance=0, code=target_code),
        },
    )


@pytest.mark.parametrize(
    "beneficiary_type",
    [
        pytest.param("eoa", id="eoa"),
        pytest.param("nonexistent", id="nonexistent"),
    ],
)
def test_witness_codes_selfdestruct_beneficiary_no_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    beneficiary_type: str,
) -> None:
    """
    SELFDESTRUCT where beneficiary has no code (EOA or nonexistent).

    Only system contract bytecodes, the caller's code, and the
    target's code should appear in executionWitness.codes. Nothing
    else should leak into the witness.
    """
    sender = pre.fund_eoa()

    target_balance = 1
    beneficiary: Address
    if beneficiary_type == "eoa":
        beneficiary_initial_balance = 1
        beneficiary = pre.fund_eoa(amount=beneficiary_initial_balance)
    else:
        beneficiary_initial_balance = 0
        beneficiary = Address(0xDEAD)

    target_code = Op.PUSH20(beneficiary) + Op.SELFDESTRUCT
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    caller_code = Op.CALL(Op.GAS, target, 0, 0, 0, 0, 0) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

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
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            beneficiary: Account(
                balance=beneficiary_initial_balance + target_balance
            ),
            target: Account(balance=0, code=target_code),
        },
    )
