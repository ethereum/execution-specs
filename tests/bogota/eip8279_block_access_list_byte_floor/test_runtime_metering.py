"""
Tests for the runtime block access list byte metering of
[EIP-8279: Block Access List Byte Floor](https://eips.ethereum.org/EIPS/eip-8279).
"""

from dataclasses import dataclass, field
from typing import Dict

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    EIPChecklist,
    Fork,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing import Macros as Om
from execution_testing.base_types import StorageRootType

from .helpers import floor_dominating_calldata
from .spec import ref_spec_8279

REFERENCE_SPEC_GIT_PATH = ref_spec_8279.git_path
REFERENCE_SPEC_VERSION = ref_spec_8279.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT = 1
# Past the slots `cold_sload` reads, so the witness is a fresh key.
WITNESS_SLOT = SLOT + 2
ORIGINAL_VALUE = 5
CONTRACT_BALANCE = 1
PEER_BALANCE = 1
DEPLOY_CODE = Op.STOP * 16


@dataclass
class Trigger:
    """
    One block access list contributor: the code that runs it in the
    tested contract, the bytes the EIP meters for it, and the state it
    leaves behind on success.
    """

    code: Bytecode
    bal_floor: int
    """Floor gas the code's block access list entries add."""
    gas_bound: int
    """Upper bound on the gas the code spends, child frames included."""
    halts: bool = False
    """Whether the code ends the frame, leaving no room for a witness."""
    contract_storage: StorageRootType = field(default_factory=dict)
    """Storage the contract starts with."""
    success_storage: StorageRootType = field(default_factory=dict)
    """The contract's storage after the trigger ran."""
    success_balance: int = CONTRACT_BALANCE
    """The contract's balance after the trigger ran."""
    success_post: Dict[Address, Account | None] = field(default_factory=dict)
    """Other accounts' state after the trigger ran."""
    failure_post: Dict[Address, Account | None] = field(default_factory=dict)
    """Other accounts' state when the transaction failed."""
    created_code: Bytes | None = None
    """Code the trigger deploys at the contract's next creation address."""
    endowment: int = 0
    """Balance the trigger endows the created account with."""


