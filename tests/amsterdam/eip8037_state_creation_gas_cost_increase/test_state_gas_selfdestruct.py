"""
Test SELFDESTRUCT state gas charging under EIP-8037.

SELFDESTRUCT charges new-account state gas of state gas when the
beneficiary account does not exist AND the originating contract has
a nonzero balance. No state gas is charged when the beneficiary
already exists or the originator has zero balance.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Header,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_charges_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to non-existent beneficiary charges state gas.

    When the beneficiary does not exist and the originator has nonzero
    balance, SELFDESTRUCT charges new-account state gas for
    creating the new beneficiary account.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    # Non-existent beneficiary
    beneficiary = 0xDEAD

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_existing_beneficiary_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to existing beneficiary charges no state gas.

    When the beneficiary already exists, no new account is created
    and no state gas is charged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    beneficiary = pre.fund_eoa(amount=0)

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_zero_balance_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT with zero balance charges no state gas.

    When the originating contract has zero balance, no value is
    transferred, so no new account is created even if the beneficiary
    does not exist.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    # Non-existent beneficiary but contract has zero balance
    beneficiary = 0xDEAD

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=0,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_state_gas_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT state gas drawn from reservoir.

    Provide gas above TX_MAX_GAS_LIMIT so the new account state gas
    for the non-existent beneficiary is drawn from the reservoir.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    beneficiary = 0xDEAD

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_to_self_in_create_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to self in the transaction the contract was created.

    When a contract created in the current transaction SELFDESTRUCTs
    to itself, the balance is burned and the account is deleted. No
    new account state gas is charged since the beneficiary already
    exists.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()

    inner_code = Op.SELFDESTRUCT(Op.ADDRESS)

    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(inner_code), "big")
                << (256 - 8 * len(inner_code)),
            )
            + Op.POP(Op.CREATE(1, 0, len(inner_code)))
        ),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap * 2,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gas accounting for SELFDESTRUCT to new beneficiary.

    A contract with nonzero balance SELFDESTRUCTs to a non-existent
    beneficiary, charging GAS_NEW_ACCOUNT state gas. The block must
    be accepted with correct 2D gas accounting in the header.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    beneficiary = pre.fund_eoa(amount=0)

    storage = Storage()
    inner = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )
    caller = pre.deploy_contract(
        code=(
            Op.CALL(gas=100_000, address=inner)
            + Op.SSTORE(storage.store_next(1, "completed"), 1)
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx]),
        ],
        post={caller: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "num_slots",
    [
        pytest.param(0, id="no_storage"),
        pytest.param(1, id="one_slot"),
        pytest.param(5, id="five_slots"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_selfdestruct_refunds_account_and_storage(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    num_slots: int,
) -> None:
    """
    Verify same tx CREATE+SELFDESTRUCT refunds account and storage.

    Factory CREATE/CREATE2 initcode does N cold SSTOREs then
    SELFDESTRUCTs. Refund covers `GAS_NEW_ACCOUNT` plus each
    created slot's state gas. Under OLD behavior the state charges
    remain in `block_state_gas_used`. Under NEW they are refunded.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    init_code = Bytecode()
    for i in range(num_slots):
        init_code += Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )(i, 1)
    init_code += Op.SELFDESTRUCT.with_metadata(address_warm=True)(Op.ADDRESS)
    mstore_value, size = init_code_at_high_bytes(init_code)

    # Metadata so `.gas_cost(fork)` matches runtime charges.
    mstore = Op.MSTORE.with_metadata(new_memory_size=32, old_memory_size=0)(
        0, mstore_value
    )
    create_metadata = create_opcode.with_metadata(init_code_size=size)
    create_call = (
        create_metadata(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_metadata(value=0, offset=0, size=size)
    )
    factory_code = mstore + Op.POP(create_call)
    factory = pre.deploy_contract(code=factory_code)

    total_state_refund = new_account_state_gas + num_slots * sstore_state_gas
    # Subtract the state portion so tx_regular matches the header.
    tx_regular = (
        intrinsic_gas
        + factory_code.gas_cost(fork)
        + init_code.gas_cost(fork)
        - total_state_refund
    )

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit_cap + total_state_refund,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={},
    )


