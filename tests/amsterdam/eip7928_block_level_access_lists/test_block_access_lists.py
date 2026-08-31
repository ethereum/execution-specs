"""Tests for EIP-7928 using the consistent data class pattern."""

from typing import Callable

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountAbsentValues,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Conditional,
    EIPChecklist,
    Environment,
    Fork,
    Hash,
    Header,
    Initcode,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
    Withdrawal,
    add_kzg_version,
    compute_create_address,
)
from execution_testing import Macros as Om

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")
SYSTEM_ADDRESS = Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)


@EIPChecklist.BlockHeaderField.Test.ValueBehavior.Accept()
@EIPChecklist.BlockHeaderField.Test.Genesis()
def test_bal_nonce_changes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL captures changes to nonce."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=100,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=100),
        },
    )


def test_bal_balance_changes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Ensure BAL captures changes to balance."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_calculator(
        calldata=b"",
        contract_creation=False,
        access_list=[],
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    total_gas_cost = intrinsic_gas_cost + top_frame_state_gas
    # Hard-coded gas price allows to calculate the tx final price
    gas_price = 1_000_000_000
    tx_value = 100

    tx = Transaction(
        sender=alice,
        to=bob,
        value=tx_value,
        gas_price=gas_price,
    )

    alice_account = pre[alice]
    assert alice_account is not None, "Alice account should exist"
    alice_initial_balance = alice_account.balance

    # Account for both the value sent and gas cost (gas_price * gas_used)
    alice_final_balance = (
        alice_initial_balance - tx_value - (total_gas_cost * gas_price)
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=alice_final_balance,
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=100
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1, balance=alice_final_balance),
            bob: Account(balance=100),
        },
    )


def test_bal_code_changes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL captures changes to account code."""
    runtime_code = Op.STOP
    runtime_code_bytes = bytes(runtime_code)

    init_code = (
        Op.PUSH1(len(runtime_code_bytes))  # size = 1
        + Op.DUP1  # duplicate size for return
        + Op.PUSH1(0x0C)  # offset in init code where runtime code starts
        + Op.PUSH1(0x00)  # dest offset
        + Op.CODECOPY  # copy runtime code to memory
        + Op.PUSH1(0x00)  # memory offset for return
        + Op.RETURN  # return runtime code
        + runtime_code  # the actual runtime code to deploy
    )
    init_code_bytes = bytes(init_code)

    # Factory contract that uses CREATE to deploy
    factory_code = (
        # Push init code to memory
        Op.PUSH32(init_code_bytes)
        + Op.PUSH1(0x00)
        + Op.MSTORE  # Store at memory position 0
        # CREATE parameters: value, offset, size
        + Op.PUSH1(len(init_code_bytes))  # size of init code
        + Op.PUSH1(
            32 - len(init_code_bytes)
        )  # offset in memory (account for padding)
        + Op.PUSH1(0x00)  # value = 0 (no ETH sent)
        + Op.CREATE  # Deploy the contract
        + Op.STOP
    )

    factory_contract = pre.deploy_contract(code=factory_code)
    alice = pre.fund_eoa()

    tx = Transaction(
        sender=alice,
        to=factory_contract,
    )

    created_contract = compute_create_address(
        address=factory_contract, nonce=1
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                factory_contract: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                ),
                created_contract: BalAccountExpectation(
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=runtime_code_bytes
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            factory_contract: Account(nonce=2),  # incremented by CREATE to 2
            created_contract: Account(
                code=runtime_code_bytes,
                storage={},
            ),
        },
    )


@pytest.mark.parametrize(
    "account_access_opcode",
    [
        pytest.param(
            lambda target_addr: Op.BALANCE(target_addr), id="balance"
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODESIZE(target_addr), id="extcodesize"
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODECOPY(target_addr, 0, 0, 32),
            id="extcodecopy",
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODEHASH(target_addr), id="extcodehash"
        ),
        pytest.param(
            lambda target_addr: Op.CALL(0, target_addr, 0, 0, 0, 0, 0),
            id="call",
        ),
        pytest.param(
            lambda target_addr: Op.CALLCODE(0, target_addr, 0, 0, 0, 0, 0),
            id="callcode",
        ),
        pytest.param(
            lambda target_addr: Op.DELEGATECALL(0, target_addr, 0, 0, 0, 0),
            id="delegatecall",
        ),
        pytest.param(
            lambda target_addr: Op.STATICCALL(0, target_addr, 0, 0, 0, 0),
            id="staticcall",
        ),
    ],
)
def test_bal_account_access_target(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    account_access_opcode: Callable[[Address], Op],
) -> None:
    """Ensure BAL captures target address of account access opcodes."""
    alice = pre.fund_eoa()
    target_contract = pre.deploy_contract(code=Op.STOP)

    oracle_contract = pre.deploy_contract(
        balance=100,
        code=account_access_opcode(target_contract),
    )

    tx = Transaction(sender=alice, to=oracle_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ]
                ),
                target_contract: BalAccountExpectation.empty(),
                oracle_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_callcode_nested_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures balance changes from nested value transfers
    when CALLCODE executes target code that itself makes CALL with value.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    # TargetContract sends 100 wei to bob
    target_code = Op.CALL(0, bob, 100, 0, 0, 0, 0)
    target_contract = pre.deploy_contract(code=target_code)

    # Oracle contract that uses CALLCODE to execute TargetContract's code
    oracle_code = Op.CALLCODE(address=target_contract, value=100)
    oracle_contract = pre.deploy_contract(code=oracle_code, balance=200)

    tx = Transaction(sender=alice, to=oracle_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle_contract: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=100
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=100
                        )
                    ],
                ),
                target_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


@pytest.mark.parametrize(
    "delegated_opcode",
    [
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
        pytest.param(Op.CALLCODE, id="callcode"),
    ],
)
def test_bal_delegated_storage_writes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    delegated_opcode: Op,
) -> None:
    """
    Ensure BAL captures delegated storage writes via
    DELEGATECALL and CALLCODE.
    """
    alice = pre.fund_eoa()

    # TargetContract that writes 0x42 to slot 0x01
    target_code = Op.SSTORE(0x01, 0x42)
    target_contract = pre.deploy_contract(code=target_code)

    # Oracle contract that uses delegated opcode to execute
    # TargetContract's code
    oracle_code = delegated_opcode(address=target_contract)
    oracle_contract = pre.deploy_contract(code=oracle_code)

    tx = Transaction(sender=alice, to=oracle_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle_contract: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        )
                    ],
                ),
                target_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


@pytest.mark.parametrize(
    "delegated_opcode",
    [
        pytest.param(
            lambda target_addr: Op.DELEGATECALL(
                50000, target_addr, 0, 0, 0, 0
            ),
            id="delegatecall",
        ),
        pytest.param(
            lambda target_addr: Op.CALLCODE(50000, target_addr, 0, 0, 0, 0, 0),
            id="callcode",
        ),
    ],
)
def test_bal_delegated_storage_reads(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    delegated_opcode: Callable[[Address], Op],
) -> None:
    """
    Ensure BAL captures delegated storage reads via
    DELEGATECALL and CALLCODE.
    """
    alice = pre.fund_eoa()

    # TargetContract that reads from slot 0x01
    target_code = Op.SLOAD(0x01) + Op.STOP
    target_contract = pre.deploy_contract(code=target_code)

    # Oracle contract with storage slot 0x01 = 0x42,
    # uses delegated opcode to execute TargetContract's code
    oracle_code = delegated_opcode(target_contract)
    oracle_contract = pre.deploy_contract(
        code=oracle_code, storage={0x01: 0x42}
    )

    tx = Transaction(
        sender=alice,
        to=oracle_contract,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle_contract: BalAccountExpectation(
                    storage_reads=[0x01],
                ),
                target_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_block_rewards(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Ensure BAL captures fee recipient balance changes from block rewards."""
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)  # fee recipient

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator(
        calldata=b"",
        contract_creation=False,
        access_list=[],
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    expected_gas_used = intrinsic_gas + top_frame_state_gas
    tx_gas_limit = expected_gas_used + 1000  # add a small buffer
    gas_price = 0xA
    tx_value = 100
    extra_balance = 1000

    alice_initial_balance = (
        (tx_gas_limit * gas_price) + tx_value + extra_balance
    )
    alice = pre.fund_eoa(amount=alice_initial_balance)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=tx_value,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    # EIP-1559 fee calculation:
    # - Total gas cost
    total_gas_cost = expected_gas_used * gas_price
    # - Tip portion

    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )
    tip_to_charlie = (gas_price - base_fee_per_gas) * expected_gas_used

    alice_final_balance = alice_initial_balance - tx_value - total_gas_cost

    block = Block(
        txs=[tx],
        fee_recipient=charlie,  # Set Charlie as the fee recipient
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=alice_final_balance,
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=100
                        )
                    ],
                ),
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=tip_to_charlie
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={},
        genesis_environment=genesis_env,
    )


@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
def test_bal_selfdestruct_to_coinbase(
    pre: Alloc,
    state_test: StateTestFiller,
    same_tx: bool,
) -> None:
    """
    Ensure BAL records SELFDESTRUCT when the beneficiary is the coinbase.

    Post-Cancun (EIP-6780) the contract is only actually destroyed when
    created in the same tx; the pre-deployed path only transfers balance
    and preserves the contract. Both shapes must appear in BAL.
    """
    alice = pre.fund_eoa()
    coinbase = pre.fund_eoa(amount=0)
    victim_balance = 100
    victim_code = Op.SELFDESTRUCT(Op.COINBASE)

    # Match gas_price to base_fee so the priority-fee tip is zero;
    # coinbase's BAL entry then carries only the SELFDESTRUCT transfer.
    base_fee_per_gas = 7
    env = Environment(
        base_fee_per_gas=base_fee_per_gas, fee_recipient=coinbase
    )

    account_expectations: dict[Address, BalAccountExpectation]

    if same_tx:
        initcode = Initcode(deploy_code=victim_code)
        factory_code = Om.MSTORE(initcode, 0) + Op.CALL(
            gas=Op.GAS,
            address=Op.CREATE(
                value=victim_balance, offset=0, size=len(initcode)
            ),
        )
        factory = pre.deploy_contract(
            code=factory_code, balance=victim_balance
        )
        victim = compute_create_address(address=factory, nonce=1)
        tx_target = factory
        post = {
            factory: Account(balance=0),
            victim: Account.NONEXISTENT,
            coinbase: Account(balance=victim_balance),
        }
        account_expectations = {
            factory: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=2)
                ],
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=0)
                ],
            ),
            # Created and destroyed in the same tx — empty changes.
            victim: BalAccountExpectation.empty(),
            coinbase: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=victim_balance
                    )
                ],
            ),
        }
    else:
        victim = pre.deploy_contract(code=victim_code, balance=victim_balance)
        tx_target = victim
        # Pre-deployed and not same-tx: post-Cancun preserves the contract.
        post = {
            victim: Account(balance=0, code=victim_code),
            coinbase: Account(balance=victim_balance),
        }
        account_expectations = {
            victim: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=0)
                ],
            ),
            coinbase: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=victim_balance
                    )
                ],
            ),
        }

    tx = Transaction(
        sender=alice,
        to=tx_target,
        gas_price=base_fee_per_gas,
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            base_fee_per_gas=base_fee_per_gas
        ),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations,
        ),
    )


