"""Test `SETCODEFROM` across call contexts, initcode and system calls."""

from typing import Iterator

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Conditional,
    EIPChecklist,
    Fork,
    GasConsumer,
    Hash,
    Initcode,
    Op,
    ParameterSet,
    StateTestFiller,
    SystemCallPhase,
    Transaction,
    compute_create_address,
)

from ...cancun.eip4788_beacon_root.spec import Spec as BeaconSpec
from .helpers import (
    ADOPT_FROM_CALLDATA,
    MARKER_A,
    MARKER_B,
    MARKER_SLOT,
    RESULT_SLOT,
    REVERT_WITH_CODE_HASH,
    SENTINEL,
    SSTORE_MARKER_A,
    SSTORE_MARKER_B,
    adopt_code,
    adoption,
    call_with,
    word,
)
from .spec import ref_spec_8298

REFERENCE_SPEC_GIT_PATH = ref_spec_8298.git_path
REFERENCE_SPEC_VERSION = ref_spec_8298.version

pytestmark = pytest.mark.valid_from("EIP8298")


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode != Op.STATICCALL
)
@EIPChecklist.Opcode.Test.ExecutionContext.Call()
@EIPChecklist.Opcode.Test.ExecutionContext.Callcode()
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall()
def test_call_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """Verify the current account, not the code owner, adopts the source."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    callee_code = adopt_code()
    callee = pre.deploy_contract(callee_code)
    caller_code = (
        Op.SSTORE(
            RESULT_SLOT, call_with(callee, template, call_opcode=call_opcode)
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(caller_code, storage={RESULT_SLOT: SENTINEL})
    if call_opcode == Op.CALL:
        adopter = callee
        post = {
            caller: Account(code=caller_code, storage={RESULT_SLOT: 1}),
            callee: Account(code=SSTORE_MARKER_A),
        }
    elif call_opcode in (Op.CALLCODE, Op.DELEGATECALL):
        adopter = caller
        post = {
            caller: Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1}),
            callee: Account(code=callee_code),
        }
    else:
        raise ValueError(f"unexpected call opcode: {call_opcode}")
    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=caller),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                template: BalAccountExpectation.empty(),
                adopter: BalAccountExpectation(
                    code_changes=adoption(1, SSTORE_MARKER_A)
                ),
            }
        ),
    )


STATIC = EIPChecklist.Opcode.Test.ExecutionContext.Staticcall


@pytest.mark.parametrize(
    "source_kind",
    [
        pytest.param("valid", marks=STATIC.BanCheck()),
        pytest.param("same_hash", marks=STATIC.BanNoModification()),
        pytest.param("nonexistent", marks=STATIC.BanNoModification()),
    ],
)
@EIPChecklist.Opcode.Test.ExceptionalAbort()
@STATIC()
def test_static_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    source_kind: str,
) -> None:
    """Verify `SETCODEFROM` halts in a static context before reading source."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    adopter_code = adopt_code()
    if source_kind == "valid":
        source = template
    elif source_kind == "same_hash":
        source = pre.deploy_contract(adopter_code)
    elif source_kind == "nonexistent":
        source = pre.nonexistent_account()
    else:
        raise ValueError(f"unexpected source kind: {source_kind}")
    adopter = pre.deploy_contract(adopter_code)
    driver = pre.deploy_contract(
        Op.SSTORE(
            RESULT_SLOT,
            call_with(adopter, source, call_opcode=Op.STATICCALL),
        )
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )
    state_test(
        pre=pre,
        post={
            driver: Account(storage={RESULT_SLOT: 0}),
            adopter: Account(code=adopter_code),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=driver),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={source: None}
        ),
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.SubCalls()
def test_static_propagates_through_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a DELEGATECALL under STATICCALL still cannot adopt."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    lib = pre.deploy_contract(adopt_code())
    middle_code = (
        Op.CALLDATACOPY(0, 0, 32)
        + Op.MSTORE(0, Op.DELEGATECALL(address=lib, args_size=32))
        + Op.RETURN(0, 32)
    )
    middle = pre.deploy_contract(middle_code)
    # Slot 1 holds the inner DELEGATECALL result that `middle` returns.
    driver = pre.deploy_contract(
        Op.SSTORE(
            RESULT_SLOT,
            call_with(
                middle, template, call_opcode=Op.STATICCALL, ret_size=32
            ),
        )
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL, 1: SENTINEL},
    )
    state_test(
        pre=pre,
        post={
            driver: Account(storage={RESULT_SLOT: 1, 1: 0}),
            middle: Account(code=middle_code),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=driver),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={template: None}
        ),
    )