def build_trigger(name: str, fork: Fork, pre: Alloc) -> Trigger:
    """Build the named trigger, deploying any peer accounts it needs."""
    bal_floor = fork.block_access_list_floor_cost

    if name == "cold_sload":
        code = Op.POP(Op.SLOAD(SLOT)) + Op.POP(Op.SLOAD(SLOT + 1))
        return Trigger(code, bal_floor(storage_keys=2), code.gas_cost(fork))

    if name == "cold_sstore":
        code = Op.SSTORE(SLOT, 1, original_value=0, new_value=1)
        return Trigger(
            code,
            bal_floor(storage_keys=1, storage_values=1),
            code.gas_cost(fork),
            success_storage={SLOT: 1},
        )

    if name == "sstore_round_trip":
        # Writing the slot back to its transaction-start value turns the
        # change into a plain read, but the value bytes stay metered: the
        # count is an upper bound and never refunds.
        code = Op.SSTORE(
            SLOT, 6, original_value=ORIGINAL_VALUE, new_value=6
        ) + Op.SSTORE(
            SLOT,
            ORIGINAL_VALUE,
            key_warm=True,
            original_value=ORIGINAL_VALUE,
            current_value=6,
            new_value=ORIGINAL_VALUE,
        )
        return Trigger(
            code,
            bal_floor(storage_keys=1, storage_values=1),
            code.gas_cost(fork),
            contract_storage={SLOT: ORIGINAL_VALUE},
            success_storage={SLOT: ORIGINAL_VALUE},
        )

    if name == "sstore_repeated_writes":
        # The block access list keeps one post-value per changed slot,
        # so the value bytes are metered once, on the first change.
        code = Op.SSTORE(SLOT, 6, original_value=ORIGINAL_VALUE, new_value=6)
        for current_value, new_value in ((6, 7), (7, 8)):
            code += Op.SSTORE(
                SLOT,
                new_value,
                key_warm=True,
                original_value=ORIGINAL_VALUE,
                current_value=current_value,
                new_value=new_value,
            )
        return Trigger(
            code,
            bal_floor(storage_keys=1, storage_values=1),
            code.gas_cost(fork),
            contract_storage={SLOT: ORIGINAL_VALUE},
            success_storage={SLOT: 8},
        )

    if name == "cold_balance":
        peer = pre.fund_eoa(amount=PEER_BALANCE)
        code = Op.POP(Op.BALANCE(peer))
        return Trigger(code, bal_floor(addresses=1), code.gas_cost(fork))

    if name == "call_with_value":
        # The transfer changes both the caller's and the peer's balance.
        peer = pre.fund_eoa(amount=PEER_BALANCE)
        code = Op.POP(
            Op.CALL(gas=0, address=peer, value=1, value_transfer=True)
        )
        return Trigger(
            code,
            bal_floor(addresses=1, balances=2),
            code.gas_cost(fork),
            success_balance=CONTRACT_BALANCE - 1,
            success_post={peer: Account(balance=PEER_BALANCE + 1)},
            failure_post={peer: Account(balance=PEER_BALANCE)},
        )

    if name == "call_with_value_to_self":
        # The contract's own address is its first touch; a self transfer
        # changes no balance.
        code = Op.POP(
            Op.CALL(
                gas=0,
                address=Op.ADDRESS,
                value=1,
                address_warm=True,
                value_transfer=True,
            )
        )
        return Trigger(code, bal_floor(addresses=1), code.gas_cost(fork))

    if name == "callcode_with_value":
        # The value stays with the contract: only the peer's address.
        peer = pre.fund_eoa(amount=PEER_BALANCE)
        code = Op.POP(
            Op.CALLCODE(gas=0, address=peer, value=1, value_transfer=True)
        )
        return Trigger(
            code,
            bal_floor(addresses=1),
            code.gas_cost(fork),
            success_post={peer: Account(balance=PEER_BALANCE)},
        )

    if name == "call_delegated_target":
        # The target and the code address it delegates to both enter the
        # block access list.
        delegate = pre.deploy_contract(Op.STOP)
        target = pre.fund_eoa(amount=0, delegation=delegate)
        code = Op.POP(
            Op.CALL(gas=Op.GAS, address=target, delegated_address=True)
        )
        return Trigger(code, bal_floor(addresses=2), code.gas_cost(fork))

    if name == "selfdestruct_to_self":
        # A self sweep moves nothing, so only the contract's own address.
        code = Op.SELFDESTRUCT(Op.ADDRESS, address_warm=True)
        return Trigger(
            code, bal_floor(addresses=1), code.gas_cost(fork), halts=True
        )

    if name == "selfdestruct_with_balance":
        # The sweep changes both the contract's and the peer's balance.
        peer = pre.fund_eoa(amount=PEER_BALANCE)
        code = Op.SELFDESTRUCT(peer)
        return Trigger(
            code,
            bal_floor(addresses=1, balances=2),
            code.gas_cost(fork),
            halts=True,
            success_balance=0,
            success_post={
                peer: Account(balance=PEER_BALANCE + CONTRACT_BALANCE)
            },
            failure_post={peer: Account(balance=PEER_BALANCE)},
        )

    if name in ("create", "create_with_endowment"):
        endowment = 1 if name == "create_with_endowment" else 0
        initcode = Initcode(deploy_code=DEPLOY_CODE)
        code = Om.MSTORE(initcode, 0) + Op.POP(
            Op.CREATE(
                endowment,
                0,
                len(initcode),
                init_code_size=len(initcode),
                new_memory_size=len(initcode),
            )
        )
        # The new account's address and code, the creator's and the new
        # account's nonce, and both balances when endowed.
        create_floor = bal_floor(
            addresses=1,
            nonces=2,
            balances=2 * endowment,
            code_bytes=len(DEPLOY_CODE),
        )
        return Trigger(
            code,
            create_floor,
            code.gas_cost(fork) + initcode.gas_cost(fork),
            success_balance=CONTRACT_BALANCE - endowment,
            created_code=Bytes(DEPLOY_CODE),
            endowment=endowment,
        )

    raise ValueError(f"unknown trigger {name}")


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param("floor_binds", id="floor_binds"),
        pytest.param("out_of_gas", id="out_of_gas"),
    ],
)
@pytest.mark.parametrize(
    "trigger_name",
    [
        "cold_sload",
        "cold_sstore",
        "sstore_round_trip",
        "sstore_repeated_writes",
        "cold_balance",
        "call_with_value",
        "call_with_value_to_self",
        "callcode_with_value",
        "call_delegated_target",
        "selfdestruct_with_balance",
        "selfdestruct_to_self",
        "create",
        "create_with_endowment",
    ],
)
def test_runtime_metering(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    trigger_name: str,
) -> None:
    """
    Bytes an opcode adds to the block access list extend the floor at
    the per-byte floor rate, and a floor the gas limit cannot cover
    halts the transaction at the metering step.

    A data-heavy transaction whose static floor already dominates its
    execution calls a contract that runs one trigger, so the gas used
    shows the floor extension directly.
    """
    sender = pre.fund_eoa()
    trigger = build_trigger(trigger_name, fork, pre)

    # A witness write at the end proves the code ran to completion; it
    # is metered like any other store. A halting trigger is its own
    # witness.
    code = trigger.code
    bal_floor = trigger.bal_floor
    gas_bound = trigger.gas_bound
    success_storage = {**trigger.contract_storage, **trigger.success_storage}
    if not trigger.halts:
        witness = Op.SSTORE(WITNESS_SLOT, 1, original_value=0, new_value=1)
        code += witness
        bal_floor += fork.block_access_list_floor_cost(
            storage_keys=1, storage_values=1
        )
        gas_bound += witness.gas_cost(fork)
        success_storage[WITNESS_SLOT] = 1

    contract = pre.deploy_contract(
        code,
        balance=CONTRACT_BALANCE,
        storage=trigger.contract_storage,
    )
    success_post = dict(trigger.success_post)
    failure_post = dict(trigger.failure_post)
    if trigger.created_code is not None:
        created = compute_create_address(address=contract, nonce=1)
        success_post[created] = Account(
            nonce=1, balance=trigger.endowment, code=trigger.created_code
        )
        failure_post[created] = Account.NONEXISTENT

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()

    def total_cost(byte_count: int) -> int:
        return (
            intrinsic_calc(
                calldata=b"\x00" * byte_count,
                return_cost_deducted_prior_execution=True,
            )
            + gas_bound
        )

    def floor_cost(byte_count: int) -> int:
        return floor_calc(data=b"\x00" * byte_count)

    calldata = floor_dominating_calldata(total_cost, floor_cost)
    static_floor = floor_cost(len(calldata))
    extended_floor = static_floor + bal_floor

    if outcome == "floor_binds":
        tx = Transaction(
            sender=sender,
            to=contract,
            data=calldata,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=extended_floor
            ),
        )
        post: Dict[Address, Account | None] = {
            contract: Account(
                balance=trigger.success_balance, storage=success_storage
            ),
            **success_post,
        }
    elif outcome == "out_of_gas":
        # One short of the extended floor still covers the static floor
        # and the execution, so only the metering can halt the
        # transaction, which then consumes its whole gas limit.
        gas_limit = extended_floor - 1
        tx = Transaction(
            sender=sender,
            to=contract,
            data=calldata,
            gas_limit=gas_limit,
            expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit),
        )
        post = {
            contract: Account(
                balance=CONTRACT_BALANCE,
                storage=trigger.contract_storage,
            ),
            **failure_post,
        }
    else:
        raise ValueError(f"unknown outcome {outcome}")

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "accessed",
    [
        pytest.param(True, id="keys_read"),
        pytest.param(False, id="keys_unread"),
    ],
)
@pytest.mark.parametrize("key_count", [1, 8])
def test_access_listed_slots(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    accessed: bool,
    key_count: int,
) -> None:
    """
    A slot the access list pre-warmed is metered on its first access.

    The access list prices the slot key as transaction content, but the
    key enters the block access list only when the slot is read, so the
    warm ``SLOAD`` still meters it. Listed slots that are never read add
    nothing beyond the static floor.
    """
    sender = pre.fund_eoa()
    keys = [Hash(slot) for slot in range(key_count)]
    code = sum(
        (Op.POP(Op.SLOAD(slot)) for slot in range(key_count)), Bytecode()
    )
    contract = pre.deploy_contract(code if accessed else Op.STOP)
    access_list = [AccessList(address=contract, storage_keys=keys)]
    execution_gas = code.gas_cost(fork) if accessed else 0

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()

    def total_cost(byte_count: int) -> int:
        return (
            intrinsic_calc(
                calldata=b"\x00" * byte_count,
                access_list=access_list,
                return_cost_deducted_prior_execution=True,
            )
            + execution_gas
        )

    def floor_cost(byte_count: int) -> int:
        return floor_calc(data=b"\x00" * byte_count, access_list=access_list)

    calldata = floor_dominating_calldata(total_cost, floor_cost)
    static_floor = floor_cost(len(calldata))
    metered_floor = static_floor
    if accessed:
        metered_floor += fork.block_access_list_floor_cost(
            storage_keys=key_count
        )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=calldata,
        access_list=access_list,
        expected_receipt=TransactionReceipt(cumulative_gas_used=metered_floor),
    )
    state_test(pre=pre, tx=tx, post={})