def test_bal_2930_account_listed_but_untouched(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL excludes untouched access list accounts."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    oracle = pre.deploy_contract(code=Op.STOP)

    access_list = AccessList(
        address=oracle,
        storage_keys=[Hash(0x1)],
    )

    tx = Transaction(
        ty=1,
        sender=alice,
        to=bob,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # The address excluded from BAL since state is not accessed
                oracle: None,
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
        },
    )


def test_bal_2930_slot_listed_but_untouched(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL excludes untouched access list storage slots."""
    alice = pre.fund_eoa()
    pure_calculator = pre.deploy_contract(
        # Pure add operation
        Op.ADD(35, 7)
    )

    access_list = AccessList(
        address=pure_calculator,
        storage_keys=[Hash(0x1)],
    )

    tx = Transaction(
        ty=1,
        sender=alice,
        to=pure_calculator,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # The account was loaded.
                pure_calculator: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
        },
    )


def test_bal_2930_slot_listed_and_unlisted_writes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL includes storage writes regardless of access list presence.
    """
    alice = pre.fund_eoa()
    storage_writer = pre.deploy_contract(
        code=Op.SSTORE(0x01, 0x42) + Op.SSTORE(0x02, 0x43)
    )

    # Access list only includes slot 0x01, but contract writes to both
    # 0x01 and 0x02
    access_list = AccessList(
        address=storage_writer,
        storage_keys=[Hash(0x01)],
    )

    tx = Transaction(
        ty=1,
        sender=alice,
        to=storage_writer,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                storage_writer: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x43
                                )
                            ],
                        ),
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            storage_writer: Account(storage={0x01: 0x42, 0x02: 0x43}),
        },
    )


def test_bal_2930_slot_listed_and_unlisted_reads(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL includes storage reads regardless of access list presence."""
    alice = pre.fund_eoa()
    storage_reader = pre.deploy_contract(
        code=Op.SLOAD(0x01) + Op.SLOAD(0x02),
        storage={0x01: 0x42, 0x02: 0x43},  # Pre-populate storage with values
    )

    # Access list only includes slot 0x01, but contract reads from both
    # 0x01 and 0x02
    access_list = AccessList(
        address=storage_reader,
        storage_keys=[Hash(0x01)],
    )

    tx = Transaction(
        ty=1,
        sender=alice,
        to=storage_reader,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                storage_reader: BalAccountExpectation(
                    storage_reads=[0x01, 0x02],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            storage_reader: Account(storage={0x01: 0x42, 0x02: 0x43}),
        },
    )


def test_bal_self_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test that BAL correctly handles self-transfers."""
    start_balance = 1_000_000
    alice = pre.fund_eoa(amount=start_balance)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_calculator(
        recipient_type=RecipientType.SELF
    )

    tx = Transaction(
        sender=alice,
        to=alice,
        gas_limit=intrinsic_gas_cost,
        value=100,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=start_balance
                            - intrinsic_gas_cost * int(tx.gas_price or 0),
                        )
                    ],
                )
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_zero_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test that BAL correctly handles zero-value transfers."""
    start_balance = 1_000_000
    alice = pre.fund_eoa(amount=start_balance)
    bob = pre.fund_eoa(amount=100)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_calculator(
        recipient_type=RecipientType.EOA
    )

    tx = Transaction(
        sender=alice,
        to=bob,
        gas_limit=intrinsic_gas_cost,
        value=0,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=start_balance
                            - intrinsic_gas_cost * int(tx.gas_price or 0),
                        )
                    ],
                ),
                # Include the address; omit from balance_changes.
                bob: BalAccountExpectation(balance_changes=[]),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


@pytest.mark.parametrize(
    "initial_balance,transfer_amount,transfer_mechanism",
    [
        pytest.param(0, 0, "call", id="zero_balance_zero_transfer_call"),
        pytest.param(
            0, 0, "selfdestruct", id="zero_balance_zero_transfer_selfdestruct"
        ),
        pytest.param(1, 1, "call", id="nonzero_balance_net_zero"),
        pytest.param(100, 50, "call", id="larger_balance_net_zero"),
    ],
)
def test_bal_net_zero_balance_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    initial_balance: int,
    transfer_amount: int,
    transfer_mechanism: str,
) -> None:
    """
    Test that BAL does not record balance changes when net change is zero.

    A contract starts with `initial_balance`, receives `transfer_amount`
    (increasing its balance), then sends `transfer_amount` to a recipient
    (decreasing its balance back to `initial_balance`). The net change is zero,
    so BAL should not record any balance changes for this contract.

    The contract verifies this by reading its own balance with SELFBALANCE,
    storing it in slot 0, then sending that amount to the recipient.
    """
    alice = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)

    net_zero_bal_contract_code = (
        Op.SSTORE(0, Op.SELFBALANCE) + Op.SELFDESTRUCT(recipient)
        if transfer_mechanism == "selfdestruct"
        # store current balance in slot 0
        else (
            Op.SSTORE(0, Op.SELFBALANCE)
            # send only the `transfer_amount` received to recipient (net zero)
            + Op.CALL(0, recipient, Op.CALLVALUE, 0, 0, 0, 0)
            + Op.STOP
        )
    )
    net_zero_bal_contract = pre.deploy_contract(
        code=net_zero_bal_contract_code, balance=initial_balance
    )

    tx = Transaction(
        sender=alice, to=net_zero_bal_contract, value=transfer_amount
    )

    expected_balance_in_slot = initial_balance + transfer_amount

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                net_zero_bal_contract: BalAccountExpectation(
                    # receives transfer_amount and sends transfer_amount away
                    # (net-zero change)
                    balance_changes=[],
                    storage_reads=[0x00]
                    if expected_balance_in_slot == 0
                    else [],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1,
                                    post_value=expected_balance_in_slot,
                                )
                            ],
                        )
                    ]
                    if expected_balance_in_slot > 0
                    else [],
                ),
                # recipient receives transfer_amount
                recipient: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=transfer_amount
                        )
                    ]
                    if transfer_amount > 0
                    else [],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            net_zero_bal_contract: Account(
                balance=initial_balance,
                storage={0x00: expected_balance_in_slot}
                if expected_balance_in_slot > 0
                else {},
            ),
            recipient: Account(balance=transfer_amount)
            if transfer_amount > 0
            else Account.NONEXISTENT,
        },
    )


def test_bal_pure_contract_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Test that BAL captures contract access for pure computation calls."""
    alice = pre.fund_eoa()
    pure_contract = pre.deploy_contract(code=Op.ADD(0x3, 0x2))

    tx = Transaction(sender=alice, to=pure_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # Ensure called contract is tracked
                pure_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_noop_storage_write(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Test that BAL correctly handles no-op storage write."""
    alice = pre.fund_eoa()
    code = Op.SSTORE(
        0x01, 0x42, key_warm=False, original_value=0, new_value=0x42
    )
    storage_contract = pre.deploy_contract(code=code, storage={0x01: 0x42})

    tx = Transaction(sender=alice, to=storage_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                storage_contract: BalAccountExpectation(
                    storage_reads=[0x01],
                    storage_changes=[],
                ),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


@pytest.mark.parametrize(
    "abort_opcode",
    [
        pytest.param(Op.REVERT(0, 0), id="revert"),
        pytest.param(Op.INVALID, id="invalid"),
    ],
)
def test_bal_aborted_storage_access(
    pre: Alloc, blockchain_test: BlockchainTestFiller, abort_opcode: Op
) -> None:
    """Ensure BAL captures storage access in aborted transactions correctly."""
    alice = pre.fund_eoa()
    storage_contract = pre.deploy_contract(
        code=Op.SLOAD(0x01) + Op.SSTORE(0x02, 0x42) + abort_opcode,
        storage={0x01: 0x10},  # Pre-existing value in slot 0x01
    )

    tx = Transaction(sender=alice, to=storage_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ]
                ),
                storage_contract: BalAccountExpectation(
                    storage_changes=[],
                    storage_reads=[0x01, 0x02],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={},
    )


@pytest.mark.parametrize(
    "account_access_opcode",
    [
        pytest.param(
            lambda target_addr: Op.BALANCE(target_addr), id="balance"
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODESIZE(target_addr), id="extcodesize"
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODECOPY(target_addr, 0, 0, 32),
            id="extcodecopy",
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODEHASH(target_addr), id="extcodehash"
        ),
        pytest.param(
            lambda target_addr: Op.CALL(0, target_addr, 50, 0, 0, 0, 0),
            id="call",
        ),
        pytest.param(
            lambda target_addr: Op.CALLCODE(0, target_addr, 50, 0, 0, 0, 0),
            id="callcode",
        ),
        pytest.param(
            lambda target_addr: Op.DELEGATECALL(0, target_addr, 0, 0, 0, 0),
            id="delegatecall",
        ),
        pytest.param(
            lambda target_addr: Op.STATICCALL(0, target_addr, 0, 0, 0, 0),
            id="staticcall",
        ),
    ],
)
@pytest.mark.parametrize(
    "abort_opcode",
    [
        pytest.param(Op.REVERT(0, 0), id="revert"),
        pytest.param(Op.INVALID, id="invalid"),
    ],
)
def test_bal_aborted_account_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    account_access_opcode: Callable[[Address], Op],
    abort_opcode: Op,
) -> None:
    """Ensure BAL captures account access in aborted transactions."""
    alice = pre.fund_eoa()
    target_contract = pre.deploy_contract(code=Op.STOP)

    abort_contract = pre.deploy_contract(
        balance=100,
        code=account_access_opcode(target_contract) + abort_opcode,
    )

    tx = Transaction(sender=alice, to=abort_contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ]
                ),
                target_contract: BalAccountExpectation.empty(),
                abort_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={},
    )


@pytest.mark.parametrize(
    "inner_action",
    ["sstore", "sload", "balance", "extcodesize"],
)
@pytest.mark.parametrize(
    "outer_abort",
    [
        pytest.param(Op.REVERT(0, 0), id="outer_revert"),
        pytest.param(Op.INVALID, id="outer_invalid"),
    ],
)
def test_bal_parent_revert_state_access(
    pre: Alloc,
    state_test: StateTestFiller,
    inner_action: str,
    outer_abort: Op,
) -> None:
    """Ensure BAL captures child-frame state access when the parent reverts."""
    alice = pre.fund_eoa()
    extra_target = pre.deploy_contract(code=Op.STOP)

    if inner_action == "sstore":
        # Write demoted to read by parent revert; pre-set 0xDEAD so the
        # post-state confirms the slot was unchanged.
        inner = pre.deploy_contract(
            code=Op.SSTORE(1, 0x42) + Op.STOP,
            storage={1: 0xDEAD},
        )
    elif inner_action == "sload":
        inner = pre.deploy_contract(
            code=Op.POP(Op.SLOAD(1)) + Op.STOP,
            storage={1: 0xDEAD},
        )
    elif inner_action == "balance":
        inner = pre.deploy_contract(
            code=Op.POP(Op.BALANCE(extra_target)) + Op.STOP
        )
    elif inner_action == "extcodesize":
        inner = pre.deploy_contract(
            code=Op.POP(Op.EXTCODESIZE(extra_target)) + Op.STOP
        )
    else:
        raise ValueError(f"unknown inner_action: {inner_action}")
    outer = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=inner) + outer_abort
    )

    tx = Transaction(sender=alice, to=outer)

    account_expectations: dict[Address, BalAccountExpectation]
    if inner_action in ("sstore", "sload"):
        account_expectations = {
            inner: BalAccountExpectation(storage_reads=[1]),
        }
    elif inner_action in ("balance", "extcodesize"):
        account_expectations = {
            inner: BalAccountExpectation.empty(),
            extra_target: BalAccountExpectation.empty(),
        }
    else:
        raise ValueError(f"unknown inner_action: {inner_action}")

    post: dict = {alice: Account(nonce=1)}
    if inner_action in ("sstore", "sload"):
        # Slot 1 stays at its pre-state value: SSTORE demoted to read,
        # SLOAD never mutates.
        post[inner] = Account(storage={1: 0xDEAD})

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations,
        ),
    )


@pytest.mark.parametrize(
    "inner_op",
    [pytest.param("call", id="call"), pytest.param("create", id="create")],
)
def test_bal_outer_revert_with_inner_insufficient_funds(
    pre: Alloc,
    state_test: StateTestFiller,
    inner_op: str,
) -> None:
    """
    Outer REVERT + inner CALL/CREATE that fails on insufficient funds.

    Inner writes two slots and then attempts a value-bearing CALL or
    CREATE that fails (balance=0 < value). The opcode's state-touching
    costs are charged before the balance check, so the failed CALL's
    target stays in BAL with empty changes, while CREATE fails before
    `track_address` and the would-be address does not appear at all.
    Inner's writes demote to reads under outer's REVERT; the post-state
    checks confirm none of the rolled-back state leaked through.
    """
    alice = pre.fund_eoa()
    slot_a, slot_b = 1, 2
    insufficient_value = 100

    if inner_op == "call":
        target = pre.deploy_contract(code=Op.STOP)
        inner = pre.deploy_contract(
            code=(
                Op.SSTORE(slot_a, 0x42)
                + Op.SSTORE(
                    slot_b,
                    Op.CALL(
                        gas=100_000,
                        address=target,
                        value=insufficient_value,
                    ),
                )
                + Op.STOP
            ),
            balance=0,
        )
        extra_account = target
        extra_bal: BalAccountExpectation | None = BalAccountExpectation.empty()
        extra_post: Account | None = Account(balance=0)
    elif inner_op == "create":
        initcode_bytes = bytes(Initcode(deploy_code=Op.STOP))
        inner = pre.deploy_contract(
            code=(
                Op.MSTORE(0, Op.PUSH32(initcode_bytes))
                + Op.SSTORE(slot_a, 0x42)
                + Op.SSTORE(
                    slot_b,
                    Op.CREATE(
                        value=insufficient_value,
                        offset=32 - len(initcode_bytes),
                        size=len(initcode_bytes),
                    ),
                )
                + Op.STOP
            ),
            balance=0,
        )
        extra_account = compute_create_address(address=inner, nonce=1)
        extra_bal = None
        extra_post = Account.NONEXISTENT
    else:
        raise ValueError(f"unknown inner_op: {inner_op}")

    outer = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=inner) + Op.REVERT(0, 0)
    )

    tx = Transaction(sender=alice, to=outer)

    state_test(
        pre=pre,
        post={
            alice: Account(nonce=1),
            outer: Account(balance=0, storage={}),
            inner: Account(balance=0, storage={}),
            extra_account: extra_post,
        },
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                outer: BalAccountExpectation.empty(),
                inner: BalAccountExpectation(storage_reads=[slot_a, slot_b]),
                extra_account: extra_bal,
            },
        ),
    )


def test_bal_fully_unmutated_account(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test that BAL captures account that has zero net mutations.

    oracle account:
        1. Storage read and write the same value (no net change).
        2. Receives `0` value transfer (no net change).
    """
    alice = pre.fund_eoa()
    # Deploy Oracle contract with pre-existing storage value
    oracle = pre.deploy_contract(
        code=Op.SSTORE(0x01, 0x42) + Op.STOP,
        storage={0x01: 0x42},  # Pre-existing value
    )

    tx = Transaction(sender=alice, to=oracle, value=0, gas_price=0xA)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation(
                    storage_changes=[],  # No net storage changes
                    storage_reads=[0x01],  # But storage was accessed
                    balance_changes=[],  # No net balance changes
                ),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_empty_block_no_coinbase(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL correctly handles empty blocks without including coinbase.

    When a block has no transactions and no withdrawals, the coinbase/fee
    recipient receives no fees and should not be included in the BAL.
    """
    coinbase = pre.fund_eoa(amount=0)

    block = Block(
        txs=[],
        withdrawals=None,
        fee_recipient=coinbase,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # Coinbase must NOT be included - receives no fees
                coinbase: None,
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_coinbase_zero_tip(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Ensure BAL includes coinbase even when priority fee is zero."""
    bob = pre.fund_eoa(amount=0)
    coinbase = pre.fund_eoa(amount=0)  # fee recipient

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator(
        calldata=b"",
        contract_creation=False,
        access_list=[],
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    tx_gas_limit = intrinsic_gas + top_frame_state_gas + 1000

    # Calculate base fee
    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )

    # Set gas_price equal to base_fee so tip = 0
    tx_value = 5
    alice_initial_balance = (tx_gas_limit * base_fee_per_gas) + tx_value
    alice = pre.fund_eoa(amount=alice_initial_balance)
    tx = Transaction(
        sender=alice,
        to=bob,
        value=tx_value,
        gas_limit=tx_gas_limit,
        gas_price=base_fee_per_gas,
    )

    alice_final_balance = (
        alice_initial_balance
        - tx_value
        - ((intrinsic_gas + top_frame_state_gas) * base_fee_per_gas)
    )

    block = Block(
        txs=[tx],
        fee_recipient=coinbase,
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=alice_final_balance,
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=5)
                    ]
                ),
                # Coinbase must be included even with zero tip
                coinbase: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1, balance=alice_final_balance),
            bob: Account(balance=5),
        },
        genesis_environment=genesis_env,
    )