@pytest.mark.with_all_contract_creating_tx_types
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Tx()
def test_initcode_creation_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
) -> None:
    """Verify a creation tx's initcode adopts instead of depositing code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=None,
        data=Op.SSTORE(0, Op.SETCODEFROM(template)) + Op.STOP,
    )
    created = tx.created_contract
    state_test(
        pre=pre,
        post={created: Account(code=SSTORE_MARKER_A, storage={0: 1}, nonce=1)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                created: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=adoption(1, SSTORE_MARKER_A),
                ),
                template: BalAccountExpectation.empty(),
            }
        ),
    )


@pytest.mark.with_all_create_opcodes
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Opcode()
def test_initcode_create_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """Verify CREATE/CREATE2 initcode adopts instead of depositing code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode = Op.SSTORE(0, Op.SETCODEFROM(template)) + Op.STOP
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, create_opcode(offset=0, size=Op.CALLDATASIZE))
        + Op.STOP
    )
    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )
    state_test(
        pre=pre,
        post={
            factory: Account(storage={0: created}, nonce=2),
            created: Account(code=SSTORE_MARKER_A, storage={0: 1}, nonce=1),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=factory, data=initcode),
    )


def self_inspection(
    template: Address,
) -> tuple[Bytecode, dict[int, int | Hash]]:
    """
    Return initcode that adopts `template` (`SSTORE_MARKER_A`) and stores
    what `EXTCODE*` and `CODE*` show of the new account, and that storage.
    """
    initcode = (
        Op.POP(Op.SETCODEFROM(template))
        + Op.SSTORE(0, Op.EXTCODEHASH(Op.ADDRESS))
        + Op.SSTORE(1, Op.EXTCODESIZE(Op.ADDRESS))
        + Op.EXTCODECOPY(Op.ADDRESS, 0, 0, 32)
        + Op.SSTORE(2, Op.MLOAD(0))
        + Op.SSTORE(3, Op.CODESIZE)
        + Op.CODECOPY(32, 0, 32)
        + Op.SSTORE(4, Op.MLOAD(32))
        + Op.STOP
    )
    storage: dict[int, int | Hash] = {
        0: SSTORE_MARKER_A.keccak256(),
        1: len(SSTORE_MARKER_A),
        2: Hash(bytes(SSTORE_MARKER_A)[:32], right_padding=True),
        3: len(initcode),
        4: Hash(bytes(initcode)[:32], right_padding=True),
    }
    return initcode, storage


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
def test_initcode_self_inspection(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify EXTCODE* see adopted code and CODE* see the initcode."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode, storage = self_inspection(template)
    tx = Transaction(sender=pre.fund_eoa(), to=None, data=initcode)
    state_test(
        pre=pre,
        post={
            tx.created_contract: Account(code=SSTORE_MARKER_A, storage=storage)
        },
        tx=tx,
    )


@pytest.mark.with_all_create_opcodes
def test_initcode_self_inspection_create_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """
    Verify EXTCODE* see adopted code and CODE* see the initcode in
    CREATE/CREATE2 initcode.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode, storage = self_inspection(template)
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(create_opcode(offset=0, size=Op.CALLDATASIZE))
        + Op.STOP
    )
    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )
    state_test(
        pre=pre,
        post={created: Account(code=SSTORE_MARKER_A, storage=storage)},
        tx=Transaction(sender=pre.fund_eoa(), to=factory, data=initcode),
    )


@pytest.mark.parametrize(
    "payload", ["ef_prefixed", "over_max_code_size", "template_b_code"]
)
def test_initcode_return_data_ignored(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    payload: str,
) -> None:
    """Verify return data is ignored once initcode has adopted code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    adopt = Op.SSTORE(0, Op.SETCODEFROM(template))
    initcode: Bytecode
    if payload == "ef_prefixed":
        initcode = Initcode(
            initcode_prefix=adopt, deploy_code=b"\xef" + bytes(31)
        )
    elif payload == "over_max_code_size":
        initcode = adopt + Op.RETURN(0, fork.max_code_size() + 1)
    elif payload == "template_b_code":
        initcode = Initcode(initcode_prefix=adopt, deploy_code=SSTORE_MARKER_B)
    else:
        raise ValueError(f"unexpected payload: {payload}")
    tx = Transaction(sender=pre.fund_eoa(), to=None, data=initcode)
    state_test(
        pre=pre,
        post={
            tx.created_contract: Account(
                code=SSTORE_MARKER_A, storage={0: 1}, nonce=1
            )
        },
        tx=tx,
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize("probe", ["returndatasize", "returndatacopy"])
def test_initcode_return_data_not_in_caller_buffer(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    probe: str,
) -> None:
    """
    Verify a creation whose initcode adopted and then returned data leaves
    the creator's return data buffer empty.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode = Initcode(
        initcode_prefix=Op.POP(Op.SETCODEFROM(template)),
        deploy_code=SSTORE_MARKER_B,
    )
    if probe == "returndatasize":
        probe_code = Op.SSTORE(1, Op.RETURNDATASIZE)
        halts = False
    elif probe == "returndatacopy":
        # Copying one byte out of an empty buffer halts the whole tx.
        probe_code = Op.RETURNDATACOPY(0, 0, 1) + Op.SSTORE(1, 1)
        halts = True
    else:
        raise ValueError(f"unexpected probe: {probe}")
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, create_opcode(offset=0, size=Op.CALLDATASIZE))
        + probe_code
        + Op.STOP,
        storage={0: SENTINEL, 1: SENTINEL},
    )
    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )
    post: dict[Address, Account | None]
    if halts:
        post = {
            factory: Account(storage={0: SENTINEL, 1: SENTINEL}, nonce=1),
            created: Account.NONEXISTENT,
        }
    else:
        post = {
            factory: Account(storage={0: created, 1: 0}, nonce=2),
            created: Account(code=SSTORE_MARKER_A, nonce=1),
        }
    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=factory, data=initcode),
    )


def test_initcode_self_as_source(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify an account created in the tx is not a valid source to itself."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode = (
        Op.SSTORE(0, Op.SETCODEFROM(template))
        + Op.SSTORE(1, Op.SETCODEFROM(Op.ADDRESS))
        + Op.STOP
    )
    tx = Transaction(sender=pre.fund_eoa(), to=None, data=initcode)
    state_test(
        pre=pre,
        post={
            tx.created_contract: Account(
                code=SSTORE_MARKER_A, storage={0: 1, 1: 0}
            )
        },
        tx=tx,
    )


@pytest.mark.parametrize("reentry", ["via_helper", "direct"])
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Reentry()
def test_initcode_reentrant_call_sees_adopted_code(
    state_test: StateTestFiller,
    pre: Alloc,
    reentry: str,
) -> None:
    """
    Verify a call back into the new account runs the adopted code, and
    that `CODESIZE` and `CODECOPY` in that frame see it.
    """
    template_code = (
        Op.SSTORE(0, Op.CODESIZE)
        + Op.CODECOPY(0, 0, 32)
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.STOP
    )
    template = pre.deploy_contract(template_code)
    if reentry == "via_helper":
        helper = pre.deploy_contract(
            Op.POP(Op.CALL(address=Op.CALLER)) + Op.STOP
        )
        call_back = Op.CALL(address=helper)
    elif reentry == "direct":
        call_back = Op.CALL(address=Op.ADDRESS)
    else:
        raise ValueError(f"unexpected reentry: {reentry}")
    initcode = Op.POP(Op.SETCODEFROM(template)) + Op.POP(call_back) + Op.STOP
    tx = Transaction(sender=pre.fund_eoa(), to=None, data=initcode)
    state_test(
        pre=pre,
        post={
            tx.created_contract: Account(
                code=template_code,
                storage={
                    0: len(template_code),
                    1: Hash(bytes(template_code)[:32], right_padding=True),
                },
            )
        },
        tx=tx,
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize("ending", ["revert", "invalid", "out_of_gas"])
def test_initcode_revert_after_adopt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    ending: str,
) -> None:
    """
    Verify initcode that adopts and then reverts or halts creates no
    account.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    adopt = Op.POP(Op.SETCODEFROM(template))
    if ending == "revert":
        initcode = adopt + REVERT_WITH_CODE_HASH
        returned = SSTORE_MARKER_A.keccak256()
    elif ending == "invalid":
        initcode = adopt + Op.INVALID
        returned = Hash(0)
    elif ending == "out_of_gas":
        initcode = adopt + GasConsumer.out_of_gas(fork)
        returned = Hash(0)
    else:
        raise ValueError(f"unexpected ending: {ending}")
    # The return data is copied past the initcode, which fills memory first.
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(RESULT_SLOT, create_opcode(offset=0, size=Op.CALLDATASIZE))
        + Op.RETURNDATACOPY(Op.CALLDATASIZE, 0, Op.RETURNDATASIZE)
        + Op.SSTORE(1, Op.MLOAD(Op.CALLDATASIZE))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL, 1: SENTINEL},
    )
    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )
    state_test(
        pre=pre,
        post={
            factory: Account(
                storage={RESULT_SLOT: 0, 1: returned},
                nonce=2,
            ),
            created: Account.NONEXISTENT,
        },
        tx=Transaction(sender=pre.fund_eoa(), to=factory, data=initcode),
    )


