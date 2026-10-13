"""Test SETCODEFROM semantics, source validity and reverts."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalCodeChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Conditional,
    EIPChecklist,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import (
    ADOPT_FROM_CALLDATA,
    MARKER_A,
    MARKER_C,
    MARKER_SLOT,
    RESULT_SLOT,
    REVERT_WITH_CODE_HASH,
    SENTINEL,
    SSTORE_MARKER_A,
    SSTORE_MARKER_B,
    SSTORE_MARKER_C_THEN_ADOPT,
    adoption,
    call_with,
    word,
)
from .spec import ref_spec_8298

REFERENCE_SPEC_GIT_PATH = ref_spec_8298.git_path
REFERENCE_SPEC_VERSION = ref_spec_8298.version

pytestmark = pytest.mark.valid_from("EIP8298")


def test_adopt(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify adoption replaces only the code hash and pushes 1."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    adopter = pre.deploy_contract(
        ADOPT_FROM_CALLDATA,
        storage={5: 7, RESULT_SLOT: SENTINEL},
        balance=10,
        nonce=3,
    )
    tx = Transaction(sender=pre.fund_eoa(), to=adopter, data=word(template))
    post = {
        adopter: Account(
            code=SSTORE_MARKER_A,
            storage={5: 7, RESULT_SLOT: 1},
            balance=10,
            nonce=3,
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                adopter: BalAccountExpectation(
                    code_changes=adoption(1, SSTORE_MARKER_A)
                ),
                template: BalAccountExpectation.empty(),
            }
        ),
    )


def test_later_call_runs_adopted_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify other frames observe and run the adopted code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    driver = pre.deploy_contract(
        Op.POP(call_with(shell, template))
        + Op.SSTORE(1, Op.EXTCODEHASH(shell))
        + Op.SSTORE(2, Op.EXTCODESIZE(shell))
        + Op.EXTCODECOPY(shell, 0, 0, 32)
        + Op.SSTORE(3, Op.MLOAD(0))
        + Op.POP(call_with(shell))
        + Op.STOP
    )
    tx = Transaction(sender=pre.fund_eoa(), to=driver)
    post = {
        shell: Account(
            code=SSTORE_MARKER_A,
            storage={RESULT_SLOT: 1, MARKER_SLOT: MARKER_A},
        ),
        driver: Account(
            storage={
                1: SSTORE_MARKER_A.keccak256(),
                2: len(SSTORE_MARKER_A),
                3: Hash(bytes(SSTORE_MARKER_A)[:32], right_padding=True),
            }
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_self_inspection_after_adopt(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `EXTCODE*` of the current account see the adopted code, while
    `CODESIZE` and `CODECOPY` see the frame's loaded code.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    code = (
        Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(template))
        + Op.SSTORE(1, Op.EXTCODEHASH(Op.ADDRESS))
        + Op.SSTORE(2, Op.EXTCODESIZE(Op.ADDRESS))
        + Op.EXTCODECOPY(Op.ADDRESS, 0, 0, 32)
        + Op.SSTORE(3, Op.MLOAD(0))
        + Op.SSTORE(4, Op.CODESIZE)
        + Op.CODECOPY(32, 0, 32)
        + Op.SSTORE(5, Op.MLOAD(32))
        + Op.STOP
    )
    adopter = pre.deploy_contract(code)
    tx = Transaction(sender=pre.fund_eoa(), to=adopter)
    post = {
        adopter: Account(
            code=SSTORE_MARKER_A,
            storage={
                RESULT_SLOT: 1,
                1: SSTORE_MARKER_A.keccak256(),
                2: len(SSTORE_MARKER_A),
                3: Hash(bytes(SSTORE_MARKER_A)[:32], right_padding=True),
                4: len(code),
                5: Hash(bytes(code)[:32], right_padding=True),
            },
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode != Op.STATICCALL
)
def test_reentrant_adoption(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Verify an inner frame's adoption leaves the outer frame on its loaded
    code, while a later call into the account runs the adopted code.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    adopter = pre.deploy_contract(
        Conditional(
            condition=Op.CALLDATASIZE,
            if_true=ADOPT_FROM_CALLDATA,
            if_false=Op.POP(
                call_with(Op.ADDRESS, template, call_opcode=call_opcode)
            )
            + Op.SSTORE(1, 1)
            + Op.POP(call_with(Op.ADDRESS, call_opcode=call_opcode))
            + Op.STOP,
        ),
        storage={RESULT_SLOT: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=adopter)
    post = {
        adopter: Account(
            code=SSTORE_MARKER_A,
            storage={RESULT_SLOT: 1, 1: 1, MARKER_SLOT: MARKER_A},
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "high_bits",
    [
        pytest.param(
            1 << 160,
            id="bit_160",
            marks=EIPChecklist.Opcode.Test.OutOfBounds.Verify.MaxPlusOne(),
        ),
        pytest.param(
            (2**256 - 1) ^ (2**160 - 1),
            id="all_high_bits",
            marks=EIPChecklist.Opcode.Test.OutOfBounds.Verify.Max(),
        ),
    ],
)
def test_source_high_bits_ignored(
    state_test: StateTestFiller,
    pre: Alloc,
    high_bits: int,
) -> None:
    """Verify only the low 160 bits of the stack input select the source."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    source = high_bits | int.from_bytes(template, "big")
    adopter = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(source)) + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=adopter)
    post = {adopter: Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("second", ["other_source", "restore"])
def test_two_adoptions_same_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    second: str,
) -> None:
    """
    Verify a second adoption in one frame replaces the first, and that
    restoring the original code hash leaves no code change.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    template_b = pre.deploy_contract(SSTORE_MARKER_B)
    code = (
        Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(Op.CALLDATALOAD(0)))
        + Op.SSTORE(1, Op.EXTCODEHASH(Op.ADDRESS))
        + Op.SSTORE(2, Op.SETCODEFROM(Op.CALLDATALOAD(32)))
        + Op.STOP
    )
    adopter = pre.deploy_contract(code)
    final_code: Bytecode
    if second == "other_source":
        second_source = template_b
        final_code = SSTORE_MARKER_B
        code_changes = adoption(1, SSTORE_MARKER_B)
    elif second == "restore":
        second_source = pre.deploy_contract(code)
        final_code = code
        code_changes = []
    else:
        raise ValueError(f"Unknown second: {second}")
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=adopter,
        data=word(template) + word(second_source),
    )
    post = {
        adopter: Account(
            code=final_code,
            storage={RESULT_SLOT: 1, 1: SSTORE_MARKER_A.keccak256(), 2: 1},
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                adopter: BalAccountExpectation(code_changes=code_changes),
            }
        ),
    )


@pytest.mark.parametrize("source", ["twin", "self"])
def test_same_hash_source(
    state_test: StateTestFiller,
    pre: Alloc,
    source: str,
) -> None:
    """Verify adopting the current code hash succeeds as a no-op."""
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    shell_twin = pre.deploy_contract(ADOPT_FROM_CALLDATA)
    if source == "twin":
        source_address = shell_twin
    elif source == "self":
        source_address = shell
    else:
        raise ValueError(f"Unknown source: {source}")
    tx = Transaction(
        sender=pre.fund_eoa(), to=shell, data=word(source_address)
    )
    post = {shell: Account(code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: 1})}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                shell: BalAccountExpectation(code_changes=[]),
            }
        ),
    )


def test_transitive_adopt_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a source that adopted earlier in the tx hands over its hash."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    shell_twin = pre.deploy_contract(ADOPT_FROM_CALLDATA)
    driver = pre.deploy_contract(
        Op.POP(call_with(shell_twin, template))
        + Op.POP(call_with(shell, shell_twin))
        + Op.STOP
    )
    tx = Transaction(sender=pre.fund_eoa(), to=driver)
    post = {
        shell_twin: Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1}),
        shell: Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_source_created_earlier_in_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a source deployed earlier in the block is valid, and that its
    bytecode outlives its own replacement.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    sender = pre.fund_eoa()
    source = compute_create_address(address=sender, nonce=0)
    block_1 = Block(
        txs=[
            Transaction(
                sender=sender,
                to=None,
                data=Initcode(deploy_code=SSTORE_MARKER_C_THEN_ADOPT),
            ),
            Transaction(sender=sender, to=shell, data=word(source)),
            Transaction(sender=sender, to=source, data=word(template)),
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                source: BalAccountExpectation(
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1,
                            new_code=SSTORE_MARKER_C_THEN_ADOPT,
                        )
                    ]
                    + adoption(3, SSTORE_MARKER_A)
                ),
                shell: BalAccountExpectation(
                    code_changes=adoption(2, SSTORE_MARKER_C_THEN_ADOPT)
                ),
            }
        ),
    )
    block_2 = Block(
        txs=[
            Transaction(sender=sender, to=shell),
            Transaction(sender=sender, to=source),
        ]
    )
    post = {
        shell: Account(
            code=SSTORE_MARKER_C_THEN_ADOPT,
            storage={RESULT_SLOT: 0, MARKER_SLOT: MARKER_C},
        ),
        source: Account(
            code=SSTORE_MARKER_A,
            storage={RESULT_SLOT: 1, MARKER_SLOT: MARKER_A},
        ),
    }
    blockchain_test(pre=pre, blocks=[block_1, block_2], post=post)


def test_adoptions_across_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Verify each tx's adoption is recorded at its own BAL index."""
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    shell_twin = pre.deploy_contract(ADOPT_FROM_CALLDATA)
    sender = pre.fund_eoa()
    source = pre.deploy_contract(SSTORE_MARKER_C_THEN_ADOPT)
    block = Block(
        txs=[
            Transaction(sender=sender, to=shell, data=word(source)),
            Transaction(sender=sender, to=shell, data=word(shell_twin)),
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                shell: BalAccountExpectation(
                    code_changes=adoption(1, SSTORE_MARKER_C_THEN_ADOPT)
                    + adoption(2, ADOPT_FROM_CALLDATA)
                ),
                shell_twin: BalAccountExpectation.empty(),
            }
        ),
    )
    post = {
        shell: Account(
            code=ADOPT_FROM_CALLDATA,
            storage={RESULT_SLOT: 1, MARKER_SLOT: MARKER_C},
        ),
    }
    blockchain_test(pre=pre, blocks=[block], post=post)