def test_bal_system_address_coinbase_zero_tip(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure BAL includes SYSTEM_ADDRESS when it is the zero-tip fee recipient.
    """
    bob = pre.fund_eoa(amount=0)

    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )

    tx_value = 5
    alice = pre.fund_eoa()
    tx = Transaction(
        sender=alice,
        to=bob,
        value=tx_value,
        gas_price=base_fee_per_gas,
    )

    block = Block(
        txs=[tx],
        fee_recipient=SYSTEM_ADDRESS,
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=5)
                    ]
                ),
                SYSTEM_ADDRESS: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=5),
            SYSTEM_ADDRESS: Account.NONEXISTENT,
        },
        genesis_environment=genesis_env,
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(10**18, id="with_value"),
        pytest.param(0, id="no_value"),
    ],
)
@pytest.mark.with_all_precompiles
def test_bal_precompile_funded(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
    value: int,
) -> None:
    """
    Ensure BAL records precompile value transfer.

    Alice sends value to precompile (pure value transfer).
    If value > 0: BAL must include balance_changes.
    If value = 0: BAL must have empty balance_changes.
    """
    alice = pre.fund_eoa()

    addr_int = int.from_bytes(precompile, "big")

    # Map precompile addresses to their required minimal input sizes
    # - Most precompiles accept zero-padded input of appropriate length
    # - For 0x0a (POINT_EVALUATION), use a known valid input from mainnet
    if addr_int == 0x0A:
        # Valid point evaluation input from mainnet tx:
        # https://etherscan.io/tx/0xcb3dc8f3b14f1cda0c16a619a112102a8ec70dce1b3f1b28272227cf8d5fbb0e
        tx_data = (
            bytes.fromhex(
                # versioned_hash (32)
                "018156B94FE9735E573BAB36DAD05D60FEB720D424CCD20AAF719343C31E4246"
            )
            + bytes.fromhex(
                # z (32)
                "019123BCB9D06356701F7BE08B4494625B87A7B02EDC566126FB81F6306E915F"
            )
            + bytes.fromhex(
                # y (32)
                "6C2EB1E94C2532935B8465351BA1BD88EABE2B3FA1AADFF7D1CD816E8315BD38"
            )
            + bytes.fromhex(
                # kzg_commitment (48)
                "A9546D41993E10DF2A7429B8490394EA9EE62807BAE6F326D1044A51581306F58D4B9DFD5931E044688855280FF3799E"
            )
            + bytes.fromhex(
                # kzg_proof (48)
                "A2EA83D9391E0EE42E0C650ACC7A1F842A7D385189485DDB4FD54ADE3D9FD50D608167DCA6C776AAD4B8AD5C20691BFE"
            )
        )
    else:
        precompile_min_input = {
            0x01: 128,  # ECRECOVER
            0x02: 0,  # SHA256 (accepts empty)
            0x03: 0,  # RIPEMD160 (accepts empty)
            0x04: 0,  # IDENTITY (accepts empty)
            0x05: 96,  # MODEXP
            0x06: 128,  # BN256ADD
            0x07: 96,  # BN256MUL
            0x08: 0,  # BN256PAIRING (empty is valid)
            0x09: 213,  # BLAKE2F
            0x0B: 256,  # BLS12_G1_ADD
            0x0C: 160,  # BLS12_G1_MSM
            0x0D: 512,  # BLS12_G2_ADD
            0x0E: 288,  # BLS12_G2_MSM
            0x0F: 384,  # BLS12_PAIRING
            0x10: 64,  # BLS12_MAP_FP_TO_G1
            0x11: 128,  # BLS12_MAP_FP2_TO_G2
            0x100: 160,  # P256VERIFY
        }

        input_size = precompile_min_input.get(addr_int, 0)
        tx_data = bytes([0x00] * input_size if input_size > 0 else [])

    tx = Transaction(
        sender=alice,
        to=precompile,
        value=value,
        data=tx_data,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                precompile: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=value
                        )
                    ]
                    if value > 0
                    else [],
                    storage_reads=[],
                    storage_changes=[],
                    code_changes=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.with_all_call_opcodes
def test_bal_precompile_call_opcode(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: int,
    call_opcode: Op,
) -> None:
    """
    Ensure BAL records the precompile address regardless of call opcode.

    Alice calls Oracle contract which invokes the precompile via the
    parametrized call opcode. For DELEGATECALL/CALLCODE the precompile
    provides the code but is not the call target, so its access has to
    be recorded explicitly rather than incidentally.
    """
    alice = pre.fund_eoa()

    oracle = pre.deploy_contract(
        code=call_opcode(address=precompile) + Op.STOP
    )

    tx = Transaction(sender=alice, to=oracle)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation.empty(),
                precompile: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="positive_value"),
    ],
)
def test_bal_nonexistent_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    value: int,
) -> None:
    """
    Ensure BAL captures non-existent account on value transfer.

    Alice sends value directly to non-existent Bob.
    """
    alice = pre.fund_eoa()
    bob = pre.nonexistent_account()

    tx = Transaction(sender=alice, to=bob, value=value)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=value
                        )
                    ]
                    if value > 0
                    else [],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=value) if value > 0 else Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "account_access_opcode",
    [
        pytest.param(
            lambda target_addr: Op.BALANCE(target_addr),
            id="balance",
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODESIZE(target_addr),
            id="extcodesize",
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODECOPY(target_addr, 0, 0, 32),
            id="extcodecopy",
        ),
        pytest.param(
            lambda target_addr: Op.EXTCODEHASH(target_addr),
            id="extcodehash",
        ),
        pytest.param(
            lambda target_addr: Op.STATICCALL(0, target_addr, 0, 0, 0, 0),
            id="staticcall",
        ),
        pytest.param(
            lambda target_addr: Op.DELEGATECALL(0, target_addr, 0, 0, 0, 0),
            id="delegatecall",
        ),
    ],
)
def test_bal_nonexistent_account_access_read_only(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    account_access_opcode: Callable[[Address], Op],
) -> None:
    """
    Ensure BAL captures non-existent account access via read-only opcodes.

    Alice calls Oracle contract which uses read-only opcodes to access
    non-existent Bob (BALANCE, EXTCODESIZE, EXTCODECOPY, EXTCODEHASH,
    STATICCALL, DELEGATECALL).
    """
    alice = pre.fund_eoa()
    bob = pre.nonexistent_account()
    oracle_balance = 2 * 10**18

    oracle_code = account_access_opcode(bob)
    oracle = pre.deploy_contract(code=oracle_code, balance=oracle_balance)

    tx = Transaction(sender=alice, to=oracle)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation.empty(),
                bob: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            oracle: Account(balance=oracle_balance),
            bob: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL),
        pytest.param(Op.CALLCODE),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(10**18, id="positive_value"),
    ],
)
def test_bal_nonexistent_account_access_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    opcode: Op,
    value: int,
) -> None:
    """
    Ensure BAL captures non-existent account access via CALL/CALLCODE
    with value.

    Alice calls Oracle contract which uses CALL or CALLCODE to access
    non-existent Bob with value transfer.
    - CALL: Transfers value from Oracle to Bob
    - CALLCODE: Self-transfer (net zero), Bob accessed for code
    """
    alice = pre.fund_eoa()
    bob = pre.nonexistent_account()
    oracle_balance = value + 10**18

    oracle_code = opcode(gas=0, address=bob, value=value)

    oracle = pre.deploy_contract(code=oracle_code, balance=oracle_balance)

    tx = Transaction(sender=alice, to=oracle)

    # Calculate expected balances
    if opcode == Op.CALL and value > 0:
        # CALL: Oracle loses value, Bob gains value
        oracle_final_balance = oracle_balance - value
        bob_final_balance = value
        bob_has_balance_change = True
        oracle_has_balance_change = True
    elif opcode == Op.CALLCODE and value > 0:
        # CALLCODE: Self-transfer (net zero), Bob just accessed for code
        oracle_final_balance = oracle_balance
        bob_final_balance = 0
        bob_has_balance_change = False
        oracle_has_balance_change = False
    else:
        # Zero value
        oracle_final_balance = oracle_balance
        bob_final_balance = 0
        bob_has_balance_change = False
        oracle_has_balance_change = False

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=oracle_final_balance,
                        )
                    ]
                    if oracle_has_balance_change
                    else [],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=bob_final_balance,
                        )
                    ]
                    if bob_has_balance_change
                    else [],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            oracle: Account(balance=oracle_final_balance),
            bob: Account(balance=bob_final_balance)
            if bob_has_balance_change
            else Account.NONEXISTENT,
        },
    )


def test_bal_multiple_balance_changes_same_account(
    pre: Alloc,
    fork: Fork,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL correctly tracks multiple balance changes to same account
    across multiple transactions.

    An account that receives funds in TX0 and spends them in TX1 should
    have TWO balance change entries in the BAL, one for each transaction.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    tx_intrinsic_gas = intrinsic_gas_calculator(
        calldata=b"",
        access_list=[],
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )

    # bob receives funds in tx0, then spends everything in tx1
    gas_price = 10
    expected_gas_used = tx_intrinsic_gas + top_frame_state_gas
    tx1_gas_cost = expected_gas_used * gas_price
    spend_amount = 100
    funding_amount = tx1_gas_cost + spend_amount

    tx0 = Transaction(
        sender=alice,
        to=bob,
        value=funding_amount,
        gas_limit=expected_gas_used,
        gas_price=gas_price,
    )

    tx1 = Transaction(
        sender=bob,
        to=charlie,
        value=spend_amount,
        gas_limit=expected_gas_used,
        gas_price=gas_price,
    )

    bob_balance_after_tx0 = funding_amount
    bob_balance_after_tx1 = 0

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx0, tx1],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        bob: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=2, post_nonce=1
                                )
                            ],
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=bob_balance_after_tx0,
                                ),
                                BalBalanceChange(
                                    block_access_index=2,
                                    post_balance=bob_balance_after_tx1,
                                ),
                            ],
                        ),
                        charlie: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=2,
                                    post_balance=spend_amount,
                                )
                            ],
                        ),
                    }
                ),
            )
        ],
        post={
            bob: Account(nonce=1, balance=bob_balance_after_tx1),
            charlie: Account(balance=spend_amount),
        },
    )


def test_bal_multiple_storage_writes_same_slot(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that BAL tracks multiple writes to the same storage slot across
    transactions in the same block.

    Setup:
    - Deploy a contract that increments storage slot 1 on each call
    - Alice calls the contract 3 times in the same block
    - Each call increments slot 1: 0 -> 1 -> 2 -> 3

    Expected BAL:
    - Contract should have 3 storage_changes for slot 1:
      * txIndex 1: postValue = 1
      * txIndex 2: postValue = 2
      * txIndex 3: postValue = 3
    """
    alice = pre.fund_eoa(amount=10**18)

    increment_code = Op.SSTORE(1, Op.ADD(Op.SLOAD(1), 1))
    contract = pre.deploy_contract(code=increment_code)

    tx1 = Transaction(sender=alice, to=contract, gas_limit=200_000)
    tx2 = Transaction(sender=alice, to=contract, gas_limit=200_000)
    tx3 = Transaction(sender=alice, to=contract, gas_limit=200_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2, tx3],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                ),
                                BalNonceChange(
                                    block_access_index=2, post_nonce=2
                                ),
                                BalNonceChange(
                                    block_access_index=3, post_nonce=3
                                ),
                            ],
                        ),
                        contract: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=1,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1, post_value=1
                                        ),
                                        BalStorageChange(
                                            block_access_index=2, post_value=2
                                        ),
                                        BalStorageChange(
                                            block_access_index=3, post_value=3
                                        ),
                                    ],
                                ),
                            ],
                            storage_reads=[],
                            balance_changes=[],
                            code_changes=[],
                        ),
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=3),
            contract: Account(storage={1: 3}),
        },
    )


