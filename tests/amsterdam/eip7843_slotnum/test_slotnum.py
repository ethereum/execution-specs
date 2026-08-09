"""Tests for EIP-7843 (SLOTNUM)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version

pytestmark = pytest.mark.valid_from("EIP7843")


@EIPChecklist.Opcode.Test.GasUsage.ExtraGas()
@pytest.mark.parametrize(
    "slot_number",
    [
        pytest.param(0, id="slot_zero"),
        pytest.param(1, id="slot_one"),
        pytest.param(0x1000, id="slot_4096"),
        pytest.param(2**32, id="slot_large"),
        pytest.param(2**64 - 1, id="slot_max_u64"),
    ],
)
def test_slotnum_value(
    state_test: StateTestFiller,
    pre: Alloc,
    slot_number: int,
) -> None:
    """
    Test that SLOTNUM opcode returns the correct slot number.

    The slot number is provided by the consensus layer and should be
    accessible via the SLOTNUM opcode (0x4B).

    Storage key 0 starts at a nonzero canary so the zero-slot case is
    distinguishable from a transaction that failed before the SSTORE.
    """
    # Store SLOTNUM result at storage key 0
    code = Op.SSTORE(0, Op.SLOTNUM)
    code_address = pre.deploy_contract(code, storage={0: 0xBA5E})

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
    )

    post = {
        code_address: Account(
            storage={0: slot_number},
        ),
    }

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post=post,
    )


@EIPChecklist.Opcode.Test.GasUsage.Normal()
@EIPChecklist.Opcode.Test.GasUsage.OutOfGasExecution()
@pytest.mark.parametrize(
    "gas_delta,call_succeeds",
    [
        pytest.param(0, True, id="enough_gas"),
        pytest.param(-1, False, id="out_of_gas"),
    ],
)
def test_slotnum_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test that SLOTNUM opcode costs exactly 2 gas (G_BASE).
    """
    slotnum_gas = Op.SLOTNUM.gas_cost(fork)
    call_gas = slotnum_gas + gas_delta

    # Callee just executes SLOTNUM
    callee_code = Op.SLOTNUM + Op.STOP
    callee_address = pre.deterministic_deploy_contract(deploy_code=callee_code)

    # Caller calls the callee with limited gas and stores result
    caller_code = Op.SSTORE(0, Op.CALL(gas=call_gas, address=callee_address))
    caller_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
    )

    post = {
        caller_address: Account(
            storage={0: 1 if call_succeeds else 0},
        ),
    }

    state_test(
        env=Environment(slot_number=12345),
        pre=pre,
        tx=tx,
        post=post,
    )


