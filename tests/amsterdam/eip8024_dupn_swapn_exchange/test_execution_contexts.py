"""
Execution-context tests for EIP-8024 (DUPN, SWAPN, EXCHANGE).

Each context executes all three opcodes, each moving a distinct planted
marker to the top of the stack. Every snippet plants its marker relative
to the current stack top, so the snippets compose regardless of items
left behind by earlier ones.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    EIPChecklist,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("EIP8024")

DUPN_MARKER = 0xA1
SWAPN_MARKER = 0xB2
EXCHANGE_MARKER = 0xC3

EXPECTED_STORAGE = {
    0: DUPN_MARKER,
    1: SWAPN_MARKER,
    2: EXCHANGE_MARKER,
}


def stack_access_storage_code() -> Bytecode:
    """Store each opcode's moved marker at storage keys 0, 1 and 2."""
    return (
        Op.PUSH1(DUPN_MARKER)
        + Op.PUSH0 * 16
        + Op.DUPN[17]
        + Op.PUSH1(0)
        + Op.SSTORE
        + Op.PUSH1(SWAPN_MARKER)
        + Op.PUSH0 * 17
        + Op.SWAPN[17]
        + Op.PUSH1(1)
        + Op.SSTORE
        + Op.PUSH1(EXCHANGE_MARKER)
        + Op.PUSH0 * 2
        + Op.EXCHANGE[1, 2]
        + Op.POP
        + Op.PUSH1(2)
        + Op.SSTORE
        + Op.STOP
    )


def stack_access_memory_code() -> Bytecode:
    """
    Write each opcode's moved marker to memory and return 96 bytes.

    Storage-free, so the code also runs inside STATICCALL frames.
    """
    return (
        Op.PUSH1(DUPN_MARKER)
        + Op.PUSH0 * 16
        + Op.DUPN[17]
        + Op.PUSH1(0)
        + Op.MSTORE
        + Op.PUSH1(SWAPN_MARKER)
        + Op.PUSH0 * 17
        + Op.SWAPN[17]
        + Op.PUSH1(32)
        + Op.MSTORE
        + Op.PUSH1(EXCHANGE_MARKER)
        + Op.PUSH0 * 2
        + Op.EXCHANGE[1, 2]
        + Op.POP
        + Op.PUSH1(64)
        + Op.MSTORE
        + Op.RETURN(0, 96)
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Call()
@EIPChecklist.Opcode.Test.ExecutionContext.Callcode()
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall()
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall()
@pytest.mark.with_all_call_opcodes
def test_stack_access_call_contexts(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Test DUPN, SWAPN and EXCHANGE in every call frame type.

    The callee returns each opcode's result through memory, so the check
    also holds inside STATICCALL frames where storage writes are banned.
    The caller stores the call's success flag and the returned markers.
    """
    callee_address = pre.deploy_contract(stack_access_memory_code())

    caller_code = (
        Op.SSTORE(
            0,
            call_opcode(address=callee_address, ret_offset=0, ret_size=96),
        )
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.SSTORE(2, Op.MLOAD(32))
        + Op.SSTORE(3, Op.MLOAD(64))
    )
    caller_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
    )

    post = {
        caller_address: Account(
            storage={
                0: 1,
                1: DUPN_MARKER,
                2: SWAPN_MARKER,
                3: EXCHANGE_MARKER,
            },
        ),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.Opcode.Test.ExecutionContext.SetCode()
def test_stack_access_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test DUPN, SWAPN and EXCHANGE inside a set-code delegated account
    (EIP-7702).
    """
    auth_signer = pre.fund_eoa(amount=0)
    set_code_to_address = pre.deploy_contract(stack_access_storage_code())

    tx = Transaction(
        to=auth_signer,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    post = {
        set_code_to_address: Account(storage={}),
        auth_signer: Account(
            nonce=1,
            code=Spec7702.delegation_designation(set_code_to_address),
            storage=EXPECTED_STORAGE,
        ),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Tx()
def test_stack_access_initcode_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test DUPN, SWAPN and EXCHANGE inside the initcode of a
    contract-creating transaction.
    """
    init_code = stack_access_storage_code()
    sender = pre.fund_eoa()
    contract_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(to=None, data=init_code, sender=sender)

    post = {
        contract_address: Account(storage=EXPECTED_STORAGE),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Opcode()
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
def test_stack_access_initcode_create(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test DUPN, SWAPN and EXCHANGE inside initcode executed via CREATE
    and CREATE2.
    """
    init_code = stack_access_storage_code()

    factory_code = (
        Op.CALLDATACOPY(offset=0, size=len(init_code))
        + opcode(offset=0, size=len(init_code))
        + Op.STOP
    )
    factory_address = pre.deploy_contract(factory_code)

    created_contract_address = compute_create_address(
        address=factory_address,
        nonce=1,
        initcode=init_code,
        opcode=opcode,
    )

    tx = Transaction(
        to=factory_address,
        data=init_code,
        sender=pre.fund_eoa(),
    )

    post = {
        created_contract_address: Account(storage=EXPECTED_STORAGE),
    }

    state_test(pre=pre, tx=tx, post=post)
