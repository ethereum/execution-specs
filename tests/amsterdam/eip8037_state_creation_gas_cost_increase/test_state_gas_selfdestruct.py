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


@pytest.mark.parametrize("funding", ["reservoir", "spill"])
@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    funding: str,
) -> None:
    """
    Test SELFDESTRUCT to a non-existent beneficiary bills NEW_ACCOUNT.

    A contract with nonzero balance self-destructs to a non-alive
    beneficiary, charging new-account state gas. The charge is billed
    identically whether drawn from the reservoir (out-of-cap tx) or
    spilled into `gas_left` (in-cap tx): the block bills NEW_ACCOUNT in
    the state dimension and the beneficiary is created.
    """
    beneficiary = pre.nonexistent_account()
    code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    state_cost = code.state_cost(fork)

    contract = pre.deploy_contract(code=code, balance=1)
    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        state_gas_reservoir=(state_cost if funding == "reservoir" else 0),
    )

    state_test(
        pre=pre,
        post={
            beneficiary: Account(balance=1),
            contract: Account(balance=0),
        },
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_cost),
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_existing_beneficiary_no_state_gas(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """
    Test SELFDESTRUCT to existing beneficiary charges no state gas.

    When the beneficiary already exists, no new account is created
    and no state gas is charged.
    """
    beneficiary = pre.fund_eoa(amount=1)
    code = Op.SELFDESTRUCT(beneficiary, account_new=False)

    contract = pre.deploy_contract(
        code=code,
        balance=1,
    )

    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + code.execution_cost(fork)
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={beneficiary: Account(balance=2), contract: Account(balance=0)},
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_zero_balance_no_state_gas(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """
    Test SELFDESTRUCT with zero balance charges no state gas.

    When the originating contract has zero balance, no value is
    transferred, so no new account is created even if the beneficiary
    does not exist.
    """
    # Non-existent beneficiary but contract has zero balance
    beneficiary = pre.nonexistent_account()
    code = Op.SELFDESTRUCT(beneficiary, account_new=False)

    contract = pre.deploy_contract(
        code=code,
        balance=0,
    )

    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + code.execution_cost(fork)
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={beneficiary: Account.NONEXISTENT, contract: Account(balance=0)},
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_to_self_in_create_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to self in the transaction the contract was created.

    When a contract created in the current transaction SELFDESTRUCTs
    to itself, the balance stays at the cleared account. No new account
    state gas is charged for the sweep since the beneficiary already
    exists: the CREATE paid it, and the clearing does not refill it.
    """
    inner_code = Op.SELFDESTRUCT(
        Op.ADDRESS,
        # gas accounting
        address_warm=True,
        account_new=False,
    )
    mstore_value, size = init_code_at_high_bytes(inner_code)

    code = Op.MSTORE(0, mstore_value) + Op.POP(
        Op.CREATE(1, 0, size, init_code_size=size, new_memory_size=32)
    )
    contract = pre.deploy_contract(code=code, balance=1)
    created = compute_create_address(address=contract, nonce=1)

    expected_state = code.state_cost(fork)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=expected_state,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_state),
            ),
        ],
        post={
            contract: Account(balance=0, nonce=2),
            created: Account(balance=1, nonce=0, code=b""),
        },
    )


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
    beneficiary = pre.nonexistent_account()

    inner_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    inner = pre.deploy_contract(
        code=inner_code,
        balance=1,
    )

    storage = Storage()
    call_code = Op.CALL(gas=100_000, address=inner) + Op.SSTORE(
        storage.store_next(1, "completed"), 1
    )
    caller = pre.deploy_contract(
        code=call_code,
    )

    state_cost = inner_code.state_cost(fork) + call_code.state_cost(fork)
    tx = Transaction(
        to=caller,
        state_gas_reservoir=state_cost,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=state_cost)),
        ],
        post={caller: Account(storage=storage)},
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_state_gas_refilled_on_ancestor_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SELFDESTRUCT state gas is refilled when an ancestor reverts.

    The inner frame spills the NEW_ACCOUNT charge and self-destructs
    successfully, then the caller reverts: the beneficiary creation
    rolls back and the spilled state charge is refilled. The EIP-8038
    execution account-write charge for the attempted empty-account value
    transfer remains billed.
    """
    beneficiary = 0xDEAD
    inner_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    inner = pre.deploy_contract(code=inner_code, balance=1)
    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=inner)) + Op.REVERT(0, 0)
    caller = pre.deploy_contract(code=caller_code)

    expected_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
    )
    tx = Transaction(to=caller, sender=pre.fund_eoa())

    state_test(
        pre=pre,
        post={beneficiary: Account.NONEXISTENT, inner: Account(balance=1)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_execution),
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
def test_create_selfdestruct_no_refund_account_and_storage(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    num_slots: int,
) -> None:
    """Verify same tx CREATE+SELFDESTRUCT does not refund state gas."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    init_code = Bytecode()
    for i in range(num_slots):
        init_code += Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )(i, 1)
    init_code += Op.SELFDESTRUCT(
        Op.ADDRESS, account_new=False, address_warm=True
    )
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

    total_state_gas = factory_code.state_cost(fork) + init_code.state_cost(
        fork
    )
    execution_used = (
        intrinsic_gas
        + factory_code.execution_cost(fork)
        + init_code.execution_cost(fork)
    )

    assert total_state_gas > execution_used, (
        f"test requires state gas > execution gas, got "
        f"state={total_state_gas} execution={execution_used}"
    )
    expected_gas_used = total_state_gas

    tx = Transaction(
        to=factory,
        state_gas_reservoir=total_state_gas,
        sender=pre.fund_eoa(),
    )

    created = compute_create_address(
        address=factory, nonce=1, opcode=create_opcode
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used)),
        ],
        post={created: Account.NONEXISTENT},
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
def test_create_selfdestruct_no_refund_code_deposit_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    code_size: int,
    beneficiary_type: str,
) -> None:
    """
    Verify same tx CREATE+SELFDESTRUCT does not refund code deposit
    state gas.
    """
    assert code_size >= 2

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

    total_state_gas = factory_code.state_cost(fork) + initcode.state_cost(fork)
    total_execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + factory_code.execution_cost(fork)
        + initcode.execution_cost(fork)
    )

    assert total_state_gas > total_execution_gas, (
        "requires state gas > execution gas"
    )

    tx = Transaction(
        to=factory,
        data=bytes(initcode),
        state_gas_reservoir=total_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=total_state_gas))
        ],
        post={created_address: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("EIP8037")
def test_create_selfdestruct_code_deposit_no_refund_header_check(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block header gas reflects the full account plus code-deposit
    state-gas charge on a same-tx CREATE+SELFDESTRUCT.
    """
    selfdestruct = Op.SELFDESTRUCT(Op.ADDRESS)
    sd_len = len(bytes(selfdestruct))
    code_size = 256
    assert code_size >= sd_len
    deployed = bytes(selfdestruct) + b"\x00" * (code_size - sd_len)
    initcode = Initcode(deploy_code=deployed)
    initcode_len = len(initcode)

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

    total_state_gas = factory_code.state_cost(fork) + initcode.state_cost(fork)
    tx = Transaction(
        to=factory,
        data=bytes(initcode),
        state_gas_reservoir=total_state_gas,
        sender=pre.fund_eoa(),
    )

    baseline_block_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + factory_code.execution_cost(fork)
        + initcode.execution_cost(fork)
    )
    assert total_state_gas > baseline_block_execution, (
        "requires state gas > execution gas"
    )
    expected_gas_used = max(baseline_block_execution, total_state_gas)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={created_address: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("EIP8037")
def test_create_selfdestruct_sstore_restoration_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SSTORE restoration still refunds its slot state gas when
    the surrounding contract SELFDESTRUCTs.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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

    new_account_state_gas = factory_code.state_cost(fork)
    state_used = new_account_state_gas
    execution_used = (
        intrinsic_gas
        + factory_code.execution_cost(fork)
        + init_code.execution_cost(fork)
    )
    expected_gas_used = max(execution_used, state_used)
    assert expected_gas_used == state_used, (
        "expected state gas to dominate execution gas"
    )

    tx = Transaction(
        to=factory,
        state_gas_reservoir=new_account_state_gas + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used)),
        ],
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
    header `gas_used` reflects the full execution-gas tx cost (no
    state-gas refund offset).
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Victim deployed in `pre` (NOT same-tx-created).  SELFDESTRUCTs
    # to self so no new-account state gas is charged to the tx.
    victim_code = Op.SELFDESTRUCT.with_metadata(address_warm=True)(Op.ADDRESS)
    victim = pre.deploy_contract(code=victim_code)

    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=victim))
    caller = pre.deploy_contract(code=caller_code)

    # No refund offset: both caller_code and victim_code are pure
    # execution gas (SELFDESTRUCT to self, no value-to-new-account).
    tx_execution = (
        intrinsic_gas
        + caller_code.execution_cost(fork)
        + victim_code.execution_cost(fork)
    )

    tx = Transaction(
        to=caller,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    # Per EIP-6780, SELFDESTRUCT on a not-same-tx-created account
    # does not delete it — the account still exists after the tx.
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_execution))],
        post={victim: Account(code=victim_code)},
    )