@pytest.mark.parametrize(
    "intermediate_values",
    [
        pytest.param([2], id="depth_1"),
        pytest.param([2, 3], id="depth_2"),
        pytest.param([2, 3, 4], id="depth_3"),
    ],
)
@pytest.mark.eels_base_coverage
def test_bal_nested_delegatecall_storage_writes_net_zero(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    intermediate_values: list,
) -> None:
    """
    Test BAL correctly handles nested DELEGATECALL frames where intermediate
    frames write different values but the deepest frame reverts to original.

    Each nesting level writes a different intermediate value, and the deepest
    frame writes back the original value, resulting in net-zero change.

    Example for depth=2 (intermediate_values=[2, 3]):
    - Pre-state: slot 0 = 1
    - Root frame writes: slot 0 = 2
    - Child frame writes: slot 0 = 3
    - Grandchild frame writes: slot 0 = 1 (back to original)
    - Expected: No storage_changes (net-zero overall)
    """
    alice = pre.fund_eoa()
    starting_value = 1

    # deepest contract writes back to starting_value
    deepest_code = Op.SSTORE(0, starting_value) + Op.STOP
    next_contract = pre.deploy_contract(code=deepest_code)
    delegate_contracts = [next_contract]

    # Build intermediate contracts (in reverse order) that write then
    # DELEGATECALL. Skip the first value since that's for the root contract
    for value in reversed(intermediate_values[1:]):
        code = (
            Op.SSTORE(0, value)
            + Op.DELEGATECALL(100_000, next_contract, 0, 0, 0, 0)
            + Op.STOP
        )
        next_contract = pre.deploy_contract(code=code)
        delegate_contracts.append(next_contract)

    # root_contract writes first intermediate value, then DELEGATECALLs
    root_contract = pre.deploy_contract(
        code=(
            Op.SSTORE(0, intermediate_values[0])
            + Op.DELEGATECALL(100_000, next_contract, 0, 0, 0, 0)
            + Op.STOP
        ),
        storage={0: starting_value},
    )

    tx = Transaction(
        sender=alice,
        to=root_contract,
        gas_limit=500_000,
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        root_contract: BalAccountExpectation(
            storage_reads=[0],
            storage_changes=[],  # validate no changes
        ),
    }
    # All delegate contracts accessed but no changes
    for contract in delegate_contracts:
        account_expectations[contract] = BalAccountExpectation.empty()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            root_contract: Account(storage={0: starting_value}),
        },
    )


