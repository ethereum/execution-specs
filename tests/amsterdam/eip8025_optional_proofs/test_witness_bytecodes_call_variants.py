"""Witness bytecode collection for call variant opcodes."""

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
def test_witness_codes_call_existing_contract(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    call_opcode: Op,
) -> None:
    """
    Call an existing contract with each call variant.

    The target bytecode should appear in executionWitness.codes because
    all call opcodes fetch code via get_code().
    """
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    if call_opcode in (Op.CALL, Op.CALLCODE):
        caller_code = call_opcode(Op.GAS, target, 0, 0, 0, 0, 0)
    else:
        caller_code = call_opcode(Op.GAS, target, 0, 0, 0, 0)
    caller_code += Op.STOP
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
                        codes_present=[Bytes(bytes(target_code))],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_witness_codes_nested_calls(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Nested calls A -> B -> C record all three bytecodes in witness codes.

    Each call depth fetches code via get_code(), so all accessed contract
    bytecodes should appear in executionWitness.codes.
    """
    code_c = Op.PUSH1(0x01) + Op.POP + Op.STOP
    contract_c = pre.deploy_contract(code=code_c)

    code_b = Op.CALL(Op.GAS, contract_c, 0, 0, 0, 0, 0) + Op.STOP
    contract_b = pre.deploy_contract(code=code_b)

    code_a = Op.CALL(Op.GAS, contract_b, 0, 0, 0, 0, 0) + Op.STOP
    contract_a = pre.deploy_contract(code=code_a)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract_a, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(code_a)),
                            Bytes(bytes(code_b)),
                            Bytes(bytes(code_c)),
                        ],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )
