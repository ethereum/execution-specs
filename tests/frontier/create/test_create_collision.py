"""
Test collision in CREATE/CREATE2 account creation, where the existing
account has non-empty code or nonce (EIP-684), and that an account
with only a balance or only storage is deployable.
"""

from typing import Dict, List, Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    GasConsumer,
    Initcode,
    Op,
    ParameterSet,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

pytestmark = [
    pytest.mark.valid_from("Frontier"),
    # We need to modify the pre-alloc to include the target account
    pytest.mark.pre_alloc_mutable,
]

# The prefix makes any initcode execution visible in storage: it adds
# slot 0x00, the witness that creation ran in the balance-only tests,
# and zeroes slot 0x01, which the collision tests pre-seed on some
# account shapes. On a correct collision abort neither write happens.
CORRECT_INITCODE = Initcode(
    deploy_code=Op.STOP,
    initcode_prefix=Op.SSTORE(0, 1) + Op.SSTORE(1, 0),
)

# Every account shape where creation must abort under EIP-684: the
# product of nonce, code, storage and balance with non-empty code or
# nonce. Cells with zero nonce and empty code are excluded because
# the account is deployable (see the balance-only and storage-only
# tests). Cells with empty storage catch clients that incorrectly
# abort on storage instead of code or nonce; cells with non-empty
# storage also check that the aborted creation neither wipes the
# storage nor runs the initcode, which would zero slot 0x01 in the
# correct-initcode case.
COLLISION_ACCOUNT_CASES = [
    (
        nonce,
        code,
        storage,
        balance,
        (
            f"nonce_{nonce}-"
            f"{'code' if code else 'no_code'}-"
            f"{'storage' if storage else 'no_storage'}-"
            f"balance_{balance}"
        ),
    )
    for nonce in (0, 1)
    for code in (b"", b"\0")
    for storage in ({}, {0x01: 0x01})
    for balance in (0, 1)
    if nonce != 0 or code != b""
]

# Preserve the reverting and out-of-gas initcode coverage for the two
# original ported account shapes. The successful initcode is the probe
# that distinguishes a missed collision for every additional shape.
ORIGINAL_COLLISION_ACCOUNT_IDS = {
    "nonce_0-code-storage-balance_0",
    "nonce_1-no_code-no_storage-balance_0",
}


def collision_params(fork: Fork) -> List[ParameterSet]:
    """
    Return every account shape crossed with every initcode outcome.

    The out-of-gas initcode is sized against the fork's own memory
    pricing, so the cases cannot be built before the fork is known.
    """
    initcode_cases = [
        (CORRECT_INITCODE, "correct-initcode", False),
        (Op.REVERT(0, 0), "revert-initcode", True),
        (GasConsumer.out_of_gas(fork), "oog-initcode", True),
    ]
    return [
        pytest.param(
            nonce,
            code,
            storage,
            balance,
            initcode,
            id=f"{initcode_id}-{account_id}",
        )
        for initcode, initcode_id, original_accounts_only in initcode_cases
        for nonce, code, storage, balance, account_id in (
            COLLISION_ACCOUNT_CASES
        )
        if not original_accounts_only
        or account_id in ORIGINAL_COLLISION_ACCOUNT_IDS
    ]


PORTED_FROM = pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stSStoreTest/InitCollisionFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stSStoreTest/InitCollisionNonZeroNonceFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/636"],
)