@pytest.mark.with_all_create_opcodes
def test_adopt_into_account_created_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """Verify an account created earlier in the tx can adopt code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode = Initcode(deploy_code=ADOPT_FROM_CALLDATA)
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.MSTORE(32, create_opcode(offset=0, size=Op.CALLDATASIZE))
        + Op.POP(call_with(Op.MLOAD(32), template))
        + Op.STOP
    )
    created = compute_create_address(
        address=factory, nonce=1, initcode=initcode, opcode=create_opcode
    )
    tx = Transaction(sender=pre.fund_eoa(), to=factory, data=initcode)
    post = {
        created: Account(
            code=SSTORE_MARKER_A, nonce=1, storage={RESULT_SLOT: 1}
        ),
    }
    state_test(
        pre=pre,
        post=post,
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


def test_adopted_account_as_delegation_target(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a delegation to an adopter resolves to its adopted code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    delegating_eoa = pre.fund_eoa(delegation=shell)
    driver = pre.deploy_contract(
        Op.POP(call_with(shell, template))
        + Op.POP(call_with(delegating_eoa))
        + Op.STOP
    )
    tx = Transaction(sender=pre.fund_eoa(), to=driver)
    post = {
        shell: Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1}),
        delegating_eoa: Account(storage={MARKER_SLOT: MARKER_A}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_selfdestructed_source_stays_valid(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a source that self-destructed earlier in the tx stays valid."""
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    # Not created in this tx: post-Cancun its code stays.
    source_code = Op.SELFDESTRUCT(Op.ORIGIN)
    source = pre.deploy_contract(source_code)
    driver = pre.deploy_contract(
        Op.POP(call_with(source)) + Op.POP(call_with(shell, source)) + Op.STOP
    )
    tx = Transaction(sender=pre.fund_eoa(), to=driver)
    post = {
        shell: Account(code=source_code, storage={RESULT_SLOT: 1}),
        source: Account(code=source_code),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_system_contracts
def test_system_contract_source(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    system_contract: int,
) -> None:
    """Verify a system contract is a valid source."""
    source = Address(system_contract)
    adopter = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(source))
        + Op.SSTORE(
            1, Op.EQ(Op.EXTCODEHASH(Op.ADDRESS), Op.EXTCODEHASH(source))
        )
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=adopter)
    post = {adopter: Account(storage={RESULT_SLOT: 1, 1: 1})}
    blockchain_test(pre=pre, blocks=[Block(txs=[tx])], post=post)


