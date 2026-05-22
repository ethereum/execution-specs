"""
Test collision in CREATE/CREATE2 account creation, where the existing account
only has a non-zero storage slot set.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytecode,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7610.md"
REFERENCE_SPEC_VERSION = "80ef48d0bbb5a4939ade51caaaac57b5df6acd4e"

pytestmark = [
    pytest.mark.valid_from("Frontier"),
    pytest.mark.ported_from(
        [
            "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stSStoreTest/InitCollisionFiller.json",
            "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stSStoreTest/InitCollisionNonZeroNonceFiller.json",
            "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stSStoreTest/InitCollisionParisFiller.json",
        ],
        pr=["https://github.com/ethereum/execution-spec-tests/pull/636"],
    ),
    pytest.mark.parametrize(
        "collision_nonce,collision_balance,collision_code",
        [
            pytest.param(0, 0, b"\0", id="non-empty-code"),
            pytest.param(0, 1, b"", id="non-empty-balance"),
            pytest.param(1, 0, b"", id="non-empty-nonce"),
        ],
    ),
    pytest.mark.parametrize(
        "initcode",
        [
            pytest.param(
                Initcode(
                    deploy_code=Op.STOP,
                    initcode_prefix=Op.SSTORE(0, 1) + Op.SSTORE(1, 0),
                ),
                id="correct-initcode",
            ),
            pytest.param(Op.REVERT(0, 0), id="revert-initcode"),
            pytest.param(
                Op.MSTORE(0xFFFFFFFFFFFFFFFFFFFFFFFFFFF, 1), id="oog-initcode"
            ),
        ],
    ),
    # We need to modify the pre-alloc to include the collision
    pytest.mark.pre_alloc_mutable,
]


@pytest.mark.with_all_contract_creating_tx_types
@pytest.mark.eels_base_coverage
def test_init_collision_create_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    collision_nonce: int,
    collision_balance: int,
    collision_code: bytes,
    initcode: Bytecode,
    fork: Fork,
) -> None:
    """
    Test that a contract creation transaction exceptionally aborts when
    the target address has a non-empty storage, balance, nonce, or code.
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
        storage={0x01: 0x01},
        nonce=collision_nonce,
        balance=collision_balance,
        code=collision_code,
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
                storage={0x01: 0x01},
            ),
        },
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CREATE,
        pytest.param(
            Op.CREATE2, marks=pytest.mark.valid_from("Constantinople")
        ),
    ],
)
def test_init_collision_create_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    collision_nonce: int,
    collision_balance: int,
    collision_code: bytes,
    initcode: Bytecode,
) -> None:
    """
    Test that a contract creation opcode exceptionally aborts when the target
    address has a non-empty storage, balance, nonce, or code.
    """
    assert len(initcode) <= 32
    contract_creator_code = (
        # Reverts if and only if contract creation fails. In Frontier/Homestead
        # this runs out of gas, and every other fork jumps to a non-JUMPDEST.
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.JUMPI(
            condition=Op.ISZERO(opcode(value=0, offset=0, size=len(initcode))),
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
        opcode=opcode,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=gas_limiter_address,
        protected=False,
    )

    pre[created_contract_address] = Account(
        storage={0x01: 0x01},
        nonce=collision_nonce,
        balance=collision_balance,
        code=collision_code,
    )

    state_test(
        pre=pre,
        post={
            created_contract_address: Account(
                storage={0x01: 0x01},
            ),
            gas_limiter_address: Account(storage={0x01: 0x00}),
        },
        tx=tx,
    )