def test_bal_create_transaction_empty_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL does not record spurious code changes when a CREATE transaction
    deploys empty code.
    """
    alice = pre.fund_eoa()
    contract_address = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,
        data=b"",
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        contract_address: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            code_changes=[],  # ensure no code_changes recorded
        ),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            contract_address: Account(nonce=1, code=b""),
        },
    )


@pytest.mark.parametrize(
    "tx2_value",
    [
        pytest.param(0x0, id="tx2_reverts_to_zero"),
        pytest.param(0xABCD, id="tx2_rewrites_same_value"),
    ],
)
def test_bal_cross_tx_storage_write(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    tx2_value: int,
) -> None:
    """
    Tx1's storage_change must be preserved regardless of tx2's write.

    Regression for the blobhash scenario where back-to-pre writes were
    filtered as net-zero across tx boundaries. The same-value case
    additionally exercises the uniqueness rule: a slot in storage_changes
    MUST NOT also appear in storage_reads.
    """
    alice = pre.fund_eoa()
    tx1_value = 0xABCD

    contract = pre.deploy_contract(code=Op.SSTORE(0, Op.CALLDATALOAD(0)))

    tx1 = Transaction(
        sender=alice,
        to=contract,
        data=Hash(tx1_value),
    )

    tx2 = Transaction(
        sender=alice,
        to=contract,
        data=Hash(tx2_value),
    )

    slot_changes = [
        BalStorageChange(block_access_index=1, post_value=tx1_value),
    ]
    if tx2_value != tx1_value:
        slot_changes.append(
            BalStorageChange(block_access_index=2, post_value=tx2_value)
        )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=1, post_nonce=1),
                BalNonceChange(block_access_index=2, post_nonce=2),
            ],
        ),
        contract: BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(slot=0, slot_changes=slot_changes),
            ],
            storage_reads=[],
        ),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            alice: Account(nonce=2),
            contract: Account(storage={0: tx2_value}),
        },
    )


def test_bal_cross_tx_reverted_storage_reads(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Reverted `SSTORE`s from two transactions accumulate in one account's
    `storage_reads`.

    Each transaction succeeds while the frame holding its `SSTORE` reverts,
    so both demoted writes must survive their transaction boundary and the
    block-level list must hold the union of the two slots. Reported in
    https://github.com/erigontech/erigon/issues/23407.
    """
    alice = pre.fund_eoa()
    slots = [0x01, 0x02]  # one per transaction
    pre_value = 0xDEAD

    reverting_writer = pre.deploy_contract(
        code=Op.SSTORE(Op.CALLDATALOAD(0), 0x42) + Op.REVERT(0, 0),
        storage=dict.fromkeys(slots, pre_value),
    )
    # Ignores the failed call so the transaction itself succeeds and only
    # `reverting_writer`'s frame is rolled back.
    caller = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=reverting_writer,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
            )
        )
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(sender=alice, to=caller, data=Hash(slot))
                    for slot in slots
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                ),
                                BalNonceChange(
                                    block_access_index=2, post_nonce=2
                                ),
                            ],
                        ),
                        caller: BalAccountExpectation.empty(),
                        reverting_writer: BalAccountExpectation(
                            storage_changes=[],
                            storage_reads=slots,
                        ),
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=2),
            reverting_writer: Account(storage=dict.fromkeys(slots, pre_value)),
        },
    )


def test_bal_cross_tx_storage_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify clients apply BAL state changes from prior transactions before
    executing later transactions in the same block.

    Each Tx i seeds slots 0 and 1 with `1`, then computes a
    Fibonacci-style sum into slot i: `slot[i] = SLOAD(i-1) + SLOAD(i-2)`.
    Every Tx i>=2 depends on the two immediately preceding writes, so
    any parallelization that fails to apply a prior Tx's BAL storage
    change cascades into a wrong slot value and a different state root.
    """
    chain_length = 8
    # i<2 seeds slot i with 1; i>=2 computes the Fibonacci sum.
    contract = pre.deploy_contract(
        code=Conditional(
            condition=Op.LT(Op.CALLDATALOAD(0), 2),
            if_true=Op.SSTORE(Op.CALLDATALOAD(0), 1),
            if_false=Op.SSTORE(
                Op.CALLDATALOAD(0),
                Op.ADD(
                    Op.SLOAD(Op.SUB(Op.CALLDATALOAD(0), 1)),
                    Op.SLOAD(Op.SUB(Op.CALLDATALOAD(0), 2)),
                ),
            ),
        ),
    )

    fib = [1, 1]
    for i in range(2, chain_length):
        fib.append(fib[i - 1] + fib[i - 2])

    txs = []
    senders = []
    for i in range(chain_length):
        sender = pre.fund_eoa()
        senders.append(sender)
        txs.append(
            Transaction(
                sender=sender,
                to=contract,
                data=Hash(i),
            )
        )

    account_expectations: dict = {
        sender: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=i + 1, post_nonce=1)
            ],
        )
        for i, sender in enumerate(senders)
    }
    account_expectations[contract] = BalAccountExpectation(
        storage_changes=[
            BalStorageSlot(
                slot=i,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=i + 1, post_value=fib[i]
                    ),
                ],
            )
            for i in range(chain_length)
        ],
        nonce_changes=[],
        balance_changes=[],
        code_changes=[],
        storage_reads=[],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            contract: Account(
                storage={i: fib[i] for i in range(chain_length)}
            ),
        },
    )


@pytest.mark.parametrize(
    "num_slots",
    [
        pytest.param(17, id="17_slots"),
        pytest.param(32, id="32_slots"),
        pytest.param(128, id="128_slots"),
    ],
)
def test_bal_many_storage_writes_single_account(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    num_slots: int,
) -> None:
    """
    Verify the BAL records many distinct storage changes for a single
    account written by a single transaction.

    One transaction calls a contract that writes `num_slots` distinct,
    previously-zero slots (`slot[i] = i + 1` for `i` in `0..num_slots`).
    The account's `storage_changes` in the BAL must list every slot, in
    ascending slot order, each at `block_access_index=1`.

    Existing BAL storage tests touch at most a handful of slots per
    account (e.g. `test_bal_cross_tx_storage_chain` writes 8 slots, one
    per transaction). This exercises a much higher per-account,
    per-transaction storage-change cardinality, which stresses any client
    that records or preloads an account's BAL storage keys into a
    fixed-size buffer.
    """
    contract_code = Op.SSTORE(0, 1)
    for i in range(1, num_slots):
        contract_code += Op.SSTORE(i, i + 1)
    contract_code += Op.STOP
    contract = pre.deploy_contract(code=contract_code)

    alice = pre.fund_eoa()
    tx = Transaction(
        sender=alice,
        to=contract,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        contract: BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=i,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1, post_value=i + 1
                        )
                    ],
                )
                for i in range(num_slots)
            ],
            storage_reads=[],
        ),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            contract: Account(storage={i: i + 1 for i in range(num_slots)}),
        },
    )


@pytest.mark.with_all_create_opcodes
def test_bal_cross_tx_deploy_then_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    create_opcode: Op,
) -> None:
    """
    Verify clients apply Tx1's CREATE to their state view before
    executing Tx2's CALL in the same block. Tx1 deploys a contract at a
    deterministic address whose runtime code writes a sentinel to slot 0.
    Tx2 CALLs that address. A client that parallelizes Tx2 without
    applying Tx1's `code_changes` would hit an empty account, the CALL
    would no-op, and slot 0 would remain 0.
    """
    sentinel = 0x42
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    runtime = Op.SSTORE(0, sentinel) + Op.STOP
    initcode = Initcode(deploy_code=runtime)
    initcode_bytes = bytes(initcode)

    salt = 0
    is_create2 = create_opcode == Op.CREATE2
    if is_create2:
        deploy_op = Op.CREATE2(
            value=0, offset=0, size=Op.CALLDATASIZE, salt=salt
        )
    else:
        deploy_op = Op.CREATE(value=0, offset=0, size=Op.CALLDATASIZE)
    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, deploy_op)
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    target = compute_create_address(
        address=factory,
        nonce=1,
        salt=salt,
        initcode=initcode_bytes,
        opcode=create_opcode,
    )

    tx_deploy = Transaction(
        sender=alice,
        to=factory,
        data=initcode_bytes,
    )
    tx_call = Transaction(
        sender=bob,
        to=target,
    )

    account_expectations = {
        target: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            code_changes=[
                BalCodeChange(block_access_index=1, new_code=bytes(runtime))
            ],
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=2, post_value=sentinel
                        ),
                    ],
                ),
            ],
        ),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_deploy, tx_call],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            target: Account(
                nonce=1, code=bytes(runtime), storage={0: sentinel}
            ),
            factory: Account(nonce=2, storage={0: target}),
        },
    )


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("none", id="no_failure"),
        pytest.param("collision", id="mid_chain_collision"),
        pytest.param("oog", id="mid_chain_oog"),
    ],
)
@pytest.mark.pre_alloc_mutable()
def test_bal_cross_tx_factory_nonce_create_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Cross-tx CREATE chain: 8 senders share a factory whose CREATE
    address derives solely from `factory.nonce`. `collision` and `oog`
    test opposite parallelization hazards mid-chain — collision still
    bumps factory.nonce (later txs slide forward), OOG does not (later
    txs slide backward, reusing the OOG'd slot).
    """
    chain_length = 8
    failure_index = 3 if failure_mode in ("collision", "oog") else None

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.CREATE(0, 0, Op.CALLDATASIZE)
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    factory_pre_nonce = 1

    deploy_code = Op.STOP
    initcode = Initcode(deploy_code=deploy_code)
    collision_code = Op.PUSH1(0x42) + Op.STOP

    targets = [
        compute_create_address(address=factory, nonce=factory_pre_nonce + k)
        for k in range(chain_length)
    ]

    if failure_mode == "collision":
        assert failure_index is not None
        pre[targets[failure_index]] = Account(code=collision_code)

    sequence: list[dict] = []
    factory_nonce = factory_pre_nonce
    for i in range(chain_length):
        block_idx = i + 1
        if failure_mode == "oog" and i == failure_index:
            sequence.append(
                {"block_idx": block_idx, "target_idx": None, "deployed": False}
            )
        else:
            target_idx = factory_nonce - factory_pre_nonce
            factory_nonce += 1
            deployed = not (failure_mode == "collision" and i == failure_index)
            sequence.append(
                {
                    "block_idx": block_idx,
                    "factory_post_nonce": factory_nonce,
                    "target_idx": target_idx,
                    "deployed": deployed,
                }
            )

    senders = [pre.fund_eoa() for _ in range(chain_length)]
    # OOG tx: intrinsic + 1 — valid to include but no gas to run CREATE.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(initcode), contract_creation=False, access_list=[]
    )
    txs = [
        Transaction(
            sender=senders[i],
            to=factory,
            data=initcode,
            gas_limit=(
                intrinsic + 1
                if failure_mode == "oog" and i == failure_index
                else fork.transaction_gas_limit_cap()
            ),
        )
        for i in range(chain_length)
    ]

    account_expectations: dict = {
        senders[i]: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=i + 1, post_nonce=1)
            ],
        )
        for i in range(chain_length)
    }
    # Factory: only txs that bumped its nonce contribute entries.
    account_expectations[factory] = BalAccountExpectation(
        nonce_changes=[
            BalNonceChange(
                block_access_index=s["block_idx"],
                post_nonce=s["factory_post_nonce"],
            )
            for s in sequence
            if s["target_idx"] is not None
        ],
    )
    for s in sequence:
        if s["target_idx"] is None:
            continue
        target = targets[s["target_idx"]]
        if s["deployed"]:
            account_expectations[target] = BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(
                        block_access_index=s["block_idx"], post_nonce=1
                    )
                ],
                code_changes=[
                    BalCodeChange(
                        block_access_index=s["block_idx"],
                        new_code=deploy_code,
                    )
                ],
            )
        else:
            # Collision: accessed during EIP-684 check, no state change.
            account_expectations[target] = BalAccountExpectation.empty()

    touched_target_idxs = {
        s["target_idx"] for s in sequence if s["target_idx"] is not None
    }
    final_factory_nonce = factory_pre_nonce + len(touched_target_idxs)
    post: dict = {
        factory: Account(nonce=final_factory_nonce),
        **{sender: Account(nonce=1) for sender in senders},
    }
    for s in sequence:
        if s["target_idx"] is None:
            continue
        target = targets[s["target_idx"]]
        post[target] = (
            Account(nonce=1, code=deploy_code)
            if s["deployed"]
            else Account(code=collision_code)
        )
    for k, target in enumerate(targets):
        if k not in touched_target_idxs:
            post[target] = Account.NONEXISTENT

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post=post,
    )


