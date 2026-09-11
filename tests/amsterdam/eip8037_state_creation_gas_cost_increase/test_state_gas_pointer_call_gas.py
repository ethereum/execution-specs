"""
Pointer vs direct call gas under EIP-8037's 2D model.

Amsterdam counterparts of Prague's
``test_gas_diff_pointer_vs_direct_call`` and
``test_pointer_call_followed_by_direct_call``.

The ``GAS`` opcode reports ``gas_left`` only (not the state-gas reservoir).
These tests fund the reservoir so SSTORE state charges are invisible to
``GAS``; the measured delta is therefore the execution component of the
call plus the outer measurement ``SSTORE``, matching the Prague layout
but with Amsterdam execution costs and CALL warmth.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

from enum import Enum

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

# Remaining push/add overhead beyond the priced SLOAD/SSTORE/CALL pieces
# in ``SSTORE(slot, ADD(SLOAD(slot), 1))`` — same constant as Prague.
_OPCODES_PRICE = 37


class AccessListCall(Enum):
    """Add addresses to access list."""

    NONE = 1
    IN_NORMAL_TX_ONLY = 2
    IN_POINTER_TX_ONLY = 3
    IN_BOTH_TX = 4


class PointerDefinition(Enum):
    """Define pointer in transactions."""

    SEPARATE = 1
    IN_NORMAL_TX_ONLY = 2
    IN_POINTER_TX_ONLY = 3
    IN_BOTH_TX = 4


class AccessListTo(Enum):
    """Define access list to."""

    POINTER_ADDRESS = 1
    CONTRACT_ADDRESS = 2


def _sstore_state_gas(fork: Fork) -> int:
    """Return EIP-8037 state gas for a zero-to-nonzero SSTORE."""
    return Op.SSTORE(new_value=1).state_cost(fork)


def _measured_call_gas(
    fork: Fork,
    *,
    call_address_warm: bool,
    sload_warm: bool,
    delegation_target_warm: bool | None = None,
) -> int:
    """
    Return the ``GAS`` delta for ``GAS; CALL; SSTORE(delta)`` when the
    reservoir covers all SSTORE state charges.

    Mirrors the Prague breakdown: outer measurement SSTORE (execution
    only, key treated warm as in the Prague fixtures), CALL base, inner
    SLOAD, optional cold/warm access to the delegation target, plus the
    shared push/add overhead.
    """
    cost = (
        Op.SSTORE(key_warm=True, new_value=1).execution_cost(fork)
        + Op.CALL(address_warm=call_address_warm).gas_cost(fork)
        + Op.SLOAD(key_warm=sload_warm).gas_cost(fork)
        + _OPCODES_PRICE
    )
    if delegation_target_warm is not None:
        cost += Op.CALL(address_warm=delegation_target_warm).gas_cost(fork)
    return cost


def _auth_for_pointer(
    contract: Address, pointer_a: Address
) -> list[AuthorizationTuple]:
    """Return a fresh-delegation auth for an existing authority."""
    return [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=pointer_a,
            creates_account=False,
            writes_delegation=True,
        )
    ]


@pytest.mark.parametrize(
    "access_list_rule",
    [
        AccessListCall.NONE,
        AccessListCall.IN_BOTH_TX,
        AccessListCall.IN_NORMAL_TX_ONLY,
        AccessListCall.IN_POINTER_TX_ONLY,
    ],
)
@pytest.mark.parametrize(
    "pointer_definition",
    [
        PointerDefinition.SEPARATE,
        PointerDefinition.IN_BOTH_TX,
        PointerDefinition.IN_NORMAL_TX_ONLY,
        PointerDefinition.IN_POINTER_TX_ONLY,
    ],
)
@pytest.mark.parametrize(
    "access_list_to",
    [AccessListTo.POINTER_ADDRESS, AccessListTo.CONTRACT_ADDRESS],
)
@pytest.mark.valid_from("EIP8037")
def test_gas_diff_pointer_vs_direct_call(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    access_list_rule: AccessListCall,
    pointer_definition: PointerDefinition,
    access_list_to: AccessListTo,
) -> None:
    """
    Check the gas difference when calling the contract directly vs as a
    pointer under EIP-8037.

    Same AccessList / AuthTuple matrix as Prague's
    ``test_gas_diff_pointer_vs_direct_call``, but with a funded state-gas
    reservoir so ``GAS`` only sees execution costs.
    """
    env = Environment()
    sstore_state = _sstore_state_gas(fork)
    # Cover outer measurement SSTORE + inner SSTORE (+ auth AUTH_BASE).
    reservoir = 3 * sstore_state + fork.gas_costs().AUTH_BASE

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()
    call_worked = 1

    direct_account_warm = access_list_rule in [
        AccessListCall.IN_NORMAL_TX_ONLY,
        AccessListCall.IN_BOTH_TX,
    ]
    direct_storage_warm = direct_account_warm
    direct_call_gas = _measured_call_gas(
        fork,
        call_address_warm=direct_account_warm,
        sload_warm=direct_storage_warm,
    )

    pointer_account_warm = (
        pointer_definition
        in [
            PointerDefinition.IN_BOTH_TX,
            PointerDefinition.IN_POINTER_TX_ONLY,
        ]
        or access_list_rule
        in [
            AccessListCall.IN_BOTH_TX,
            AccessListCall.IN_POINTER_TX_ONLY,
        ]
        and access_list_to == AccessListTo.POINTER_ADDRESS
    )
    pointer_storage_warm = (
        access_list_rule
        in [
            AccessListCall.IN_BOTH_TX,
            AccessListCall.IN_POINTER_TX_ONLY,
        ]
        and access_list_to == AccessListTo.POINTER_ADDRESS
    )
    pointer_contract_warm = (
        access_list_rule
        in [
            AccessListCall.IN_BOTH_TX,
            AccessListCall.IN_POINTER_TX_ONLY,
        ]
        and access_list_to == AccessListTo.CONTRACT_ADDRESS
    )
    pointer_call_gas = _measured_call_gas(
        fork,
        call_address_warm=pointer_account_warm,
        sload_warm=pointer_storage_warm,
        delegation_target_warm=pointer_contract_warm,
    )

    contract = pre.deploy_contract(
        code=Op.SSTORE(call_worked, Op.ADD(Op.SLOAD(call_worked), 1))
    )

    storage_normal: Storage = Storage()
    contract_test_normal = pre.deploy_contract(
        code=Op.GAS()
        + Op.POP(Op.CALL(gas=200_000, address=contract))
        + Op.SSTORE(
            storage_normal.store_next(direct_call_gas, "normal_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
    )

    storage_pointer: Storage = Storage()
    contract_test_pointer = pre.deploy_contract(
        code=Op.GAS()
        + Op.POP(Op.CALL(gas=200_000, address=pointer_a))
        + Op.SSTORE(
            storage_pointer.store_next(pointer_call_gas, "pointer_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
    )

    tx_0 = Transaction(
        to=1,
        sender=sender,
        state_gas_reservoir=reservoir,
        authorization_list=(
            _auth_for_pointer(contract, pointer_a)
            if pointer_definition == PointerDefinition.SEPARATE
            else None
        ),
    )

    tx = Transaction(
        to=contract_test_normal,
        sender=sender,
        state_gas_reservoir=reservoir,
        authorization_list=(
            _auth_for_pointer(contract, pointer_a)
            if pointer_definition
            in [
                PointerDefinition.IN_BOTH_TX,
                PointerDefinition.IN_NORMAL_TX_ONLY,
            ]
            else None
        ),
        access_list=(
            [
                AccessList(
                    address=contract,
                    storage_keys=[call_worked],
                )
            ]
            if access_list_rule
            in [
                AccessListCall.IN_BOTH_TX,
                AccessListCall.IN_NORMAL_TX_ONLY,
            ]
            else None
        ),
    )
    tx2 = Transaction(
        to=contract_test_pointer,
        sender=sender,
        state_gas_reservoir=reservoir,
        authorization_list=(
            _auth_for_pointer(contract, pointer_a)
            if pointer_definition
            in [
                PointerDefinition.IN_BOTH_TX,
                PointerDefinition.IN_POINTER_TX_ONLY,
            ]
            else None
        ),
        access_list=(
            [
                AccessList(
                    address=(
                        pointer_a
                        if access_list_to == AccessListTo.POINTER_ADDRESS
                        else contract
                    ),
                    storage_keys=[call_worked],
                )
            ]
            if access_list_rule
            in [
                AccessListCall.IN_BOTH_TX,
                AccessListCall.IN_POINTER_TX_ONLY,
            ]
            else None
        ),
    )

    post = {
        contract: Account(storage={call_worked: 1}),
        pointer_a: Account(storage={call_worked: 1}),
        contract_test_normal: Account(storage=storage_normal),
        contract_test_pointer: Account(storage=storage_pointer),
    }
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[Block(txs=[tx_0]), Block(txs=[tx]), Block(txs=[tx2])],
    )


@pytest.mark.valid_from("EIP8037")
def test_pointer_call_followed_by_direct_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Pointer call then direct call: account warms, storage stays cold.

    Amsterdam counterpart of Prague's
    ``test_pointer_call_followed_by_direct_call``. Reservoir-funded so
    ``GAS`` reports execution-only costs under the 2D model.
    """
    env = Environment()
    sstore_state = _sstore_state_gas(fork)
    # Two inner SSTOREs (pointer + contract) + two outer measurement stores.
    reservoir = 4 * sstore_state + fork.gas_costs().AUTH_BASE

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()
    call_worked = 1

    pointer_call_gas = _measured_call_gas(
        fork,
        call_address_warm=True,  # pointer warmed by same-tx auth
        sload_warm=False,
        delegation_target_warm=False,  # contract still cold
    )
    direct_call_gas = _measured_call_gas(
        fork,
        call_address_warm=True,  # contract warmed by prior pointer resolve
        sload_warm=False,  # storage warmth is per-account; still cold
    )

    contract = pre.deploy_contract(
        code=Op.SSTORE(call_worked, Op.ADD(Op.SLOAD(call_worked), 1))
    )

    storage_test_gas: Storage = Storage()
    contract_test_gas = pre.deploy_contract(
        code=Op.GAS()
        + Op.POP(Op.CALL(gas=200_000, address=pointer_a))
        + Op.SSTORE(
            storage_test_gas.store_next(
                pointer_call_gas, "pointer_call_price"
            ),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
        + Op.GAS()
        + Op.POP(Op.CALL(gas=200_000, address=contract))
        + Op.SSTORE(
            storage_test_gas.store_next(direct_call_gas, "direct_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
    )

    tx = Transaction(
        to=contract_test_gas,
        sender=sender,
        state_gas_reservoir=reservoir,
        authorization_list=_auth_for_pointer(contract, pointer_a),
    )

    post = {
        contract: Account(storage={call_worked: 1}),
        pointer_a: Account(storage={call_worked: 1}),
        contract_test_gas: Account(storage=storage_test_gas),
    }
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