@pytest.mark.parametrize(
    "beneficiary_type,code_size",
    [
        pytest.param("self", 2, id="self_tiny"),
        pytest.param("self", 100, id="self_medium"),
        pytest.param("external", 100, id="external_medium"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_create_selfdestruct_refunds_code_deposit_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    code_size: int,
    beneficiary_type: str,
) -> None:
    """
    Verify same tx CREATE+SELFDESTRUCT refunds code deposit state gas.

    Factory CREATEs a contract deploying `code_size` bytes of code
    then CALLs it to trigger SELFDESTRUCT. Refund is account plus
    `code_size * cost_per_state_byte`. `external` beneficiary tests
    that the refund applies to the created account, not the
    destination of the ETH transfer.
    """
    assert code_size >= 2
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    code_deposit_state_gas = fork.code_deposit_state_gas(code_size=code_size)

    if beneficiary_type == "self":
        selfdestruct = Op.SELFDESTRUCT(Op.ADDRESS)
    else:
        beneficiary = pre.deploy_contract(code=Op.STOP)
        selfdestruct = Op.SELFDESTRUCT(beneficiary)
    sd_len = len(bytes(selfdestruct))
    assert code_size >= sd_len
    deployed = bytes(selfdestruct) + b"\x00" * (code_size - sd_len)
    initcode = Initcode(deploy_code=deployed)
    initcode_len = len(initcode)

    # Nest CREATE directly as the address argument to CALL so the
    # deployed contract's address flows via the stack, avoiding a
    # magic memory slot for address storage and an arbitrary gas
    # budget.
    factory_code = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        data_size=initcode_len,
        new_memory_size=initcode_len,
    ) + Op.POP(
        Op.CALL(
            gas=Op.GAS,
            address=Op.CREATE(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
                init_code_size=initcode_len,
            ),
        )
    )
    factory = pre.deploy_contract(code=factory_code)
    created_address = compute_create_address(address=factory, nonce=1)

    total_state_refund = new_account_state_gas + code_deposit_state_gas
    tx = Transaction(
        to=factory,
        data=bytes(initcode),
        gas_limit=gas_limit_cap + total_state_refund,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={created_address: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("EIP8037")
def test_create_selfdestruct_code_deposit_refund_header_check(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block header gas reflects the code-deposit state-gas
    refund on a same-tx CREATE plus SELFDESTRUCT.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    # Deployed code is sized so the code-deposit state gas would
    # dominate block regular gas if the refund did not land.
    selfdestruct = Op.SELFDESTRUCT(Op.ADDRESS)
    sd_len = len(bytes(selfdestruct))
    code_size = 256
    assert code_size >= sd_len
    deployed = bytes(selfdestruct) + b"\x00" * (code_size - sd_len)
    initcode = Initcode(deploy_code=deployed)
    initcode_len = len(initcode)
    code_deposit_state_gas = fork.code_deposit_state_gas(code_size=code_size)

    factory_code = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        data_size=initcode_len,
        new_memory_size=initcode_len,
    ) + Op.POP(
        Op.CALL(
            gas=Op.GAS,
            address=Op.CREATE(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
                init_code_size=initcode_len,
            ),
        )
    )
    factory = pre.deploy_contract(code=factory_code)
    created_address = compute_create_address(address=factory, nonce=1)

    total_state_refund = new_account_state_gas + code_deposit_state_gas
    tx = Transaction(
        to=factory,
        data=bytes(initcode),
        gas_limit=gas_limit_cap + total_state_refund,
        sender=pre.fund_eoa(),
    )

    # Empirical baseline: block_state_gas refunds to zero so the
    # header reports block regular only. Baseline regular must stay
    # below the code-deposit state gas so a missing refund would
    # push the header above this value.
    baseline_block_regular = 0x8EAE
    assert baseline_block_regular < code_deposit_state_gas, (
        "Baseline regular must be below code_deposit_state_gas so "
        "the mutation's un-refunded state_gas dominates the header."
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=baseline_block_regular),
            ),
        ],
        post={created_address: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("EIP8037")
def test_create_selfdestruct_no_double_refund_with_sstore_restoration(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SSTORE restoration and SELFDESTRUCT refunds do not stack.

    Initcode does SSTORE(0, 1) then SSTORE(0, 0) then SELFDESTRUCT.
    The 0 to x to 0 restoration refunds the slot inline. The end of
    tx selfdestruct refund scans `storage_writes[B]` and only counts
    non zero final values, so the restored slot is excluded and the
    end of tx refund is account only.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    init_code = (
        Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.SELFDESTRUCT.with_metadata(address_warm=True)(Op.ADDRESS)
    )
    mstore_value, size = init_code_at_high_bytes(init_code)

    mstore = Op.MSTORE.with_metadata(new_memory_size=32, old_memory_size=0)(
        0, mstore_value
    )
    create_call = Op.CREATE.with_metadata(init_code_size=size)(0, 0, size)
    factory_code = mstore + Op.POP(create_call)
    factory = pre.deploy_contract(code=factory_code)

    # Subtract both state charges (CREATE account + cold SSTORE) to
    # isolate the regular total.
    tx_regular = (
        intrinsic_gas
        + factory_code.gas_cost(fork)
        + init_code.gas_cost(fork)
        - new_account_state_gas
        - sstore_state_gas
    )

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit_cap + new_account_state_gas + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_pre_existing_account_no_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SELFDESTRUCT of a pre-existing account earns no refund.

    The same-tx-create guard (`address in tx_state.created_accounts`)
    is load-bearing: without it, destroying any account would leak
    state gas back into the reservoir.  A contract deployed in `pre`
    is destroyed by the tx; `accounts_to_delete` contains it but
    `created_accounts` does not, so no refund is applied.  The block
    header `gas_used` reflects the full regular-gas tx cost (no
    state-gas refund offset).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Victim deployed in `pre` (NOT same-tx-created).  SELFDESTRUCTs
    # to self so no new-account state gas is charged to the tx.
    victim_code = Op.SELFDESTRUCT.with_metadata(address_warm=True)(Op.ADDRESS)
    victim = pre.deploy_contract(code=victim_code)

    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=victim))
    caller = pre.deploy_contract(code=caller_code)

    # No refund offset: both caller_code and victim_code are pure
    # regular gas (SELFDESTRUCT to self, no value-to-new-account).
    tx_regular = (
        intrinsic_gas + caller_code.gas_cost(fork) + victim_code.gas_cost(fork)
    )

    tx = Transaction(
        to=caller,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    # Per EIP-6780, SELFDESTRUCT on a not-same-tx-created account
    # does not delete it — the account still exists after the tx.
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={victim: Account(code=victim_code)},
    )


@pytest.mark.parametrize(
    "num_hops",
    [
        pytest.param(1, id="single_hop"),
        pytest.param(2, id="two_hops"),
    ],
)
@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode in (Op.DELEGATECALL, Op.CALLCODE)
)
@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_via_delegatecall_chain(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_hops: int,
    call_opcode: Op,
) -> None:
    """
    Verify SELFDESTRUCT refund when the opcode executes in a nested
    DELEGATECALL/CALLCODE frame below a same-tx-created contract.

    A factory CREATEs contract A; A delegates down `num_hops` frames
    into a helper that runs SELFDESTRUCT(Op.ADDRESS). `current_target`
    is preserved by DELEGATECALL/CALLCODE, so A is queued for deletion
    and its account + code-deposit state gas is refunded at tx end.
    Exercises `accounts_to_delete` propagation across multiple
    `incorporate_child_on_success` hops.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    sstore_state_gas = fork.sstore_state_gas()

    # Bottom of the chain does the SELFDESTRUCT; intermediate helpers
    # just delegate further down.
    delegate_target = pre.deploy_contract(code=Op.SELFDESTRUCT(Op.ADDRESS))
    for _ in range(num_hops - 1):
        delegate_target = pre.deploy_contract(
            code=Op.POP(call_opcode(gas=Op.GAS, address=delegate_target))
            + Op.STOP,
        )

    # A's deployed runtime: one delegation into the top of the chain.
    deployed = bytes(
        Op.POP(call_opcode(gas=Op.GAS, address=delegate_target)) + Op.STOP
    )
    code_deposit_state_gas = fork.code_deposit_state_gas(
        code_size=len(deployed)
    )
    initcode = Initcode(deploy_code=deployed)
    initcode_len = len(initcode)

    # Slots 0 and 1 guard against a vacuously-NONEXISTENT A: slot 0
    # fails if CREATE silently returned 0, slot 1 fails if the factory
    # OOGed before completing the nested CALL.  TSTORE caches the
    # CREATE return so both can reuse it.
    factory_storage = Storage()
    factory_code = (
        Op.CALLDATACOPY(
            0,
            0,
            Op.CALLDATASIZE,
            data_size=initcode_len,
            new_memory_size=initcode_len,
        )
        + Op.TSTORE(
            0,
            Op.CREATE(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
                init_code_size=initcode_len,
            ),
        )
        + Op.SSTORE(
            factory_storage.store_next(1, "create_returned_nonzero"),
            Op.ISZERO(Op.ISZERO(Op.TLOAD(0))),
        )
        + Op.SSTORE(
            factory_storage.store_next(1, "call_returned_success"),
            Op.CALL(gas=Op.GAS, address=Op.TLOAD(0)),
        )
    )
    factory = pre.deploy_contract(code=factory_code)
    created_address = compute_create_address(address=factory, nonce=1)

    # Reservoir must also cover the two fresh SSTORE markers.
    total_state_refund = new_account_state_gas + code_deposit_state_gas
    tx = Transaction(
        to=factory,
        data=bytes(initcode),
        gas_limit=gas_limit_cap + total_state_refund + 2 * sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={
            created_address: Account.NONEXISTENT,
            factory: Account(storage=factory_storage),
        },
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_no_regular_account_creation_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SELFDESTRUCT to a new beneficiary does not charge a
    regular account-creation cost on top of state gas.
    """
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    beneficiary = pre.fund_eoa(amount=0)

    victim_code = Op.SELFDESTRUCT(beneficiary)
    victim = pre.deploy_contract(code=victim_code, balance=1)

    # Tight budget: slack is less than the old pre-Amsterdam regular
    # account-creation cost, so any extra regular draw would OOG.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    tx = Transaction(
        to=victim,
        gas_limit=(
            intrinsic
            + victim_code.gas_cost(fork)
            + new_account_state_gas
            + 20_000
        ),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={beneficiary: Account(balance=1)}, tx=tx)
