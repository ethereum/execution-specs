"""
Verify what CREATE/CREATE2 leave behind for each constructor outcome --
success, out of gas, empty revert, revert with data, empty deploy, and an
in-init SELFDESTRUCT -- plus each call kind's result against the contract a
successful constructor deploys, and the frame-aborting RETURNDATACOPY past
an empty return buffer.

Written by Ori Pomerantz (qbzzt1@gmail.com).

Ported from:
state_tests/stCreateTest/CreateResultsFiller.yml

@manually-enhanced: Do not overwrite. The filler drove a single LLL
dispatcher that branched at run time on an ABI calldata triple, because a
static filler can only vary data, not code. Here the three axes are
parametrized, so the creator contract and the init code are generated per
case and the whole jump table, its code-copied constructor fragments, and
its hardcoded layout are gone. The created account is asserted per case,
which the filler never did.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Initcode,
    Opcodes,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Written last; proves the creator frame ran to completion.
COMPLETED = 0xC0DE

# Scratch memory, clear of the init code copied in from the calldata.
ADDRESS_MEM = 0x100
RETURN_DATA_MEM = 0x120

# Memory expansion value that guarantees an OOG
MEM_EXPANSION_OOG = 0x2FFFFFFF

# Where the created contract records that it ran, and what it writes. CALL
# runs it in its own context while CALLCODE and DELEGATECALL run it in the
# creator's, so the slot is kept clear of the creator's own observations.
EXECUTED_SLOT = 0x64
EXECUTED = 0xE0DE

# Word the `revert_data` constructor reverts with.
REVERT_WORD = 0x60A7


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.with_all_create_opcodes
@pytest.mark.with_all_call_opcodes
def test_create_results_with_call(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Opcodes,
    call_opcode: Opcodes,
) -> None:
    """
    Verify each call kind's result against a successfully created contract.

    The creator invokes what it just deployed, and where that contract's
    store lands is what separates the call kinds: its own storage for
    CALL, the creator's for CALLCODE and DELEGATECALL, nowhere at all for
    STATICCALL, which forbids the write and so fails the call outright.
    """
    deployed_code = Op.SSTORE(EXECUTED_SLOT, EXECUTED) + Op.STOP
    init_code = Initcode(deploy_code=deployed_code)

    # STATICCALL forbids that store, so the call itself fails. The rest
    # succeed and differ only in whose storage the store lands in.
    call_succeeds = call_opcode != Op.STATICCALL
    writes_to_creator = call_opcode in (Op.CALLCODE, Op.DELEGATECALL)

    st = Storage()
    factory_code = (
        Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        # The created address is only known at run time, so park it in memory.
        + Op.MSTORE(
            offset=ADDRESS_MEM,
            value=create_opcode(value=0x0, offset=0x0, size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(st.store_next(0), Op.RETURNDATASIZE)
        + Op.SSTORE(
            st.store_next(len(bytes(deployed_code))),
            Op.EXTCODESIZE(address=Op.MLOAD(offset=ADDRESS_MEM)),
        )
        + Op.SSTORE(
            st.store_next(1 if call_succeeds else 0),
            call_opcode(address=Op.MLOAD(offset=ADDRESS_MEM)),
        )
        + Op.SSTORE(st.store_next(0), Op.RETURNDATASIZE)
        + Op.SSTORE(st.store_next(COMPLETED), COMPLETED)
        + Op.STOP
    )
    creator = pre.deploy_contract(code=factory_code, storage=st.canary())

    created = compute_create_address(
        address=creator, nonce=1, initcode=init_code, opcode=create_opcode
    )

    if writes_to_creator:
        st[EXECUTED_SLOT] = EXECUTED
    post = {
        creator: Account(storage=st),
        created: Account(
            code=deployed_code,
            nonce=1,
            storage={EXECUTED_SLOT: EXECUTED}
            if call_opcode == Op.CALL
            else {},
        ),
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        data=init_code,
        state_gas_reservoir=0,
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.with_all_create_opcodes
def test_returndatacopy_after_successful_create_aborts(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Opcodes,
) -> None:
    """
    Verify that reading past the empty buffer a successful CREATE leaves
    halts the creating frame.

    A create that succeeds produces no return data, so copying a word out
    of it is an out-of-bounds read: the frame halts, every canary it was
    seeded with survives, its completion marker is never written, and the
    contract it had just created is rolled back with it.
    """
    deployed_code = Op.SSTORE(EXECUTED_SLOT, EXECUTED) + Op.STOP
    init_code = Initcode(deploy_code=deployed_code)

    st = Storage()
    factory_code = (
        Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.MSTORE(
            offset=ADDRESS_MEM,
            value=create_opcode(value=0x0, offset=0x0, size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(st.store_next(0), Op.RETURNDATASIZE)
        # Nothing past this point ever runs.
        + Op.RETURNDATACOPY(dest_offset=RETURN_DATA_MEM, offset=0x0, size=0x20)
        + Op.SSTORE(st.store_next(0), Op.MLOAD(offset=RETURN_DATA_MEM))
        + Op.SSTORE(st.store_next(COMPLETED), COMPLETED)
        + Op.STOP
    )
    creator = pre.deploy_contract(code=factory_code, storage=st.canary())

    created = compute_create_address(
        address=creator, nonce=1, initcode=init_code, opcode=create_opcode
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        data=init_code,
        state_gas_reservoir=0,
    )

    post = {
        creator: Account(storage=st.canary()),
        created: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize(
    "constructor",
    [
        "oog",
        "revert",
        "revert_data",
        "empty_deploy",
        "selfdestruct",
    ],
)
def test_create_results_without_call(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Opcodes,
    constructor: str,
) -> None:
    """
    Verify what CREATE returns and leaves behind when the constructor
    deploys nothing callable.

    The creator makes no follow-up call: it only records the create's
    return data and the code size of the address it was handed.
    """
    # What the constructor would have deployed had it got that far.
    deployed_code = Op.SSTORE(EXECUTED_SLOT, EXECUTED) + Op.STOP

    # Each outcome is a prologue in front of the code that would return
    # `deployed_code`; all of them halt before reaching it.
    prologue: Bytecode
    if constructor == "oog":
        prologue = Op.POP(Op.SHA3(offset=0x0, size=MEM_EXPANSION_OOG))
    elif constructor == "revert":
        prologue = Op.REVERT(offset=0x0, size=0x0)
    elif constructor == "revert_data":
        prologue = Op.MSTORE(offset=0x0, value=REVERT_WORD) + Op.REVERT(
            offset=0x0, size=0x20
        )
    elif constructor == "empty_deploy":
        prologue = Op.STOP
    else:
        prologue = Op.SELFDESTRUCT(address=0x0)

    init_code = Initcode(deploy_code=deployed_code, initcode_prefix=prologue)

    st = Storage()
    # Only `revert_data` leaves a return buffer to read.
    read_return_data: Bytecode = Bytecode()
    if constructor == "revert_data":
        read_return_data = Op.RETURNDATACOPY(
            dest_offset=RETURN_DATA_MEM, offset=0x0, size=0x20
        ) + Op.SSTORE(
            st.store_next(REVERT_WORD), Op.MLOAD(offset=RETURN_DATA_MEM)
        )

    factory_code = (
        Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        # The created address is only known at run time, so park it in memory.
        + Op.MSTORE(
            offset=ADDRESS_MEM,
            value=create_opcode(value=0x0, offset=0x0, size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(
            st.store_next(0x20 if constructor == "revert_data" else 0),
            Op.RETURNDATASIZE,
        )
        + read_return_data
        + Op.SSTORE(
            st.store_next(0),
            Op.EXTCODESIZE(address=Op.MLOAD(offset=ADDRESS_MEM)),
        )
        + Op.SSTORE(st.store_next(COMPLETED), COMPLETED)
        + Op.STOP
    )
    creator = pre.deploy_contract(code=factory_code, storage=st.canary())

    created = compute_create_address(
        address=creator, nonce=1, initcode=init_code, opcode=create_opcode
    )

    post = {
        creator: Account(storage=st),
        # An empty deploy leaves an account with no code; every other
        # outcome leaves nothing at all, an in-init SELFDESTRUCT included
        # (destroyed in its creation transaction per EIP-6780).
        created: Account(code=b"", nonce=1, storage={})
        if constructor == "empty_deploy"
        else Account.NONEXISTENT,
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        data=init_code,
        state_gas_reservoir=0,
    )

    state_test(pre=pre, post=post, tx=tx)