@pytest.mark.parametrize(
    "num_hops",
    [
        pytest.param(1, id="single_hop"),
        pytest.param(2, id="two_hops"),
    ],
)
@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_via_delegatecall_chain_no_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_hops: int,
    call_opcode: Op,
) -> None:
    """
    Verify SELFDESTRUCT in a nested DELEGATECALL/CALLCODE frame below
    a same-tx-created contract does not refund state gas.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Bottom of the chain does the SELFDESTRUCT; intermediate helpers
    # just delegate further down. Track each frame's bytecode so we
    # can sum its execution gas into `expected_gas_used` below.
    sd_code = Op.SELFDESTRUCT.with_metadata(address_warm=True)(Op.ADDRESS)
    chain_execution_gas = sd_code.execution_cost(fork)
    delegate_target = pre.deploy_contract(code=sd_code)
    for _ in range(num_hops - 1):
        hop_code = (
            Op.POP(
                call_opcode.with_metadata(address_warm=False)(
                    gas=Op.GAS, address=delegate_target
                )
            )
            + Op.STOP
        )
        chain_execution_gas += hop_code.execution_cost(fork)
        delegate_target = pre.deploy_contract(code=hop_code)

    # A's deployed runtime: one delegation into the top of the chain.
    deployed_code = (
        Op.POP(
            call_opcode.with_metadata(address_warm=False)(
                gas=Op.GAS, address=delegate_target
            )
        )
        + Op.STOP
    )
    deployed = bytes(deployed_code)
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
            Op.CREATE.with_metadata(init_code_size=initcode_len)(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
            ),
        )
        + Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )(
            factory_storage.store_next(1, "create_returned_nonzero"),
            Op.ISZERO(Op.ISZERO(Op.TLOAD(0))),
        )
        + Op.SSTORE.with_metadata(
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )(
            factory_storage.store_next(1, "call_returned_success"),
            Op.CALL.with_metadata(address_warm=True)(
                gas=Op.GAS, address=Op.TLOAD(0)
            ),
        )
    )
    factory = pre.deploy_contract(code=factory_code)
    created_address = compute_create_address(address=factory, nonce=1)

    total_state_gas = factory_code.state_cost(fork) + initcode.state_cost(fork)
    execution_used = (
        intrinsic_gas
        + factory_code.execution_cost(fork)
        + initcode.execution_cost(fork)
        + deployed_code.execution_cost(fork)
        + chain_execution_gas
    )
    expected_gas_used = max(execution_used, total_state_gas)

    tx = Transaction(
        to=factory,
        data=bytes(initcode),
        state_gas_reservoir=total_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            )
        ],
        post={
            created_address: Account.NONEXISTENT,
            factory: Account(storage=factory_storage),
        },
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_account_write_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SELFDESTRUCT to a new beneficiary charges `ACCOUNT_WRITE`
    execution gas plus the account-creation state gas, and not the
    legacy combined execution account-creation cost.
    """
    # TODO: Modify to subcall scenario
    beneficiary = pre.fund_eoa(amount=0)

    victim_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    victim = pre.deploy_contract(code=victim_code, balance=1)

    # Tight budget: slack is less than the legacy 25,000 execution
    # account-creation cost minus `ACCOUNT_WRITE`, so any execution draw
    # beyond `ACCOUNT_WRITE` would OOG. The opcode metadata folds the
    # `ACCOUNT_WRITE` execution cost and the account-creation state gas
    # into `gas_cost`.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = intrinsic + victim_code.gas_cost(fork)
    tx = Transaction(
        to=victim,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={beneficiary: Account(balance=1)}, tx=tx)