@PORTED_FROM
@pytest.mark.parametrize_by_fork(
    "collision_nonce,collision_code,collision_storage,collision_balance,initcode",
    collision_params,
)
@pytest.mark.with_all_contract_creating_tx_types
@pytest.mark.eels_base_coverage
def test_create_tx_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    collision_nonce: int,
    collision_code: bytes,
    collision_storage: Dict[int, int],
    collision_balance: int,
    initcode: Bytecode,
    fork: Fork,
) -> None:
    """
    Test that a contract creation transaction exceptionally aborts when
    the target address has non-empty code or nonce, leaving the existing
    account untouched.
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        ty=tx_type,
        to=None,
        data=initcode,
        protected=False,
    )

    created_contract_address = tx.created_contract

    # This is the collision
    pre[created_contract_address] = Account(
        nonce=collision_nonce,
        code=collision_code,
        storage=collision_storage,
        balance=collision_balance,
    )

    expected_block_access_list = None
    if fork.is_eip_enabled(7928):
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                created_contract_address: BalAccountExpectation.empty()
            }
        )

    state_test(
        pre=pre,
        post={
            created_contract_address: Account(
                nonce=collision_nonce,
                code=collision_code,
                storage=collision_storage,
                balance=collision_balance,
            ),
        },
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )


@PORTED_FROM
@pytest.mark.parametrize_by_fork(
    "collision_nonce,collision_code,collision_storage,collision_balance,initcode",
    collision_params,
)
@pytest.mark.with_all_create_opcodes
def test_create_opcode_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    collision_nonce: int,
    collision_code: bytes,
    collision_storage: Dict[int, int],
    collision_balance: int,
    initcode: Bytecode,
) -> None:
    """
    Test that a contract creation opcode exceptionally aborts when the
    target address has non-empty code or nonce, leaving the existing
    account untouched.
    """
    assert len(initcode) <= 32
    contract_creator_code = (
        # Reverts if and only if contract creation fails. In Frontier/Homestead
        # this runs out of gas, and every other fork jumps to a non-JUMPDEST.
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.JUMPI(
            condition=Op.ISZERO(
                create_opcode(value=0, offset=0, size=len(initcode))
            ),
            pc=0,
        )
        + Op.STOP
    )
    contract_creator_address = pre.deploy_contract(contract_creator_code)

    gas_limiter_code = (
        # Calls the contract creator, reserving some gas to SSTORE the result.
        Op.SSTORE(
            0x01,
            Op.CALL(
                gas=Op.SUB(Op.GAS, 50_000),
                address=contract_creator_address,
                value=0,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            ),
        )
    )
    gas_limiter_address = pre.deploy_contract(
        gas_limiter_code,
        storage={0x01: 0x02},
    )

    created_contract_address = compute_create_address(
        address=contract_creator_address,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=gas_limiter_address,
        protected=False,
    )

    pre[created_contract_address] = Account(
        nonce=collision_nonce,
        code=collision_code,
        storage=collision_storage,
        balance=collision_balance,
    )

    state_test(
        pre=pre,
        post={
            created_contract_address: Account(
                nonce=collision_nonce,
                code=collision_code,
                storage=collision_storage,
                balance=collision_balance,
            ),
            gas_limiter_address: Account(storage={0x01: 0x00}),
        },
        tx=tx,
    )


@pytest.mark.with_all_contract_creating_tx_types
def test_create_tx_balance_only_target(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
) -> None:
    """
    Test that a contract creation transaction succeeds when the target
    address has only a balance: an account with zero nonce, no code and
    no storage is not a collision (EIP-684).
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        ty=tx_type,
        to=None,
        data=CORRECT_INITCODE,
        protected=False,
    )

    created_contract_address = tx.created_contract

    pre[created_contract_address] = Account(balance=1)

    state_test(
        pre=pre,
        post={
            created_contract_address: Account(
                balance=1,
                code=CORRECT_INITCODE.deploy_code,
                storage={0x00: 0x01},
            ),
        },
        tx=tx,
    )