@pytest.mark.parametrize(
    "funding_method",
    ["direct_call", "selfdestruct"],
)
def test_bal_cross_tx_balance_dependency(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    funding_method: str,
) -> None:
    """
    Verify clients apply Tx1's balance change before executing Tx2 in
    the same block. Tx1 routes value into a contract; Tx2 invokes the
    contract which records its `SELFBALANCE` to storage. A client that
    parallelizes Tx2 without applying Tx1's `balance_changes` would
    record the pre-block balance, yielding a different state root. The
    `selfdestruct` variant routes the funds via SELFDESTRUCT from a
    pre-funded killer contract so the recipient's bytecode never runs
    in Tx1 — catching any client optimization that ties balance
    tracking to code execution.
    """
    transferred = 1
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    # Any non-empty calldata triggers the SELFBALANCE record path;
    # empty calldata is the value-receiver path.
    contract = pre.deploy_contract(
        code=Conditional(
            condition=Op.ISZERO(Op.CALLDATASIZE),
            if_true=Op.STOP,
            if_false=Op.SSTORE(0, Op.SELFBALANCE),
        ),
    )

    if funding_method == "direct_call":
        tx_send = Transaction(sender=alice, to=contract, value=transferred)
        send_expectations: dict = {}
    elif funding_method == "selfdestruct":
        killer = pre.deploy_contract(
            code=Op.SELFDESTRUCT(contract),
            balance=transferred,
        )
        tx_send = Transaction(sender=alice, to=killer)
        send_expectations = {
            killer: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=0),
                ],
            ),
        }
    else:
        raise ValueError(f"unknown funding_method: {funding_method}")

    tx_read = Transaction(sender=bob, to=contract, data=b"\x01")

    account_expectations = {
        contract: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(
                    block_access_index=1, post_balance=transferred
                ),
            ],
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=2, post_value=transferred
                        ),
                    ],
                ),
            ],
        ),
        **send_expectations,
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_send, tx_read],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            contract: Account(balance=transferred, storage={0: transferred}),
        },
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "eunice_outcome",
    [
        pytest.param("success", id="success"),
        pytest.param("oog_minus_1", id="oog_minus_1"),
        pytest.param(
            "insufficient_funds",
            id="insufficient_funds",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_bal_cross_tx_funding_chain(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    eunice_outcome: str,
) -> None:
    """
    Funding chain: alice → bob → charlie → dan → eunice → target. Each
    intermediate starts empty and must receive the prior tx's forwarded
    value to afford its own upfront gas + outgoing transfer. A client
    that parallelizes any later tx against pre-block state would see a
    zero balance on its sender and wrongly reject the block. The
    `oog_minus_1` variant funds eunice with exactly `gas_limit - 1`
    worth of gas so her SSTORE OOGs at the boundary (target's BAL flips
    from `storage_changes` to `storage_reads`). The `insufficient_funds`
    variant has dan forward one wei short of eunice's `gas_limit *
    gas_price`, so eunice's tx is rejected pre-execution and the entire
    block MUST be rejected with `INSUFFICIENT_ACCOUNT_FUNDS` — a sanity
    check on the off-by-one boundary of the upfront balance check.
    """
    gas_price = 0xA

    target_code = Op.SSTORE(
        0, 0xC0FFEE, key_warm=False, original_value=0, new_value=0xC0FFEE
    )
    target = pre.deploy_contract(code=target_code)

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    # Last hop (eunice -> target) is a plain CONTRACT call with no
    # value, so the default intrinsic applies.
    intrinsic_gas = intrinsic_calc()
    eunice_exact_gas = intrinsic_gas + target_code.gas_cost(fork)
    eunice_gas_limit = (
        eunice_exact_gas - 1
        if eunice_outcome == "oog_minus_1"
        else eunice_exact_gas
    )
    eunice_upfront = eunice_gas_limit * gas_price
    # Forwarding hops (alice -> bob, ..., dan -> eunice) transfer value
    # to recipients that begin empty, so each pays the value-transfer
    # intrinsic surcharges plus the top-frame ``NEW_ACCOUNT`` state
    # charge that fires under EIP-2780. With the default zero
    # state-gas reservoir the latter spills entirely into execution gas.
    forwarding_intrinsic = intrinsic_calc(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    forwarding_top_frame_state = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    forwarding_gas = forwarding_intrinsic + forwarding_top_frame_state
    transfer_cost = forwarding_gas * gas_price

    # Each sender (including alice) starts with or receives exactly what
    # the next forward + its own gas demands; everyone ends at zero in
    # the success/oog variants. `insufficient_funds` shorts eunice by
    # one wei via dan, leaving her unable to cover upfront gas.
    dan_value = (
        eunice_upfront - 1
        if eunice_outcome == "insufficient_funds"
        else eunice_upfront
    )
    charlie_value = transfer_cost + dan_value
    bob_value = transfer_cost + charlie_value
    alice_value = transfer_cost + bob_value
    alice_pre_balance = transfer_cost + alice_value

    alice = pre.fund_eoa(amount=alice_pre_balance)
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)
    dan = pre.fund_eoa(amount=0)
    eunice = pre.fund_eoa(amount=0)

    eunice_error = (
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
        if eunice_outcome == "insufficient_funds"
        else None
    )

    txs = [
        Transaction(
            sender=alice,
            to=bob,
            value=alice_value,
            gas_limit=forwarding_gas,
            gas_price=gas_price,
        ),
        Transaction(
            sender=bob,
            to=charlie,
            value=bob_value,
            gas_limit=forwarding_gas,
            gas_price=gas_price,
        ),
        Transaction(
            sender=charlie,
            to=dan,
            value=charlie_value,
            gas_limit=forwarding_gas,
            gas_price=gas_price,
        ),
        Transaction(
            sender=dan,
            to=eunice,
            value=dan_value,
            gas_limit=forwarding_gas,
            gas_price=gas_price,
        ),
        Transaction(
            sender=eunice,
            to=target,
            gas_limit=eunice_gas_limit,
            gas_price=gas_price,
            error=eunice_error,
        ),
    ]

    if eunice_outcome == "insufficient_funds":
        blockchain_test(
            pre=pre,
            blocks=[
                Block(
                    txs=txs,
                    exception=(
                        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
                    ),
                )
            ],
            post={},
        )
        return

    if eunice_outcome == "oog_minus_1":
        target_bal = BalAccountExpectation(
            storage_reads=[0],
            nonce_changes=[],
            balance_changes=[],
            code_changes=[],
            storage_changes=[],
        )
        target_post = Account(storage={})
    elif eunice_outcome == "success":
        target_bal = BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=5, post_value=0xC0FFEE
                        ),
                    ],
                ),
            ],
            nonce_changes=[],
            balance_changes=[],
            code_changes=[],
            storage_reads=[],
        )
        target_post = Account(storage={0: 0xC0FFEE})
    else:
        raise ValueError(f"unknown eunice_outcome: {eunice_outcome}")

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=0),
            ],
        ),
        bob: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=2, post_nonce=1)],
            balance_changes=[
                BalBalanceChange(
                    block_access_index=1, post_balance=alice_value
                ),
                BalBalanceChange(block_access_index=2, post_balance=0),
            ],
        ),
        charlie: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=3, post_nonce=1)],
            balance_changes=[
                BalBalanceChange(block_access_index=2, post_balance=bob_value),
                BalBalanceChange(block_access_index=3, post_balance=0),
            ],
        ),
        dan: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=4, post_nonce=1)],
            balance_changes=[
                BalBalanceChange(
                    block_access_index=3, post_balance=charlie_value
                ),
                BalBalanceChange(block_access_index=4, post_balance=0),
            ],
        ),
        eunice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=5, post_nonce=1)],
            balance_changes=[
                BalBalanceChange(block_access_index=4, post_balance=dan_value),
                BalBalanceChange(block_access_index=5, post_balance=0),
            ],
        ),
        target: target_bal,
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations,
                ),
            )
        ],
        post={
            alice: Account(nonce=1, balance=0),
            bob: Account(nonce=1, balance=0),
            charlie: Account(nonce=1, balance=0),
            dan: Account(nonce=1, balance=0),
            eunice: Account(nonce=1, balance=0),
            target: target_post,
        },
    )