@pytest.mark.parametrize(
    "tx_value,beneficiary_kind",
    [
        pytest.param(0, "self", id="value0_to_self"),
        pytest.param(0, "existing", id="value0_to_existing"),
        pytest.param(0, "empty", id="value0_to_empty"),
        pytest.param(1, "self", id="value1_to_self"),
        pytest.param(1, "existing", id="value1_to_existing"),
        pytest.param(1, "empty", id="value1_to_empty"),
    ],
)
@pytest.mark.pre_alloc_mutable()
@pytest.mark.valid_from("EIP8037")
def test_create_tx_selfdestruct_initcode_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_value: int,
    beneficiary_kind: str,
) -> None:
    """
    Verify a creation tx whose initcode SELFDESTRUCTs the new contract
    still pays the top-frame NEW_ACCOUNT state gas.
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()

    sender = pre.fund_eoa(amount=10**18)
    contract_addr = compute_create_address(address=sender, nonce=0)

    if beneficiary_kind == "self":
        beneficiary = contract_addr
    elif beneficiary_kind == "existing":
        beneficiary = pre.deploy_contract(code=Op.STOP)
    else:
        beneficiary = pre.fund_eoa(amount=0)

    creates_new_beneficiary = beneficiary_kind == "empty" and tx_value > 0

    # `current_target` is added to `accessed_addresses` at message
    # entry, so SELFDESTRUCT to self skips the cold-access surcharge.
    if beneficiary_kind == "self":
        init_code = Op.SELFDESTRUCT.with_metadata(
            address_warm=True, account_new=creates_new_beneficiary
        )(beneficiary)
    else:
        init_code = Op.SELFDESTRUCT.with_metadata(
            account_new=creates_new_beneficiary
        )(beneficiary)
    intrinsic_execution = intrinsic_calc(
        calldata=bytes(init_code), contract_creation=True
    )

    expected_state = fork.transaction_top_frame_state_gas(
        contract_creation=True
    ) + init_code.state_cost(fork)
    expected_execution = intrinsic_execution + init_code.execution_cost(fork)
    expected_gas_used = max(expected_execution, expected_state)
    assert expected_gas_used == expected_state, (
        "expected state gas to dominate execution gas"
    )

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=intrinsic_execution + 100_000 + expected_state,
        sender=sender,
        value=tx_value,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={},
    )