@EIPChecklist.Opcode.Test.ExecutionContext.SetCode()
def test_delegated_eoa_adopts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify an EOA delegated to shell code in the same tx adopts itself."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa(amount=0)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=eoa,
        data=word(template),
        authorization_list=[
            AuthorizationTuple(address=shell, nonce=0, signer=eoa)
        ],
    )
    state_test(
        pre=pre,
        post={
            eoa: Account(
                code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1}, nonce=1
            ),
            shell: Account(
                code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
            ),
        },
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                eoa: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=adoption(1, SSTORE_MARKER_A),
                ),
                shell: BalAccountExpectation.empty(),
            }
        ),
    )


@pytest.mark.parametrize("context", ["delegatecall", "set_code"])
def test_adopt_code_owner(
    state_test: StateTestFiller,
    pre: Alloc,
    context: str,
) -> None:
    """
    Verify the current account adopts the account whose code it runs, as
    its own code hash differs from the source's.
    """
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    if context == "delegatecall":
        adopter = pre.deploy_contract(
            Op.SSTORE(1, call_with(shell, shell, call_opcode=Op.DELEGATECALL))
            + Op.STOP,
            storage={RESULT_SLOT: SENTINEL, 1: SENTINEL},
        )
        tx = Transaction(sender=pre.fund_eoa(), to=adopter)
        adopter_post = Account(
            code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: 1, 1: 1}
        )
    elif context == "set_code":
        adopter = pre.fund_eoa(delegation=shell)
        tx = Transaction(sender=pre.fund_eoa(), to=adopter, data=word(shell))
        adopter_post = Account(
            code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: 1}
        )
    else:
        raise ValueError(f"unexpected context: {context}")
    state_test(
        pre=pre,
        post={
            adopter: adopter_post,
            shell: Account(
                code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
            ),
        },
        tx=tx,
    )