def test_bal_cross_block_ripemd160_state_leak(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure internal EVM state for RIMPEMD-160 precompile handling does not
    leak between blocks.

    The EVM may track internal state related to the Parity Touch Bug (EIP-161)
    when calling RIPEMD-160 (0x03) with zero value. If this state is not
    properly reset between blocks, it can cause incorrect BAL entries in
    subsequent blocks.

    Prerequisites for triggering the bug:
    1. RIPEMD-160 (0x03) must already exist in state before the call.
    2. Block 1 must call RIPEMD-160 with zero value and complete successfully.
    3. Block 2 must have a TX that triggers an exception (not REVERT).

    Expected behavior:
    - Block 1: RIPEMD-160 in BAL (legitimate access)
    - Block 2: RIPEMD-160 NOT in BAL (never touched in this block)

    Bug behavior:
    - Block 2 incorrectly has RIPEMD-160 in its BAL due to leaked
      internal state.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    # Pre-fund RIPEMD-160 so it exists before the call.
    # This is required to trigger the internal state tracking.
    ripemd160_addr = Address(0x03)
    pre.fund_address(ripemd160_addr, amount=1)

    # Contract that calls RIPEMD-160 with zero value
    ripemd_caller = pre.deploy_contract(
        code=Op.CALL(50_000, ripemd160_addr, 0, 0, 0, 0, 0) + Op.STOP
    )
    # Contract that triggers an exception
    # (stack underflow from ADD on empty stack)
    exception_contract = pre.deploy_contract(code=Op.ADD)

    # Block 1: Call RIPEMD-160 successfully
    block1 = Block(
        txs=[Transaction(sender=alice, to=ripemd_caller)],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ]
                ),
                bob: None,
                ripemd_caller: BalAccountExpectation.empty(),
                ripemd160_addr: BalAccountExpectation.empty(),
            }
        ),
    )

    # Block 2: Exception triggers internal exception handling.
    # If internal state leaked from Block 1, RIPEMD-160 would incorrectly
    # appear in Block 2's BAL.
    block2 = Block(
        txs=[Transaction(sender=bob, to=exception_contract)],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: None,
                bob: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ]
                ),
                # this is the important check
                ripemd160_addr: None,
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block1, block2],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            ripemd160_addr: Account(balance=1),
        },
    )


@pytest.mark.parametrize(
    "touch_first",
    [
        pytest.param(True, id="zero_value_touch"),
        pytest.param(False, id="no_touch"),
    ],
)
def test_bal_insufficient_balance_call_to_touched_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    touch_first: bool,
) -> None:
    """
    Ensure BAL records a dead precompile reached only by a failed value
    transfer, with or without a prior zero-value touch.

    The value call fails its balance check after the target access is
    charged, so RIPEMD-160 must appear in the BAL with empty changes and
    must not exist in post-state. Regression test for
    https://github.com/erigontech/erigon/issues/23670.
    """
    ripemd160_addr = Address(0x03)
    alice = pre.fund_eoa()

    value_call = Op.POP(Op.CALL(gas=100_000, address=ripemd160_addr, value=2))
    if touch_first:
        code = (
            Op.POP(Op.CALL(gas=100_000, address=ripemd160_addr)) + value_call
        )
    else:
        code = value_call
    caller = pre.deploy_contract(code, balance=1)

    tx = Transaction(sender=alice, to=caller)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                caller: BalAccountExpectation.empty(),
                ripemd160_addr: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            caller: Account(balance=1),
            ripemd160_addr: Account.NONEXISTENT,
        },
    )


@EIPChecklist.BlockLevelConstraint.Test.Content.TransactionTypes()
def test_bal_all_transaction_types(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL with all 5 tx types in single block.

    Types: Legacy, EIP-2930, EIP-1559, Blob, EIP-7702.
    Each tx writes to contract storage. Access list addresses are pre-warmed
    but NOT in BAL.

    Expected BAL:
    - All 5 senders: nonce_changes
    - Contracts 0-3: storage_changes
    - Alice (7702): nonce_changes, code_changes (delegation), storage_changes
    - Oracle: empty (delegation target, accessed)
    """
    from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

    # Create senders for each transaction type
    sender_0 = pre.fund_eoa()  # Type 0 - Legacy
    sender_1 = pre.fund_eoa()  # Type 1 - Access List
    sender_2 = pre.fund_eoa()  # Type 2 - EIP-1559
    sender_3 = pre.fund_eoa()  # Type 3 - Blob
    sender_4 = pre.fund_eoa()  # Type 4 - EIP-7702

    # Create contracts for each tx type (except 7702 which uses delegation)
    contract_code = Op.SSTORE(0x01, Op.CALLDATALOAD(0)) + Op.STOP
    contract_0 = pre.deploy_contract(code=contract_code)
    contract_1 = pre.deploy_contract(code=contract_code)
    contract_2 = pre.deploy_contract(code=contract_code)
    contract_3 = pre.deploy_contract(code=contract_code)

    # For Type 4 (EIP-7702): Alice delegates to Oracle
    alice = pre.fund_eoa()
    oracle = pre.deploy_contract(code=Op.SSTORE(0x01, 0x05) + Op.STOP)

    # Dummy address to warm in access list
    warmed_address = pre.fund_eoa(amount=1)

    # TX1: Type 0 - Legacy transaction
    tx_type_0 = Transaction(
        ty=0,
        sender=sender_0,
        to=contract_0,
        gas_price=10,
        data=Hash(0x01),  # Value to store
    )

    # TX2: Type 1 - Access List transaction (EIP-2930)
    tx_type_1 = Transaction(
        ty=1,
        sender=sender_1,
        to=contract_1,
        gas_price=10,
        data=Hash(0x02),
        access_list=[
            AccessList(
                address=warmed_address,
                storage_keys=[],
            )
        ],
    )

    # TX3: Type 2 - EIP-1559 Dynamic fee transaction
    tx_type_2 = Transaction(
        ty=2,
        sender=sender_2,
        to=contract_2,
        max_fee_per_gas=50,
        max_priority_fee_per_gas=5,
        data=Hash(0x03),
    )

    # TX4: Type 3 - Blob transaction (EIP-4844)
    # Blob versioned hashes need KZG version prefix (0x01)
    blob_hashes = add_kzg_version([Hash(0xBEEF)], 1)
    tx_type_3 = Transaction(
        ty=3,
        sender=sender_3,
        to=contract_3,
        max_fee_per_gas=50,
        max_priority_fee_per_gas=5,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=blob_hashes,
        data=Hash(0x04),
    )

    # TX5: Type 4 - EIP-7702 Set Code transaction
    tx_type_4 = Transaction(
        ty=4,
        sender=sender_4,
        to=alice,
        max_fee_per_gas=50,
        max_priority_fee_per_gas=5,
        authorization_list=[
            AuthorizationTuple(
                address=oracle,
                nonce=0,
                signer=alice,
            )
        ],
    )

    block = Block(
        txs=[tx_type_0, tx_type_1, tx_type_2, tx_type_3, tx_type_4],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # Type 0 sender
                sender_0: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # Type 1 sender
                sender_1: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=2, post_nonce=1)
                    ],
                ),
                # Type 2 sender
                sender_2: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=3, post_nonce=1)
                    ],
                ),
                # Type 3 sender
                sender_3: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=4, post_nonce=1)
                    ],
                ),
                # Type 4 sender
                sender_4: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=5, post_nonce=1)
                    ],
                ),
                # Contract touched by Type 0
                contract_0: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x01
                                )
                            ],
                        )
                    ],
                ),
                # Contract touched by Type 1
                contract_1: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=2, post_value=0x02
                                )
                            ],
                        )
                    ],
                ),
                # Note: warmed_address from access_list is NOT in BAL
                # because access lists pre-warm but don't record in BAL
                # Contract touched by Type 2
                warmed_address: None,  # explicit check
                contract_2: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=3, post_value=0x03
                                )
                            ],
                        )
                    ],
                ),
                # Contract touched by Type 3
                contract_3: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=4, post_value=0x04
                                )
                            ],
                        )
                    ],
                ),
                # Alice (Type 4 delegation target, executes oracle code)
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=5, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=5,
                            new_code=Spec7702.delegation_designation(oracle),
                        )
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=5, post_value=0x05
                                )
                            ],
                        )
                    ],
                ),
                # Oracle (accessed via delegation)
                oracle: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender_0: Account(nonce=1),
            sender_1: Account(nonce=1),
            sender_2: Account(nonce=1),
            sender_3: Account(nonce=1),
            sender_4: Account(nonce=1),
            contract_0: Account(storage={0x01: 0x01}),
            contract_1: Account(storage={0x01: 0x02}),
            contract_2: Account(storage={0x01: 0x03}),
            contract_3: Account(storage={0x01: 0x04}),
            alice: Account(
                nonce=1,
                code=Spec7702.delegation_designation(oracle),
                storage={0x01: 0x05},
            ),
        },
    )


@pytest.mark.pre_alloc_mutable()
def test_bal_lexicographic_address_ordering(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL enforces strict lexicographic byte-wise address ordering.

    Addresses: addr_low (0x...020000), addr_mid (0x...02000000),
    addr_high (0x20...00). Endian-trap: addr_endian_low (0x01...02),
    addr_endian_high (0x02...01). Contract touches them in reverse
    order to verify sorting.

    Expected BAL order: low < mid < high < endian_low < endian_high.
    Catches endianness bugs in address comparison.
    """
    alice = pre.fund_eoa()

    # Create addresses with specific byte patterns for lexicographic testing
    # In lexicographic (byte-wise) order: low < mid < high
    # addr_low:  0x00...020000 (0x02 in third-rightmost byte)
    # addr_mid:  0x00...02000000 (0x02 in fourth-rightmost byte)
    # addr_high: 0x20...00 (leftmost byte = 0x20)
    # Note: Using 0x2xxxx addresses to avoid precompiles (0x01-0x11, 0x100)
    addr_low = Address("0x0000000000000000000000000000000000020000")
    addr_mid = Address("0x0000000000000000000000000000000002000000")
    addr_high = Address("0x2000000000000000000000000000000000000000")

    # Endian-trap addresses: byte-reversals to catch byte-order bugs
    # addr_endian_low:  0x01...02 (0x01 at byte 0, 0x02 at byte 19)
    # addr_endian_high: 0x02...01 (0x02 at byte 0, 0x01 at byte 19)
    # Note: reverse(addr_endian_low) = addr_endian_high
    # Correct order: endian_low < endian_high (0x01 < 0x02 at byte 0)
    # Reversed bytes would incorrectly get opposite order
    addr_endian_low = Address("0x0100000000000000000000000000000000000002")
    addr_endian_high = Address("0x0200000000000000000000000000000000000001")

    # Give each address a balance so they exist
    addr_balance = 100
    pre[addr_low] = Account(balance=addr_balance)
    pre[addr_mid] = Account(balance=addr_balance)
    pre[addr_high] = Account(balance=addr_balance)
    pre[addr_endian_low] = Account(balance=addr_balance)
    pre[addr_endian_high] = Account(balance=addr_balance)

    # Contract that accesses addresses in REVERSE lexicographic order
    # to verify sorting is applied correctly
    contract_code = (
        Op.BALANCE(addr_high)  # Access high first
        + Op.POP
        + Op.BALANCE(addr_low)  # Access low second
        + Op.POP
        + Op.BALANCE(addr_mid)  # Access mid third
        + Op.POP
        # Access endian-trap addresses in reverse order
        + Op.BALANCE(addr_endian_high)  # Access endian_high before endian_low
        + Op.POP
        + Op.BALANCE(addr_endian_low)
        + Op.POP
        + Op.STOP
    )

    contract = pre.deploy_contract(code=contract_code)

    tx = Transaction(sender=alice, to=contract)

    # BAL must be sorted lexicographically by address bytes
    # Order: low < mid < high < endian_low < endian_high
    # (sorted by raw address bytes, regardless of access order)
    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                contract: BalAccountExpectation.empty(),
                # These addresses appear in BAL due to BALANCE access
                # The expectation framework verifies correct order
                addr_low: BalAccountExpectation.empty(),
                addr_mid: BalAccountExpectation.empty(),
                addr_high: BalAccountExpectation.empty(),
                # Endian-trap addresses: must be sorted correctly despite being
                # byte-reversals of each other
                addr_endian_low: BalAccountExpectation.empty(),
                addr_endian_high: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            contract: Account(),
            addr_low: Account(balance=addr_balance),
            addr_mid: Account(balance=addr_balance),
            addr_high: Account(balance=addr_balance),
            addr_endian_low: Account(balance=addr_balance),
            addr_endian_high: Account(balance=addr_balance),
        },
    )


