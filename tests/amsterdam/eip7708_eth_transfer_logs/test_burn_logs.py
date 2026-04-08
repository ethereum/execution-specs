"""
Tests for EIP-7708 Burn logs.

Tests for the Burn(address,uint256) log emitted when:
- SELFDESTRUCT to self with nonzero balance
- Account created and destroyed in the same transaction
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Header,
    Initcode,
    Op,
    Opcodes,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import burn_log, ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = pytest.mark.valid_from("EIP7708")


def test_selfdestruct_to_self_pre_existing_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that selfdestruct-to-self emits NO log for pre-existing contracts.

    Burn log only emitted when created and destroyed in same tx.
    """
    contract_balance = 2000

    contract_code = Op.SELFDESTRUCT(Op.ADDRESS)
    contract = pre.deploy_contract(contract_code, balance=contract_balance)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    # Contract keeps its balance (not destroyed since not created in same tx)
    state_test(
        env=env,
        pre=pre,
        post={contract: Account(balance=contract_balance)},
        tx=tx,
    )


@pytest.mark.parametrize(
    "contract_balance",
    [
        pytest.param(2000, id="with_balance"),
        pytest.param(0, id="zero_balance"),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_selfdestruct_to_self_same_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    contract_balance: int,
    create_opcode: Op,
) -> None:
    """
    Test selfdestruct-to-self for same-tx created contracts.

    - With balance, Burn log emitted (burns ETH).
    - No balance, no logs expected.
    """
    initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    factory_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
    ) + create_opcode(
        value=Op.CALLVALUE, offset=32 - initcode_len, size=initcode_len
    )

    factory = pre.deploy_contract(factory_code)
    created_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode_bytes,
        opcode=create_opcode,
    )

    if contract_balance > 0:
        expected_logs = [
            transfer_log(sender, factory, contract_balance),
            transfer_log(factory, created_address, contract_balance),
            burn_log(created_address, contract_balance),
        ]
    else:
        expected_logs = []

    tx = Transaction(
        sender=sender,
        to=factory,
        value=contract_balance,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "contract_balance",
    [
        pytest.param(2000, id="with_balance"),
        pytest.param(0, id="zero_balance"),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_selfdestruct_to_different_address_same_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    contract_balance: int,
    create_opcode: Op,
) -> None:
    """
    Test same-tx selfdestruct to different address.

    With balance: Transfer log emitted. Zero balance: no logs.
    """
    beneficiary = pre.deploy_contract(Op.STOP)

    initcode = Op.SELFDESTRUCT(beneficiary)
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    factory_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
    ) + create_opcode(
        value=Op.CALLVALUE, offset=32 - initcode_len, size=initcode_len
    )

    factory = pre.deploy_contract(factory_code)
    created_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode_bytes,
        opcode=create_opcode,
    )

    if contract_balance > 0:
        expected_logs = [
            transfer_log(sender, factory, contract_balance),
            transfer_log(factory, created_address, contract_balance),
            transfer_log(created_address, beneficiary, contract_balance),
        ]
        post = {beneficiary: Account(balance=contract_balance)}
    else:
        expected_logs = []
        post = {}

    tx = Transaction(
        sender=sender,
        to=factory,
        value=contract_balance,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "to_self",
    [
        pytest.param(True, id="to_self"),
        pytest.param(False, id="to_other"),
    ],
)
@pytest.mark.parametrize(
    "call_twice,second_call_value",
    [
        pytest.param(True, 1, id="call_twice_with_value"),
        pytest.param(True, 0, id="call_twice"),
        pytest.param(False, 0, id="call_once"),
    ],
)
@pytest.mark.parametrize(
    "transfer_during_create",
    [
        pytest.param(True, id="transfer_during_create"),
        pytest.param(False, id="transfer_during_call"),
    ],
)
def test_selfdestruct_same_tx_via_call(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    to_self: bool,
    call_twice: bool,
    second_call_value: int,
    transfer_during_create: bool,
) -> None:
    """
    Test selfdestruct via CREATE-then-CALL (not initcode selfdestruct).

    Factory CREATEs contract with runtime code, then CALLs the contract that
    was just created to trigger SELFDESTRUCT (depending on
    `transfer_during_create`, the value of the contract is transferred during
    the CREATE or CALL opcodes). Contract is still in created_accounts.

    Depending on `call_twice`, the contract can be called twice during the
    same call frame where it was created.
    """
    contract_balance = 2000
    beneficiary = pre.deploy_contract(Op.STOP)

    if to_self:
        runtime_code = Op.SELFDESTRUCT(Op.ADDRESS)
    else:
        runtime_code = Op.SELFDESTRUCT(beneficiary)

    initcode = Initcode(deploy_code=runtime_code)
    initcode_len = len(initcode)

    if transfer_during_create:
        create_value = contract_balance
        first_call_value = 0
    else:
        create_value = 0
        first_call_value = contract_balance

    factory_code = (
        Om.MSTORE(initcode, 0)
        + Op.TSTORE(
            0, Op.CREATE(value=create_value, offset=0, size=initcode_len)
        )
        + Op.CALL(gas=100_000, address=Op.TLOAD(0), value=first_call_value)
    )
    if call_twice:
        factory_code += Op.CALL(
            gas=100_000, address=Op.TLOAD(0), value=second_call_value
        )

    factory = pre.deploy_contract(
        factory_code, balance=contract_balance + second_call_value
    )
    created_address = compute_create_address(address=factory, nonce=1)

    if to_self:
        expected_logs = [
            transfer_log(factory, created_address, contract_balance),
            burn_log(created_address, contract_balance),
        ]
        if call_twice and second_call_value > 0:
            expected_logs += [
                transfer_log(factory, created_address, second_call_value),
                burn_log(created_address, second_call_value),
            ]
        post = {}
    else:
        expected_logs = [
            transfer_log(factory, created_address, contract_balance),
            transfer_log(created_address, beneficiary, contract_balance),
        ]
        if call_twice and second_call_value > 0:
            expected_logs += [
                transfer_log(factory, created_address, second_call_value),
                transfer_log(created_address, beneficiary, second_call_value),
            ]
        post = {
            beneficiary: Account(balance=contract_balance + second_call_value)
        }

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=300_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "payer_code,eth_transferred",
    [
        pytest.param(
            Op.SELFDESTRUCT(Op.CALLDATALOAD(0)),
            True,
            id="via_selfdestruct",
        ),
        pytest.param(
            Op.CALL(
                gas=50_000,
                address=Op.CALLDATALOAD(0),
                value=Op.BALANCE(Op.ADDRESS),
            ),
            True,
            id="via_call",
        ),
        pytest.param(
            Op.CALL(
                gas=50_000,
                address=Op.CALLDATALOAD(0),
                value=Op.BALANCE(Op.ADDRESS),
            )
            + Op.REVERT(0, 0),
            False,
            id="via_call_revert",
        ),
    ],
)
@pytest.mark.parametrize(
    "to_self",
    [
        pytest.param(False, id="to_beneficiary"),
        pytest.param(True, id="to_self"),
    ],
)
def test_finalization_burn_logs(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    payer_code: Bytecode,
    eth_transferred: bool,
    to_self: bool,
) -> None:
    """
    Test Burn logs at finalization for post-selfdestruct balance.

    X contracts (x1, x2, x3) selfdestruct, then receive ETH via payer contracts
    (p1, p2, p3). At finalization, X contracts emit Burn logs for their
    in lexicographical address order (only if they received ETH).

    When to_self=True, X contracts SELFDESTRUCT to themselves (burning ETH
    with LOG2). When to_self=False, X contracts SELFDESTRUCT to a beneficiary
    (Transfer LOG3).
    """
    beneficiary = pre.deploy_contract(Op.STOP)

    # Pre-compute factory address and created contract addresses
    # so we can call them in reverse sorted order to prove finalization
    # logs are sorted by address, not by call order
    factory_address = compute_create_address(
        address=sender, nonce=sender.nonce
    )
    x1 = compute_create_address(address=factory_address, nonce=1)
    x2 = compute_create_address(address=factory_address, nonce=2)
    x3 = compute_create_address(address=factory_address, nonce=3)

    # sort() + call in REVERSE order to prove finalization
    # lexicographical sorting
    sorted_addrs = sorted([x1, x2, x3])
    reverse_sorted = list(reversed(sorted_addrs))

    # Runtime: selfdestruct on first call, STOP on subsequent calls
    target: Address | Opcodes = Op.ADDRESS if to_self else beneficiary
    runtime = (
        Op.TLOAD(0)
        + Op.ISZERO
        + Op.PUSH1(8)
        + Op.JUMPI
        + Op.STOP
        + Op.JUMPDEST
        + Op.TSTORE(0, 1)
        + Op.SELFDESTRUCT(target)
    )
    initcode = Initcode(deploy_code=runtime)
    initcode_len = len(initcode)

    # Payer contracts (p1, p2, p3) will send ETH to created contracts
    p1 = pre.deploy_contract(payer_code, balance=100)
    p2 = pre.deploy_contract(payer_code, balance=200)
    p3 = pre.deploy_contract(payer_code, balance=300)

    # Call p1/p2/p3 targeting addresses in REVERSE sorted order
    # This proves finalization logs are sorted by address, not call order
    factory_code = (
        Om.MSTORE(initcode, 0)
        # Create x1, x2, x3
        + Op.TSTORE(0, Op.CREATE(value=1000, offset=0, size=initcode_len))
        + Op.TSTORE(1, Op.CREATE(value=2000, offset=0, size=initcode_len))
        + Op.TSTORE(2, Op.CREATE(value=3000, offset=0, size=initcode_len))
        # Call x1, x2, x3 to trigger SELFDESTRUCT
        + Op.CALL(gas=100_000, address=Op.TLOAD(0), value=0)
        + Op.CALL(gas=100_000, address=Op.TLOAD(1), value=0)
        + Op.CALL(gas=100_000, address=Op.TLOAD(2), value=0)
        # p1/p2/p3 send ETH in REVERSE sorted address order
        + Op.MSTORE(0, reverse_sorted[0])
        + Op.CALL(gas=100_000, address=p1, args_offset=0, args_size=32)
        + Op.MSTORE(0, reverse_sorted[1])
        + Op.CALL(gas=100_000, address=p2, args_offset=0, args_size=32)
        + Op.MSTORE(0, reverse_sorted[2])
        + Op.CALL(gas=100_000, address=p3, args_offset=0, args_size=32)
    )

    factory_balance = 1000 + 2000 + 3000
    pre.fund_address(factory_address, factory_balance)

    # Amounts based on reverse call order:
    # p1→reverse[0], p2→reverse[1], p3→reverse[2]
    amounts = {
        reverse_sorted[0]: 100,
        reverse_sorted[1]: 200,
        reverse_sorted[2]: 300,
    }

    # Execution logs:
    # 1. CREATE x1, x2, x3 → LOG3 Transfer (factory → created)
    # 2. CALL x1, x2, x3 → LOG3 or LOG2 depending on `to_self`
    # 3. p1/p2/p3 send to reverse_sorted order
    execution_logs = [
        transfer_log(factory_address, x1, 1000),
        transfer_log(factory_address, x2, 2000),
        transfer_log(factory_address, x3, 3000),
    ]

    if to_self:
        # SELFDESTRUCT to self burns ETH → LOG2 Burn
        execution_logs.extend(
            [
                burn_log(x1, 1000),
                burn_log(x2, 2000),
                burn_log(x3, 3000),
            ]
        )
        beneficiary_balance = 0
    else:
        # SELFDESTRUCT to beneficiary → LOG3 Transfer
        execution_logs.extend(
            [
                transfer_log(x1, beneficiary, 1000),
                transfer_log(x2, beneficiary, 2000),
                transfer_log(x3, beneficiary, 3000),
            ]
        )
        beneficiary_balance = factory_balance

    if not eth_transferred:
        # Reverted CALLs emit no logs, no ETH transferred, no finalization logs
        finalization_logs = []
        post = {
            x1: Account.NONEXISTENT,
            x2: Account.NONEXISTENT,
            x3: Account.NONEXISTENT,
            beneficiary: Account(balance=beneficiary_balance),
            p1: Account(balance=100),
            p2: Account(balance=200),
            p3: Account(balance=300),
        }
    else:
        # p1/p2/p3 send ETH in reverse sorted order
        execution_logs.extend(
            [
                transfer_log(p1, reverse_sorted[0], 100),
                transfer_log(p2, reverse_sorted[1], 200),
                transfer_log(p3, reverse_sorted[2], 300),
            ]
        )
        # Finalization logs emitted in SORTED address order (not call order)
        finalization_logs = [
            burn_log(addr, amounts[addr]) for addr in sorted_addrs
        ]
        post = {
            x1: Account.NONEXISTENT,
            x2: Account.NONEXISTENT,
            x3: Account.NONEXISTENT,
            beneficiary: Account(balance=beneficiary_balance),
            p1: Account(balance=0),
            p2: Account(balance=0),
            p3: Account(balance=0),
        }

    tx = Transaction(
        sender=sender,
        to=None,
        value=0,
        data=factory_code,
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(
            logs=execution_logs + finalization_logs
        ),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "funded_after_selfdestruct",
    [
        pytest.param(True, id="funded_after_selfdestruct"),
        pytest.param(False, id="miner_fee_only"),
    ],
)
def test_selfdestruct_finalization_after_priority_fee(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    funded_after_selfdestruct: bool,
) -> None:
    """
    Verify finalization burn logs are emitted after priority fee payment.

    Sets coinbase to a contract that self-destructs in the same tx. The
    finalization burn log includes the priority fee, proving finalization
    happens after fee payment per EIP-7708.

    funded_after_selfdestruct:
    - if True: payer sends ETH, finalization = funding + priority_fee
    - if False: no payer, finalization = priority_fee only
    """
    contract_balance = 1000
    funding_amount = 10_000 if funded_after_selfdestruct else 0

    sender = pre.fund_eoa()

    factory_address = compute_create_address(address=sender, nonce=0)
    created_address = compute_create_address(address=factory_address, nonce=1)
    coinbase = created_address  # coinbase == self-destructed contract

    # inner contract: simple SELFDESTRUCT to self
    runtime_code = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode = Initcode(deploy_code=runtime_code)
    initcode_len = len(initcode)

    gas_costs = fork.gas_costs()
    mem_after_mstore = ((initcode_len + 31) // 32) * 32

    # The base factory code: CREATE + CALL to trigger selfdestruct
    factory_code = Om.MSTORE(
        initcode, 0, new_memory_size=mem_after_mstore
    ) + Op.CALL(
        gas=100_000,
        address=Op.CREATE(
            value=contract_balance,
            offset=0,
            size=initcode_len,
            init_code_size=initcode_len,
        ),
        address_warm=True,
    )

    # optionally add payer call to fund coinbase after selfdestruct
    payer = None
    payer_runtime_gas = 0
    if funded_after_selfdestruct:
        payer_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
        payer = pre.deploy_contract(payer_code, balance=funding_amount)
        factory_code += Op.MSTORE(0, created_address)
        factory_code += Op.CALL(
            gas=100_000, address=payer, args_offset=0, args_size=32
        )
        payer_runtime_gas = Op.SELFDESTRUCT(
            Op.CALLDATALOAD(0), address_warm=True, account_new=False
        ).gas_cost(fork)

    pre.fund_address(factory_address, contract_balance)

    # prio fee calc
    genesis_base_fee = 7
    gas_price = 10
    base_fee = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=genesis_base_fee,
        parent_gas_used=0,
        parent_gas_limit=Environment().gas_limit,
    )
    priority_fee_per_gas = gas_price - base_fee

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(factory_code),
        contract_creation=True,
    )
    factory_gas = factory_code.gas_cost(fork)
    initcode_exec_gas = initcode.execution_gas(fork)
    code_deposit_gas = len(runtime_code) * gas_costs.GAS_CODE_DEPOSIT_PER_BYTE
    inner_runtime_gas = Op.SELFDESTRUCT(
        Op.ADDRESS, address_warm=True, account_new=False
    ).gas_cost(fork)

    gas_used = (
        intrinsic_gas
        + factory_gas
        + initcode_exec_gas
        + code_deposit_gas
        + inner_runtime_gas
        + payer_runtime_gas
    )
    priority_fee = priority_fee_per_gas * gas_used

    # Finalization burn log proves coinbase received priority fee before log
    finalization_balance = funding_amount + priority_fee

    expected_logs = [
        transfer_log(factory_address, created_address, contract_balance),
        burn_log(created_address, contract_balance),
    ]

    # if funded after selfdestruct, expect transfer log from payer
    if funded_after_selfdestruct:
        assert payer is not None
        expected_logs.append(
            transfer_log(payer, created_address, funding_amount)
        )

    # finalization burn log
    expected_logs.append(burn_log(created_address, finalization_balance))

    tx = Transaction(
        sender=sender,
        to=None,
        value=0,
        data=factory_code,
        gas_limit=500_000,
        gas_price=gas_price,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    post: dict[Address, Account | None] = {
        created_address: Account.NONEXISTENT,
    }
    if payer is not None:
        post[payer] = Account(balance=0)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                fee_recipient=coinbase,
                header_verify=Header(base_fee_per_gas=base_fee),
            )
        ],
        post=post,
        genesis_environment=Environment(base_fee_per_gas=genesis_base_fee),
    )