def request_predeploys(fork: Fork) -> set[Address]:
    """Return the addresses of the fork's request predeploys."""
    return {
        request.system_contract_address
        for request in fork.system_contract_request_types()
    }


def block_system_calls(fork: Fork) -> Iterator[ParameterSet]:
    """Yield every system contract the block calls from SYSTEM_ADDRESS."""
    # Request predeploys are called checked, so their halt invalidates the
    # block.
    checked = request_predeploys(fork)
    for address, phase in fork.system_contract_call_phases().items():
        if phase != SystemCallPhase.NONE:
            yield pytest.param(
                address,
                id=str(address),
                marks=[pytest.mark.exception_test]
                if address in checked
                else [],
            )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize_by_fork("system_contract", block_system_calls)
def test_system_call_cannot_adopt(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    system_contract: Address,
) -> None:
    """Verify `SETCODEFROM` halts when run by a block's system call."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    override = Op.POP(Op.SETCODEFROM(template)) + Op.STOP
    pre[system_contract] = Account(code=override)
    if system_contract in request_predeploys(fork):
        block = Block(
            txs=[], exception=BlockException.SYSTEM_CONTRACT_CALL_FAILED
        )
        post = {}
    else:
        block = Block(
            txs=[],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    system_contract: BalAccountExpectation(code_changes=[]),
                    template: None,
                }
            ),
        )
        post = {system_contract: Account(code=override)}
    blockchain_test(pre=pre, blocks=[block], post=post)


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "phase,block_access_index",
    [
        pytest.param(
            SystemCallPhase.BEFORE_TRANSACTIONS, 0, id="pre_execution"
        ),
        pytest.param(
            SystemCallPhase.AFTER_TRANSACTIONS, 1, id="post_execution"
        ),
    ],
)
@pytest.mark.parametrize("later_calls", ["touch", "readopt"])
def test_adoption_across_system_calls(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    phase: SystemCallPhase,
    block_access_index: int,
    later_calls: str,
) -> None:
    """
    Verify system calls sharing a block access index record the code the
    adopter adopted last, as a code hash, including when later calls write
    the adopter without changing its code.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    template_b = pre.deploy_contract(SSTORE_MARKER_B)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    if later_calls == "touch":
        # The adopted code only writes the marker.
        source = template
        final_code = SSTORE_MARKER_A
        marker = MARKER_A
    elif later_calls == "readopt":
        # The adopted code adopts `template_b` when the next call runs it.
        source = pre.deploy_contract(
            Op.SSTORE(MARKER_SLOT, MARKER_B)
            + Op.POP(Op.SETCODEFROM(template_b))
            + Op.STOP
        )
        final_code = SSTORE_MARKER_B
        marker = MARKER_B
    else:
        raise ValueError(f"unexpected later_calls: {later_calls}")
    callers = [
        address
        for address, call_phase in fork.system_contract_call_phases().items()
        if call_phase == phase
    ]
    assert len(callers) >= 2, f"fewer than two system calls in {phase}"
    # Whichever call runs first adopts `source`; the later ones run the
    # adopted code and add to the adopter's balance.
    for caller in callers:
        pre[caller] = Account(
            balance=1,
            code=Op.POP(call_with(shell, source, value=1)) + Op.STOP,
        )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        shell: BalAccountExpectation(
                            code_changes=adoption(
                                block_access_index, final_code
                            ),
                        ),
                    }
                ),
            )
        ],
        post={
            shell: Account(
                code=final_code,
                balance=len(callers),
                storage={RESULT_SLOT: 1, MARKER_SLOT: marker},
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.with_all_system_contracts
@pytest.mark.parametrize(
    "context", ["call", "delegatecall_in", "delegatecall_out"]
)
def test_system_contract_as_current_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    context: str,
    system_contract: int,
) -> None:
    """
    Verify `SETCODEFROM` halts when a system contract the block calls is the
    current account, whoever called it.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    address = Address(system_contract)
    adopt = Op.POP(Op.SETCODEFROM(template))
    storage: dict[int, int]
    if context == "call":
        call_opcode = Op.CALL
        if_false = Op.SSTORE(0, 1) + adopt + Op.STOP
        storage = {}
    elif context == "delegatecall_in":
        call_opcode = Op.DELEGATECALL
        if_false = Op.SSTORE(0, 1) + adopt + Op.STOP
        storage = {}
    elif context == "delegatecall_out":
        call_opcode = Op.CALL
        lib = pre.deploy_contract(adopt + Op.STOP)
        if_false = Op.SSTORE(0, Op.DELEGATECALL(address=lib)) + Op.STOP
        storage = {0: SENTINEL}
    else:
        raise ValueError(f"unexpected context: {context}")
    # The block's own system call takes the STOP branch.
    override = Conditional(
        condition=Op.EQ(Op.CALLER, BeaconSpec.SYSTEM_ADDRESS),
        if_true=Op.STOP,
        if_false=if_false,
    )
    pre[address] = Account(code=override, storage=storage)
    # Slot 1, as under DELEGATECALL the override also writes slot 0 here.
    driver = pre.deploy_contract(
        Op.SSTORE(1, call_with(address, call_opcode=call_opcode)) + Op.STOP,
        storage={1: SENTINEL},
    )
    halting = (
        context != "delegatecall_in"
        and fork.system_contract_call_phases()[address] != SystemCallPhase.NONE
    )
    adopter: Address | None
    if halting and context == "call":
        adopter = None
        post = {
            driver: Account(storage={1: 0}),
            address: Account(code=override, storage={}),
        }
    elif halting and context == "delegatecall_out":
        adopter = None
        post = {
            driver: Account(storage={1: 1}),
            address: Account(code=override, storage={0: 0}),
        }
    elif context == "delegatecall_in":
        adopter = driver
        post = {
            driver: Account(code=SSTORE_MARKER_A, storage={0: 1, 1: 1}),
            address: Account(code=override, storage={}),
        }
    elif context in ("call", "delegatecall_out"):
        adopter = address
        post = {
            driver: Account(storage={1: 1}),
            address: Account(code=SSTORE_MARKER_A, storage={0: 1}),
        }
    else:
        raise ValueError(f"unexpected context: {context}")
    bal: dict[Address, BalAccountExpectation | None]
    if adopter is None:
        bal = {template: None}
    else:
        bal = {
            adopter: BalAccountExpectation(
                code_changes=adoption(1, SSTORE_MARKER_A)
            ),
            template: BalAccountExpectation.empty(),
        }
    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=driver),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=bal
        ),
    )