def test_bal_storage_slot_numeric_ordering(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL sorts storage slots as fixed-width 32-byte keys (numeric
    order), not by their minimal-length RLP encodings.

    Slots with 1, 2 and 3 byte minimal encodings are accessed in
    reverse numeric order; byte-prefix comparison of the stripped keys
    would order e.g. 0x0100 before 0x02.
    """
    alice = pre.fund_eoa()

    # Written slots span minimal-encoding widths so that stripped-key
    # byte-prefix comparison yields [0x00, 0x0100, 0x010000, 0x02, 0xFF]
    # instead of the numeric [0x00, 0x02, 0xFF, 0x0100, 0x010000].
    # Read slots are disjoint from written ones so they stay in
    # storage_reads. Distinct stored values tie each change to its slot.
    contract_code = (
        # SSTORE in reverse numeric slot order
        Op.SSTORE(0x010000, 0x0E)
        + Op.SSTORE(0x0100, 0x0D)
        + Op.SSTORE(0xFF, 0x0C)
        + Op.SSTORE(0x02, 0x0B)
        + Op.SSTORE(0x00, 0x0A)
        # SLOAD empty slots in reverse numeric order
        + Op.SLOAD(0x0200)
        + Op.POP
        + Op.SLOAD(0x03)
        + Op.POP
        + Op.STOP
    )

    contract = pre.deploy_contract(code=contract_code)

    tx = Transaction(sender=alice, to=contract)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                contract: BalAccountExpectation(
                    # Numeric slot order, regardless of access order
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x0A
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x0B
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=0xFF,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x0C
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x0100,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x0D
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x010000,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x0E
                                )
                            ],
                        ),
                    ],
                    storage_reads=[0x03, 0x0200],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            contract: Account(
                storage={
                    0x00: 0x0A,
                    0x02: 0x0B,
                    0xFF: 0x0C,
                    0x0100: 0x0D,
                    0x010000: 0x0E,
                }
            ),
        },
    )


@EIPChecklist.BlockLevelConstraint.Test.Boundary.Under()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Exact()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Over()
@pytest.mark.parametrize(
    "with_cl_withdrawal",
    [
        pytest.param(False, id="no_cl_withdrawal"),
        pytest.param(True, id="with_cl_withdrawal"),
    ],
)
@pytest.mark.parametrize(
    "with_tx",
    [pytest.param(False, id="no_tx"), pytest.param(True, id="with_tx")],
)
@pytest.mark.parametrize(
    "boundary_offset",
    [
        pytest.param(0, id="at_boundary"),
        pytest.param(
            -1, marks=pytest.mark.exception_test, id="below_boundary"
        ),
    ],
)
def test_bal_gas_limit_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    boundary_offset: int,
    with_tx: bool,
    with_cl_withdrawal: bool,
) -> None:
    """
    BAL max-items cap (``bal_items <= block_gas_limit //
    BLOCK_ACCESS_LIST_ITEM``) must be enforced on the **final** BAL —
    including pre-tx system work (beacon root, history), user txs, and
    post-tx system work (CL withdrawals, queue processing).

    Orthogonal axes:
    - `with_tx`: alice → bob transfer adds 3 items (alice + bob +
      coinbase warmed via EIP-3651).
    - `with_cl_withdrawal`: EIP-4895 withdrawal to a recipient adds 1
      item, processed between txs and the rest of the post-tx system
      work. Together they catch clients that validate the cap before
      `process_withdrawals` runs.
    """
    # Match framework's DEFAULT_BASE_FEE so gas_price == base_fee
    # cancels the priority fee (no coinbase balance_change to absorb
    # into the expected counts).
    base_fee_per_gas = 7

    extra_items = 0
    txs: list = []
    withdrawals: list = []
    expected_accounts: dict = {}
    post: dict = {}

    if with_tx:
        alice = pre.fund_eoa()
        # Fund bob with 1 wei so the recipient is alive at top-frame
        # check time; this avoids the EIP-2780 ``NEW_ACCOUNT`` state
        # charge that would otherwise inflate the tx's gas needs past
        # the BAL-sized ``block_gas_limit``.
        bob = pre.fund_eoa(amount=1)
        # alice (sender) + bob (recipient) + coinbase (EIP-3651 warm).
        extra_items += 3
        txs.append(
            Transaction(
                sender=alice,
                to=bob,
                value=1,
                gas_price=base_fee_per_gas,
            )
        )
        expected_accounts[alice] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        )
        expected_accounts[bob] = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=2)
            ],
        )
        post[bob] = Account(balance=2)

    if with_cl_withdrawal:
        charlie = pre.fund_eoa(amount=0)
        withdrawal_amount_wei = 10**9  # 1 gwei
        # CL withdrawal recipient adds 1 item; processed at
        # block_access_index = len(txs) + 1 (post-tx).
        extra_items += 1
        withdrawals.append(
            Withdrawal(index=0, validator_index=0, address=charlie, amount=1)
        )
        expected_accounts[charlie] = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(
                    block_access_index=len(txs) + 1,
                    post_balance=withdrawal_amount_wei,
                )
            ],
        )
        post[charlie] = Account(balance=withdrawal_amount_wei)

    total_items = fork.empty_block_bal_item_count() + extra_items
    gas_limit = (
        total_items * fork.gas_costs().BLOCK_ACCESS_LIST_ITEM + boundary_offset
    )

    at_boundary = boundary_offset == 0
    block = Block(
        txs=txs,
        withdrawals=withdrawals,
        exception=(
            None
            if at_boundary
            else BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED
        ),
        expected_block_access_list=(
            BlockAccessListExpectation(account_expectations=expected_accounts)
            if at_boundary and expected_accounts
            else None
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post if at_boundary else {},
        genesis_environment=Environment(
            base_fee_per_gas=base_fee_per_gas, gas_limit=gas_limit
        ),
    )


@pytest.mark.parametrize(
    "pre_value",
    [
        pytest.param(0x00, id="slot_starts_empty"),
        pytest.param(0x11, id="slot_starts_nonzero"),
        pytest.param(0xBB, id="intermediate_equals_pre"),
    ],
)
def test_bal_intra_tx_multiple_sstores_same_slot(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    pre_value: int,
) -> None:
    """
    Test that consecutive SSTOREs to the same slot within one tx produce a
    single storage change with the final post-value; intermediate writes
    (0xAA, 0xBB) must not appear in the BAL.
    """
    alice = pre.fund_eoa()

    code = (
        Op.SSTORE(0x01, 0xAA) + Op.SSTORE(0x01, 0xBB) + Op.SSTORE(0x01, 0xCC)
    )
    contract = pre.deploy_contract(code=code, storage={0x01: pre_value})

    tx = Transaction(sender=alice, to=contract)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                ),
                            ],
                        ),
                        contract: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x01,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0xCC,
                                        ),
                                    ],
                                ),
                            ],
                            storage_reads=[],
                            balance_changes=[],
                            code_changes=[],
                            absent_values=BalAccountAbsentValues(
                                storage_changes=[
                                    BalStorageSlot(
                                        slot=0x01,
                                        slot_changes=[
                                            BalStorageChange(
                                                block_access_index=1,
                                                post_value=0xAA,
                                            ),
                                            BalStorageChange(
                                                block_access_index=1,
                                                post_value=0xBB,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            contract: Account(storage={0x01: 0xCC}),
        },
    )


@pytest.mark.parametrize(
    "pre_value,writes",
    [
        pytest.param(
            0xCC, [0xAA, 0xBB, 0xCC], id="nonzero_pre_returns_to_pre"
        ),
        pytest.param(
            0x00, [0xAA, 0xBB, 0x00], id="empty_pre_ephemeral_writes"
        ),
    ],
)
def test_bal_intra_tx_sstores_same_slot_net_zero(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    pre_value: int,
    writes: list[int],
) -> None:
    """
    Test that consecutive SSTOREs to the same slot within one tx with a
    net-zero result are filtered: the slot must appear in storage_reads
    (it was accessed) but must not appear in storage_changes.
    """
    alice = pre.fund_eoa()

    code = Op.SSTORE(0x01, writes[0])
    for v in writes[1:]:
        code += Op.SSTORE(0x01, v)
    contract = pre.deploy_contract(code=code, storage={0x01: pre_value})

    tx = Transaction(sender=alice, to=contract)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                ),
                            ],
                        ),
                        contract: BalAccountExpectation(
                            storage_reads=[0x01],
                            storage_changes=[],
                            balance_changes=[],
                            code_changes=[],
                        ),
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            contract: Account(storage={0x01: pre_value}),
        },
    )