@EIPChecklist.Opcode.Test.ExecutionContext.BlockContext()
@EIPChecklist.BlockHeaderField.Test.ValueBehavior.Accept()
def test_slotnum_distinct_per_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that SLOTNUM returns each block's own slot number.

    Runs four consecutive blocks with deliberately non-monotonic slot
    numbers to disprove any caching or ordering assumption in the opcode
    implementation. Each block runs the same contract, which keys storage
    by block ``NUMBER`` so every block's outcome is independently visible
    in the final post-state.
    """
    sender = pre.fund_eoa()
    contract = pre.deploy_contract(Op.SSTORE(Op.NUMBER, Op.SLOTNUM) + Op.STOP)

    # Non-monotonic on purpose: decrease, increase, jump to large value.
    slot_numbers = [100, 42, 7, 2**32]

    blocks = [
        Block(
            slot_number=slot,
            txs=[Transaction(sender=sender, to=contract)],
        )
        for slot in slot_numbers
    ]

    post = {
        contract: Account(
            storage={i + 1: slot for i, slot in enumerate(slot_numbers)},
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.BlockHeaderField.Test.Genesis()
def test_slotnum_genesis(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that the slot number header field can be set at genesis.

    The genesis header of this fixture carries a nonzero `slot_number`,
    so a client must decode the field to reproduce the genesis hash.
    The following block then exposes its own slot number via SLOTNUM.
    """
    genesis_slot = 999
    block_slot = 1000

    contract = pre.deploy_contract(
        Op.SSTORE(0, Op.SLOTNUM), storage={0: 0xBA5E}
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    blockchain_test(
        genesis_environment=Environment(slot_number=genesis_slot),
        pre=pre,
        blocks=[Block(slot_number=block_slot, txs=[tx])],
        post={contract: Account(storage={0: block_slot})},
    )


@EIPChecklist.Opcode.Test.StackOverflow()
@EIPChecklist.Opcode.Test.ExceptionalAbort()
@pytest.mark.parametrize(
    "push_count,call_succeeds",
    [
        pytest.param(1024, True, id="stack_at_limit"),
        pytest.param(1025, False, id="stack_overflow"),
    ],
)
def test_slotnum_stack_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    push_count: int,
    call_succeeds: bool,
) -> None:
    """
    Test that SLOTNUM aborts when pushing past the 1024-item stack limit.

    The callee executes `push_count` consecutive SLOTNUM opcodes: 1024
    pushes fill the stack exactly and succeed, while the 1025th push
    aborts the frame exceptionally. The caller stores the call's success
    flag over a nonzero canary.
    """
    callee_code = Op.SLOTNUM * push_count + Op.STOP
    callee_address = pre.deploy_contract(callee_code)

    caller_code = Op.SSTORE(0, Op.CALL(gas=Op.GAS, address=callee_address))
    caller_address = pre.deploy_contract(caller_code, storage={0: 0xBA5E})

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
    )

    post = {
        caller_address: Account(
            storage={0: 1 if call_succeeds else 0},
        ),
    }

    state_test(
        env=Environment(slot_number=12345),
        pre=pre,
        tx=tx,
        post=post,
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Call()
@EIPChecklist.Opcode.Test.ExecutionContext.Callcode()
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall()
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall()
@pytest.mark.with_all_call_opcodes
def test_slotnum_call_contexts(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Test that SLOTNUM returns the slot number in every call frame type.

    The callee writes SLOTNUM to memory and returns it, so the check
    also holds inside STATICCALL frames where storage writes are banned.
    The caller stores the call's success flag and the returned value.
    """
    slot_number = 0xC0FFEE

    callee_code = Op.MSTORE(0, Op.SLOTNUM) + Op.RETURN(0, 32)
    callee_address = pre.deploy_contract(callee_code)

    caller_code = Op.SSTORE(
        0, call_opcode(address=callee_address, ret_offset=0, ret_size=32)
    ) + Op.SSTORE(1, Op.MLOAD(0))
    caller_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
    )

    post = {
        caller_address: Account(
            storage={0: 1, 1: slot_number},
        ),
    }

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post=post,
    )


@EIPChecklist.Opcode.Test.ExecutionContext.SetCode()
def test_slotnum_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SLOTNUM inside a set-code delegated account (EIP-7702).
    """
    slot_number = 0xC0FFEE

    auth_signer = pre.fund_eoa(amount=0)
    set_code = Op.SSTORE(0, Op.SLOTNUM) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

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
            storage={0: slot_number},
        ),
    }

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post=post,
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Tx()
def test_slotnum_initcode_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SLOTNUM inside the initcode of a contract-creating transaction.
    """
    slot_number = 0xC0FFEE

    init_code = Op.SSTORE(0, Op.SLOTNUM)
    sender = pre.fund_eoa()
    contract_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(to=None, data=init_code, sender=sender)

    post = {
        contract_address: Account(storage={0: slot_number}),
    }

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post=post,
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Opcode()
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
def test_slotnum_initcode_create(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test SLOTNUM inside initcode executed via CREATE and CREATE2.
    """
    slot_number = 0xC0FFEE

    init_code = Op.SSTORE(0, Op.SLOTNUM)

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
        created_contract_address: Account(storage={0: slot_number}),
    }

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post=post,
    )