def test_floor_limit_caps_runtime_floor(
    fork: Fork, pre: Alloc, state_test: StateTestFiller
) -> None:
    """
    The runtime floor is capped by the execution-gas limit, not only by
    the gas limit: metered bytes that would carry the floor past
    ``TX_MAX_GAS_LIMIT`` halt the transaction although spare gas remains.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    floor_calc = fork.transaction_data_floor_cost_calculator()
    sender = pre.fund_eoa()
    code = Op.POP(Op.SLOAD(SLOT)) + Op.SSTORE(
        WITNESS_SLOT, 1, original_value=0, new_value=1
    )
    contract = pre.deploy_contract(code)

    # The largest zero-byte calldata whose static floor fits the cap;
    # the trigger's bytes then push the floor past it.
    byte_count = 0
    while floor_calc(data=b"\x00" * (byte_count + 1)) <= cap:
        byte_count += 1
    calldata = b"\x00" * byte_count
    static_floor = floor_calc(data=calldata)
    assert (
        static_floor + fork.block_access_list_floor_cost(storage_keys=1) > cap
    )
    # Spare gas above the cap funds the state dimension only.
    gas_limit = cap + 100_000

    tx = Transaction(
        sender=sender,
        to=contract,
        data=calldata,
        gas_limit=gas_limit,
        # The halt forfeits the execution grant; the untouched state gas
        # reservoir returns, so the sender pays exactly the cap.
        expected_receipt=TransactionReceipt(cumulative_gas_used=cap),
    )
    state_test(pre=pre, tx=tx, post={contract: Account(storage={})})


def test_metering_out_of_gas_in_child_frame(
    fork: Fork, pre: Alloc, state_test: StateTestFiller
) -> None:
    """
    A metering out-of-gas in a child frame halts that frame alone: the
    deployment fails, the creating frame continues, and the bytes the
    child had not yet metered stay uncounted.
    """
    sender = pre.fund_eoa()
    initcode = Initcode(deploy_code=DEPLOY_CODE)
    witness = Op.SSTORE(WITNESS_SLOT, 1, original_value=0, new_value=1)
    create = Om.MSTORE(initcode, 0) + Op.POP(
        Op.CREATE(
            0,
            0,
            len(initcode),
            init_code_size=len(initcode),
            new_memory_size=len(initcode),
        )
    )
    code = witness + create
    contract = pre.deploy_contract(code)
    gas_bound = code.gas_cost(fork) + initcode.gas_cost(fork)

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()

    def total_cost(byte_count: int) -> int:
        return (
            intrinsic_calc(
                calldata=b"\x00" * byte_count,
                return_cost_deducted_prior_execution=True,
            )
            + gas_bound
        )

    def floor_cost(byte_count: int) -> int:
        return floor_calc(data=b"\x00" * byte_count)

    calldata = floor_dominating_calldata(total_cost, floor_cost)
    static_floor = floor_cost(len(calldata))
    # Everything metered before the deployed code: the witness, the new
    # account's address, and both nonces.
    metered_before_code = fork.block_access_list_floor_cost(
        storage_keys=1, storage_values=1, addresses=1, nonces=2
    )
    floor_before_code = static_floor + metered_before_code
    # One short of what the deployed code would add: the child halts at
    # the code's metering, the parent pays the floor reached so far.
    gas_limit = (
        floor_before_code
        + fork.block_access_list_floor_cost(code_bytes=len(DEPLOY_CODE))
        - 1
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=calldata,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=floor_before_code
        ),
    )
    post: Dict[Address, Account | None] = {
        # The creator's nonce advanced and the witness survived.
        contract: Account(nonce=2, storage={WITNESS_SLOT: 1}),
        compute_create_address(address=contract, nonce=1): Account.NONEXISTENT,
    }
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param("floor_binds", id="floor_binds"),
        pytest.param("out_of_gas", id="out_of_gas"),
    ],
)
def test_creation_transaction_deploys_code(
    fork: Fork, pre: Alloc, state_test: StateTestFiller, outcome: str
) -> None:
    """
    A creation transaction meters its deployed code like a ``CREATE``
    does: the floor grows by the code size at the floor rate, and a gas
    limit one short of that halts the deployment.
    """
    sender = pre.fund_eoa()
    # Zero padding makes the init code floor-heavy: 64 floor gas per
    # byte against 4 of intrinsic gas.
    initcode = Initcode(deploy_code=DEPLOY_CODE, initcode_length=4_000)
    floor = fork.transaction_data_floor_cost_calculator()(
        data=initcode, contract_creation=True
    )
    consumed = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode,
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + initcode.gas_cost(fork)
    )
    assert consumed < floor, "the floor must dominate the deployment"
    paid_floor = floor + fork.block_access_list_floor_cost(
        code_bytes=len(DEPLOY_CODE)
    )
    created = compute_create_address(address=sender, nonce=0)

    if outcome == "floor_binds":
        tx = Transaction(
            sender=sender,
            to=None,
            data=initcode,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=paid_floor
            ),
        )
        post: Dict[Address, Account | None] = {
            created: Account(code=DEPLOY_CODE)
        }
    elif outcome == "out_of_gas":
        gas_limit = paid_floor - 1
        tx = Transaction(
            sender=sender,
            to=None,
            data=initcode,
            gas_limit=gas_limit,
            expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit),
        )
        post = {created: Account.NONEXISTENT}
    else:
        raise ValueError(f"unknown outcome {outcome}")

    state_test(pre=pre, tx=tx, post=post)
