"""
Test collision in CREATE/CREATE2 account creation, where the existing
account has non-empty code or nonce (EIP-684), and that an account
with only a balance is deployable.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytecode,
    Fork,
    GasConsumer,
    Initcode,
    Op,
    ParameterSet,
    StateTestFiller,
    Transaction,
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
# nonce. Cells with zero nonce and empty code are excluded: with
# non-empty storage the behavior is undefined in protocol (EIP-7610
# was declined for inclusion in Glamsterdam), and with empty storage
# the account is deployable (see the balance-only tests). Cells with
# empty storage catch clients that incorrectly abort on storage
# instead of code or nonce; cells with non-empty storage also check
# that the aborted creation neither wipes the storage nor runs the
# initcode, which would zero slot 0x01 in the correct-initcode case.
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
        (GasConsumer(gas=None, fork=fork), "oog-initcode", True),
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