@pytest.mark.parametrize(
    "source_kind",
    [
        "nonexistent",
        "eoa_with_balance",
        pytest.param("eoa_nonce_only", marks=pytest.mark.pre_alloc_mutable),
        "delegated_eoa",
        pytest.param(
            "ef_prefixed_non_designator", marks=pytest.mark.pre_alloc_mutable
        ),
    ],
)
def test_invalid_source(
    state_test: StateTestFiller,
    pre: Alloc,
    source_kind: str,
) -> None:
    """Verify an invalid source pushes 0 and leaves the adopter unchanged."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    bal: dict[Address, BalAccountExpectation | None] = {}
    if source_kind == "nonexistent":
        source = pre.nonexistent_account()
    elif source_kind == "eoa_with_balance":
        source = pre.fund_eoa()
    elif source_kind == "eoa_nonce_only":
        source = pre.fund_eoa(amount=0, nonce=1)
    elif source_kind == "delegated_eoa":
        source = pre.fund_eoa(delegation=template)
        bal[template] = None  # the delegation target is never accessed
    elif source_kind == "ef_prefixed_non_designator":
        source = pre.deploy_contract(Bytes("0xef00") + bytes(40))
    else:
        raise ValueError(f"Unknown source_kind: {source_kind}")
    bal[source] = BalAccountExpectation.empty()
    tx = Transaction(sender=pre.fund_eoa(), to=shell, data=word(source))
    state_test(
        pre=pre,
        post={
            shell: Account(code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: 0})
        },
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=bal
        ),
    )


def test_source_created_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a source created earlier in the same tx is invalid."""
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    driver = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.MSTORE(32, Op.CREATE(0, 0, Op.CALLDATASIZE))
        + Op.POP(Op.CALL(address=shell, args_offset=32, args_size=32))
        + Op.STOP
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=driver,
        data=Initcode(deploy_code=SSTORE_MARKER_A),
    )
    post = {
        shell: Account(code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: 0}),
        compute_create_address(address=driver, nonce=1): Account(
            code=SSTORE_MARKER_A
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.StackUnderflow()
def test_stack_underflow(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify SETCODEFROM on an empty stack halts the frame."""
    callee_code = Op.SETCODEFROM + Op.STOP
    callee = pre.deploy_contract(callee_code)
    caller = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, Op.CALL(address=callee)) + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller)
    post = {
        caller: Account(storage={RESULT_SLOT: 0}),
        callee: Account(code=callee_code),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_revert_after_adopt(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a revert discards an adoption the frame observed."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    adopter_code = Op.POP(Op.SETCODEFROM(template)) + REVERT_WITH_CODE_HASH
    adopter = pre.deploy_contract(adopter_code)
    driver = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, call_with(adopter, ret_size=32))
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL, 1: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=driver)
    post = {
        driver: Account(
            storage={RESULT_SLOT: 0, 1: SSTORE_MARKER_A.keccak256()}
        ),
        adopter: Account(code=adopter_code),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                adopter: BalAccountExpectation(code_changes=[]),
                template: BalAccountExpectation.empty(),
            }
        ),
    )


def test_parent_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a parent frame's revert discards its callee's adoption."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    parent = pre.deploy_contract(
        Op.POP(call_with(shell, template))
        + Op.MSTORE(0, Op.EXTCODEHASH(shell))
        + Op.REVERT(0, 32)
    )
    wrapper = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, call_with(parent, ret_size=32))
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.POP(call_with(shell))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL, 1: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=wrapper)
    post = {
        wrapper: Account(
            storage={RESULT_SLOT: 0, 1: SSTORE_MARKER_A.keccak256()}
        ),
        # The post-revert call ran the original code.
        shell: Account(code=ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: 0}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_inner_adoption_reverts_outer_kept(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a reverted inner adoption restores the outer frame's one."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    template_b = pre.deploy_contract(SSTORE_MARKER_B)
    library = pre.deploy_contract(
        Op.POP(Op.SETCODEFROM(template_b)) + REVERT_WITH_CODE_HASH
    )
    adopter = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(template))
        + Op.SSTORE(1, Op.DELEGATECALL(address=library, ret_size=32))
        + Op.SSTORE(2, Op.MLOAD(0))
        + Op.POP(Op.CALL(address=Op.ADDRESS))
        + Op.STOP,
        storage={1: SENTINEL, 2: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=adopter)
    post = {
        adopter: Account(
            code=SSTORE_MARKER_A,
            storage={
                RESULT_SLOT: 1,
                1: 0,
                2: SSTORE_MARKER_B.keccak256(),
                MARKER_SLOT: MARKER_A,
            },
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_revert_restores_same_tx_delegation(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify a reverted adoption restores a delegation set in the same tx."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    impl = pre.deploy_contract(
        Op.POP(Op.SETCODEFROM(template)) + REVERT_WITH_CODE_HASH
    )
    eoa = pre.fund_eoa(amount=0)
    driver = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, call_with(eoa, ret_size=32))
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL, 1: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=driver,
        authorization_list=[
            AuthorizationTuple(address=impl, nonce=0, signer=eoa)
        ],
    )
    designator = Spec7702.delegation_designation(impl)
    post = {
        eoa: Account(code=designator, nonce=1),
        driver: Account(
            storage={RESULT_SLOT: 0, 1: SSTORE_MARKER_A.keccak256()}
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # The end-of-tx code was set by the authorization.
                eoa: BalAccountExpectation(
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=designator
                        )
                    ]
                ),
            }
        ),
    )


@pytest.mark.parametrize("created_same_tx", [True, False])
def test_created_adopter_selfdestructed(
    state_test: StateTestFiller,
    pre: Alloc,
    created_same_tx: bool,
) -> None:
    """
    Verify an adopter running adopted `SELFDESTRUCT` code is deleted only
    when it was created in the same tx.
    """
    source_code = Op.SELFDESTRUCT(Op.ORIGIN)
    source = pre.deploy_contract(source_code)
    if created_same_tx:
        initcode = Initcode(deploy_code=ADOPT_FROM_CALLDATA)
        factory = pre.deploy_contract(
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.MSTORE(32, Op.CREATE2(0, 0, Op.CALLDATASIZE, 0))
            + Op.POP(call_with(Op.MLOAD(32), source))
            + Op.POP(call_with(Op.MLOAD(32)))
            + Op.STOP
        )
        adopter = compute_create_address(
            address=factory, salt=0, initcode=initcode, opcode=Op.CREATE2
        )
        tx = Transaction(sender=pre.fund_eoa(), to=factory, data=initcode)
        post: dict[Address, Account | None] = {adopter: Account.NONEXISTENT}
        # EIP-7928: a deleted account keeps no nonce or code changes, and
        # its written slots become reads.
        adopter_bal = BalAccountExpectation(
            nonce_changes=[],
            code_changes=[],
            storage_changes=[],
            storage_reads=[RESULT_SLOT],
            balance_changes=[],
        )
    elif not created_same_tx:
        adopter = pre.deploy_contract(
            ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}, balance=1
        )
        driver = pre.deploy_contract(
            Op.POP(call_with(adopter, source))
            + Op.POP(call_with(adopter))
            + Op.STOP
        )
        tx = Transaction(sender=pre.fund_eoa(), to=driver)
        post = {
            adopter: Account(
                code=source_code, storage={RESULT_SLOT: 1}, balance=0
            ),
        }
        adopter_bal = BalAccountExpectation(
            code_changes=adoption(1, source_code)
        )
    else:
        raise ValueError(f"Unknown created_same_tx: {created_same_tx}")
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={adopter: adopter_bal}
        ),
    )