@pytest.mark.with_all_create_opcodes
def test_create_opcode_balance_only_target(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """
    Test that a contract creation opcode succeeds when the target
    address has only a balance: an account with zero nonce, no code and
    no storage is not a collision (EIP-684).
    """
    initcode = CORRECT_INITCODE
    assert len(initcode) <= 32
    contract_creator_code = (
        # Stores the created address, which is non-zero on success.
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.SSTORE(0x01, create_opcode(value=0, offset=0, size=len(initcode)))
        + Op.STOP
    )
    contract_creator_address = pre.deploy_contract(contract_creator_code)

    created_contract_address = compute_create_address(
        address=contract_creator_address,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_creator_address,
        protected=False,
    )

    pre[created_contract_address] = Account(balance=1)

    state_test(
        pre=pre,
        post={
            created_contract_address: Account(
                balance=1,
                code=CORRECT_INITCODE.deploy_code,
                storage={0x00: 0x01},
            ),
            contract_creator_address: Account(
                storage={0x01: created_contract_address}
            ),
        },
        tx=tx,
    )


# Initcode for the storage-only tests. Slot 0x00 records one more than
# the value the initcode reads from slot 0x01, which the target account
# pre-seeds: a wiped target stores 1, a retained one stores 2, and an
# aborted creation stores nothing. Slot 0x02 is never read, so only a
# wipe that covers slots the initcode does not touch can zero it.
STORAGE_PROBE_PREFIX = Op.SSTORE(
    0,
    Op.ADD(Op.SLOAD(1, key_warm=False), 1),
    key_warm=False,
    original_value=0,
    new_value=1,
)
STORAGE_PROBE_INITCODE = Initcode(
    deploy_code=Op.STOP,
    initcode_prefix=STORAGE_PROBE_PREFIX,
)
STORAGE_ONLY_PRE_STORAGE = {0x01: 0x01, 0x02: 0x02}
STORAGE_ONLY_POST_STORAGE = {0x00: 0x01, 0x01: 0x00, 0x02: 0x00}

# TODO: Contract creation over a zero-nonce account that holds storage
# stays undefined for clients until EIP-8253 (Hegota) bumps the nonce of
# the mainnet accounts of that shape. Revisit the storage-only tests once
# EIP-8253 ships: unskip them or drop them. See PR #3508.
STORAGE_ONLY_ACCOUNT_SKIP = pytest.mark.skip(
    reason="Undefined until EIP-8253 (Hegota), see PR #3508"
)


STORAGE_ONLY_INITCODE_OUTCOMES = [
    pytest.param("correct", id="correct-initcode"),
    pytest.param("revert", id="revert-initcode"),
    pytest.param("oog", id="oog-initcode"),
]


def created_contract_nonce(fork: Fork) -> int:
    """
    Return the nonce of a freshly created contract. EIP-161 set it to
    one; before that it stayed at zero, which is how the storage-only
    account shape came to exist.
    """
    return 1 if fork.is_eip_enabled(161) else 0


def storage_only_case(
    outcome: str, fork: Fork, balance: int
) -> Tuple[Bytecode, Account]:
    """
    Return the initcode for a storage-only creation outcome and the
    target account it leaves behind: the probe deploys over wiped
    storage, and a reverting or out-of-gas initcode leaves the storage
    in place.
    """
    retained = Account(
        nonce=0, balance=balance, code=b"", storage=STORAGE_ONLY_PRE_STORAGE
    )
    if outcome == "correct":
        deployed = Account(
            nonce=created_contract_nonce(fork),
            balance=balance,
            code=STORAGE_PROBE_INITCODE.deploy_code,
            storage=STORAGE_ONLY_POST_STORAGE,
        )
        return STORAGE_PROBE_INITCODE, deployed
    elif outcome == "revert":
        return Op.REVERT(0, 0), retained
    elif outcome == "oog":
        return GasConsumer.out_of_gas(fork), retained
    else:
        raise ValueError(f"unknown initcode outcome: {outcome}")


def creation_tx_gas(fork: Fork, initcode: Bytecode) -> int | None:
    """
    Return the gas a creation transaction running ``initcode`` uses, or
    ``None`` when it is the gas limit and pins nothing: an initcode that
    runs out of gas, or ``REVERT`` before EIP-140 made it an opcode.
    """
    if initcode == GasConsumer.out_of_gas(fork):
        return None
    if initcode == Op.REVERT(0, 0) and not fork.is_eip_enabled(140):
        return None
    if isinstance(initcode, Initcode) and fork.is_eip_enabled(8037):
        # TODO: Initcode.gas_cost prices the code deposit's state gas
        # 512 short of the spec, so the deploying case stays unpinned.
        return None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    # EIP-7623: the calldata floor binds when execution is cheap.
    execution_gas = intrinsic_cost(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    ) + initcode.gas_cost(fork)
    floor_gas = intrinsic_cost(calldata=initcode, contract_creation=True)
    return max(execution_gas, floor_gas)


@STORAGE_ONLY_ACCOUNT_SKIP
@pytest.mark.parametrize("initcode_outcome", STORAGE_ONLY_INITCODE_OUTCOMES)
@pytest.mark.parametrize("balance", [0, 1])
@pytest.mark.with_all_contract_creating_tx_types
def test_create_tx_storage_only_target(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    initcode_outcome: str,
    balance: int,
) -> None:
    """
    Test that a contract creation transaction succeeds when the target
    address has zero nonce and no code but non-empty storage: EIP-684
    does not consider storage, and the pre-existing storage is wiped
    before the initcode runs. A failing initcode leaves it in place.
    """
    initcode, target_post = storage_only_case(initcode_outcome, fork, balance)
    gas_used = creation_tx_gas(fork, initcode)
    tx = Transaction(
        sender=pre.fund_eoa(),
        ty=tx_type,
        to=None,
        data=initcode,
        protected=False,
        expected_receipt=(
            TransactionReceipt(cumulative_gas_used=gas_used)
            if gas_used is not None
            else None
        ),
    )

    created_contract_address = tx.created_contract

    pre[created_contract_address] = Account(
        balance=balance, storage=STORAGE_ONLY_PRE_STORAGE
    )

    state_test(
        pre=pre,
        post={created_contract_address: target_post},
        tx=tx,
    )


@STORAGE_ONLY_ACCOUNT_SKIP
@pytest.mark.parametrize("initcode_outcome", STORAGE_ONLY_INITCODE_OUTCOMES)
@pytest.mark.parametrize("balance", [0, 1])
@pytest.mark.with_all_create_opcodes
def test_create_opcode_storage_only_target(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    initcode_outcome: str,
    balance: int,
) -> None:
    """
    Test that a contract creation opcode succeeds when the target
    address has zero nonce and no code but non-empty storage: EIP-684
    does not consider storage, and the pre-existing storage is wiped
    before the initcode runs. A failing initcode leaves it in place.
    """
    initcode, target_post = storage_only_case(initcode_outcome, fork, balance)
    assert len(initcode) <= 32
    contract_creator_code = (
        # Stores the created address, which is zero on failure.
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.SSTORE(0x01, create_opcode(value=0, offset=0, size=len(initcode)))
    )
    contract_creator_address = pre.deploy_contract(contract_creator_code)

    created_contract_address = compute_create_address(
        address=contract_creator_address,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_creator_address,
        protected=False,
    )

    pre[created_contract_address] = Account(
        balance=balance, storage=STORAGE_ONLY_PRE_STORAGE
    )

    if initcode_outcome == "correct":
        creator_post = Account(
            nonce=2, storage={0x01: created_contract_address}
        )
    else:
        # Whether the creator's nonce bump survives the failed child
        # depends on EIP-150, which is not the subject here.
        creator_post = Account(storage={0x01: 0})
    state_test(
        pre=pre,
        post={
            created_contract_address: target_post,
            contract_creator_address: creator_post,
        },
        tx=tx,
    )


@STORAGE_ONLY_ACCOUNT_SKIP
def test_create_tx_storage_only_target_later_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that storage wiped by a contract creation stays wiped for the
    rest of the block: a later transaction reads the old slots as zero
    and a write of zero to one of them is a no-op.
    """
    # The deployed code repeats the initcode probe on slot 0x02, which
    # only the wipe zeroes, and writes the zero back so the block access
    # list has to net that slot against the wiped value, not the
    # pre-block one.
    runtime_probe = Op.SSTORE(
        3,
        Op.ADD(Op.SLOAD(2, key_warm=False), 1),
        key_warm=False,
        original_value=0,
        new_value=1,
    ) + Op.SSTORE(2, 0, key_warm=True, original_value=0, new_value=0)
    initcode = Initcode(
        deploy_code=runtime_probe,
        initcode_prefix=STORAGE_PROBE_PREFIX,
    )

    sender = pre.fund_eoa()
    create_gas = creation_tx_gas(fork, initcode)
    create_tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        protected=False,
        expected_receipt=(
            TransactionReceipt(cumulative_gas_used=create_gas)
            if create_gas is not None
            else None
        ),
    )
    created_contract_address = create_tx.created_contract
    pre[created_contract_address] = Account(storage=STORAGE_ONLY_PRE_STORAGE)

    # The wiped slot prices as an untouched one: a cold read, a fresh
    # write to slot 3 and a warm no-op write back to slot 2.
    probe_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + runtime_probe.gas_cost(fork)
    )
    probe_tx = Transaction(
        sender=sender,
        to=created_contract_address,
        protected=False,
        expected_receipt=(
            TransactionReceipt(cumulative_gas_used=create_gas + probe_gas)
            if create_gas is not None
            else None
        ),
    )

    expected_block_access_list = None
    if fork.is_eip_enabled(7928):
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                created_contract_address: BalAccountExpectation(
                    storage_reads=[0x01, 0x02],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=1
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x03,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=2, post_value=1
                                )
                            ],
                        ),
                    ],
                ),
            }
        )

    blockchain_test(
        pre=pre,
        post={
            created_contract_address: Account(
                nonce=created_contract_nonce(fork),
                balance=0,
                code=runtime_probe,
                storage={**STORAGE_ONLY_POST_STORAGE, 0x03: 0x01},
            ),
        },
        blocks=[
            Block(
                txs=[create_tx, probe_tx],
                expected_block_access_list=expected_block_access_list,
            )
        ],
    )
