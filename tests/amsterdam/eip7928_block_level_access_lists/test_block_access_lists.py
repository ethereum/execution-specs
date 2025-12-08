"""Tests for EIP-7928 using the consistent data class pattern."""

from typing import Callable

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Environment,
    Fork,
    Hash,
    Header,
    Op,
    Transaction,
    add_kzg_version,
    compute_create_address,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


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
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    )
    tx_gas_limit = intrinsic_gas_cost + 1000  # add a small buffer

    tx = Transaction(
        sender=alice,
        to=bob,
        value=100,
        gas_limit=tx_gas_limit,
        gas_price=1_000_000_000,
    )

    alice_account = pre[alice]
    assert alice_account is not None, "Alice account should exist"
    alice_initial_balance = alice_account.balance

    # Account for both the value sent and gas cost (gas_price * gas_used)
    alice_final_balance = (
        alice_initial_balance - 100 - (intrinsic_gas_cost * 1_000_000_000)
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1, post_balance=alice_final_balance
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=100)
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
        gas_limit=500000,
    )

    created_contract = compute_create_address(
        address=factory_contract, nonce=1
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                factory_contract: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=2)],
                ),
                created_contract: BalAccountExpectation(
                    code_changes=[
                        BalCodeChange(tx_index=1, new_code=runtime_code_bytes)
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

    tx = Transaction(
        sender=alice, to=oracle_contract, gas_limit=5_000_000, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
                ),
                target_contract: BalAccountExpectation.empty(),
                oracle_contract: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_call_with_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures balance changes from CALL opcode with
    value transfer.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    # Oracle contract that uses CALL to transfer 100 wei to Bob
    oracle_code = Op.CALL(0, bob, 100, 0, 0, 0, 0)
    oracle_contract = pre.deploy_contract(code=oracle_code, balance=200)

    tx = Transaction(
        sender=alice, to=oracle_contract, gas_limit=1_000_000, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                oracle_contract: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=100)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=100)
                    ],
                ),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_callcode_with_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures balance changes from CALLCODE opcode with
    value transfer.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    # TargetContract sends 100 wei to bob
    target_code = Op.CALL(0, bob, 100, 0, 0, 0, 0)
    target_contract = pre.deploy_contract(code=target_code)

    # Oracle contract that uses CALLCODE to execute TargetContract's code
    oracle_code = Op.CALLCODE(50_000, target_contract, 100, 0, 0, 0, 0)
    oracle_contract = pre.deploy_contract(code=oracle_code, balance=200)

    tx = Transaction(
        sender=alice, to=oracle_contract, gas_limit=1_000_000, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                oracle_contract: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=100)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=100)
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
def test_bal_delegated_storage_writes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    delegated_opcode: Callable[[Address], Op],
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
    oracle_code = delegated_opcode(target_contract)
    oracle_contract = pre.deploy_contract(code=oracle_code)

    tx = Transaction(
        sender=alice,
        to=oracle_contract,
        gas_limit=1_000_000,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                oracle_contract: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0x42)
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
        gas_limit=1_000_000,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    alice_initial_balance = 1_000_000
    alice = pre.fund_eoa(amount=alice_initial_balance)
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)  # fee recipient

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator(
        calldata=b"",
        contract_creation=False,
        access_list=[],
    )
    tx_gas_limit = intrinsic_gas + 1000  # add a small buffer
    gas_price = 0xA

    tx = Transaction(
        sender=alice,
        to=bob,
        value=100,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    # EIP-1559 fee calculation:
    # - Total gas cost
    total_gas_cost = intrinsic_gas * gas_price
    # - Tip portion

    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )
    tip_to_charlie = (gas_price - base_fee_per_gas) * intrinsic_gas

    alice_final_balance = alice_initial_balance - 100 - total_gas_cost

    block = Block(
        txs=[tx],
        fee_recipient=charlie,  # Set Charlie as the fee recipient
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1, post_balance=alice_final_balance
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=100)
                    ],
                ),
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1, post_balance=tip_to_charlie
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

    gas_limit = 1_000_000

    tx = Transaction(
        ty=1,
        sender=alice,
        to=bob,
        gas_limit=gas_limit,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    fork: Fork,
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

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_limit = (
        intrinsic_gas_calculator(
            calldata=b"",
            contract_creation=False,
            access_list=[access_list],
        )
        + 1000
    )  # intrinsic + buffer

    tx = Transaction(
        ty=1,
        sender=alice,
        to=pure_calculator,
        gas_limit=gas_limit,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    fork: Fork,
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

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_limit = (
        intrinsic_gas_calculator(
            calldata=b"",
            contract_creation=False,
            access_list=[access_list],
        )
        + 50000
    )  # intrinsic + buffer for storage writes

    tx = Transaction(
        ty=1,
        sender=alice,
        to=storage_writer,
        gas_limit=gas_limit,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                storage_writer: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0x42)
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0x43)
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
    fork: Fork,
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

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_limit = (
        intrinsic_gas_calculator(
            calldata=b"",
            contract_creation=False,
            access_list=[access_list],
        )
        + 50000
    )  # intrinsic + buffer for storage reads

    tx = Transaction(
        ty=1,
        sender=alice,
        to=storage_reader,
        gas_limit=gas_limit,
        access_list=[access_list],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    intrinsic_gas_cost = intrinsic_gas_calculator()

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
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1,
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
    intrinsic_gas_cost = intrinsic_gas_calculator()

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
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1,
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
        sender=alice,
        to=net_zero_bal_contract,
        value=transfer_amount,
        gas_limit=1_000_000,
        gas_price=0xA,
    )

    expected_balance_in_slot = initial_balance + transfer_amount

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
                                    tx_index=1,
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
                            tx_index=1, post_balance=transfer_amount
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
    fork: Fork,
) -> None:
    """Test that BAL captures contract access for pure computation calls."""
    alice = pre.fund_eoa()
    pure_contract = pre.deploy_contract(code=Op.ADD(0x3, 0x2))

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_gas_calculator() + 5_000  # Buffer

    tx = Transaction(
        sender=alice, to=pure_contract, gas_limit=gas_limit, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    fork: Fork,
) -> None:
    """Test that BAL correctly handles no-op storage write."""
    alice = pre.fund_eoa()
    storage_contract = pre.deploy_contract(
        code=Op.SSTORE(0x01, 0x42), storage={0x01: 0x42}
    )

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_limit = (
        intrinsic_gas_calculator()
        # Sufficient gas for write
        + fork.gas_costs().G_COLD_SLOAD
        + fork.gas_costs().G_COLD_ACCOUNT_ACCESS
        + fork.gas_costs().G_STORAGE_SET
        + fork.gas_costs().G_BASE * 10  # Buffer for push
    )

    tx = Transaction(
        sender=alice, to=storage_contract, gas_limit=gas_limit, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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

    tx = Transaction(
        sender=alice, to=storage_contract, gas_limit=5_000_000, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
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

    tx = Transaction(
        sender=alice, to=abort_contract, gas_limit=5_000_000, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
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

    tx = Transaction(
        sender=alice, to=oracle, gas_limit=1_000_000, value=0, gas_price=0xA
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    alice_initial_balance = 1_000_000
    alice = pre.fund_eoa(amount=alice_initial_balance)
    bob = pre.fund_eoa(amount=0)
    coinbase = pre.fund_eoa(amount=0)  # fee recipient

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator(
        calldata=b"",
        contract_creation=False,
        access_list=[],
    )
    tx_gas_limit = intrinsic_gas + 1000

    # Calculate base fee
    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )

    # Set gas_price equal to base_fee so tip = 0
    tx = Transaction(
        sender=alice,
        to=bob,
        value=5,
        gas_limit=tx_gas_limit,
        gas_price=base_fee_per_gas,
    )

    alice_final_balance = (
        alice_initial_balance - 5 - (intrinsic_gas * base_fee_per_gas)
    )

    block = Block(
        txs=[tx],
        fee_recipient=coinbase,
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1, post_balance=alice_final_balance
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=5)
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


@pytest.mark.pre_alloc_group(
    "precompile_funded",
    reason="Expects clean precompile balances, isolate in EngineX",
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
        gas_limit=5_000_000,
        data=tx_data,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                precompile: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=value)
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


@pytest.mark.parametrize_by_fork(
    "precompile",
    lambda fork: [
        pytest.param(addr, id=f"0x{int.from_bytes(addr, 'big'):02x}")
        for addr in fork.precompiles(block_number=0, timestamp=0)
    ],
)
def test_bal_precompile_call(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
) -> None:
    """
    Ensure BAL records precompile when called via contract.

    Alice calls Oracle contract which calls precompile.
    BAL must include precompile with no balance/storage/code changes.
    """
    alice = pre.fund_eoa()

    # Oracle contract that calls the precompile
    oracle = pre.deploy_contract(
        code=Op.CALL(100_000, precompile, 0, 0, 0, 0, 0) + Op.STOP
    )

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=200_000,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
        pytest.param(10**18, id="positive_value"),
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
    bob = Address(0xB0B)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=value,
        gas_limit=100_000,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=value)
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
    bob = Address(0xB0B)
    oracle_balance = 2 * 10**18

    oracle_code = account_access_opcode(bob)
    oracle = pre.deploy_contract(code=oracle_code, balance=oracle_balance)

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=1_000_000,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
    "opcode_type,value",
    [
        pytest.param("call", 0, id="call_zero_value"),
        pytest.param("call", 10**18, id="call_positive_value"),
        pytest.param("callcode", 0, id="callcode_zero_value"),
        pytest.param("callcode", 10**18, id="callcode_positive_value"),
    ],
)
def test_bal_nonexistent_account_access_value_transfer(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    opcode_type: str,
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
    bob = Address(0xB0B)
    oracle_balance = 2 * 10**18

    if opcode_type == "call":
        oracle_code = Op.CALL(100_000, bob, value, 0, 0, 0, 0)
    else:  # callcode
        oracle_code = Op.CALLCODE(100_000, bob, value, 0, 0, 0, 0)

    oracle = pre.deploy_contract(code=oracle_code, balance=oracle_balance)

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=1_000_000,
    )

    # Calculate expected balances
    if opcode_type == "call" and value > 0:
        # CALL: Oracle loses value, Bob gains value
        oracle_final_balance = oracle_balance - value
        bob_final_balance = value
        bob_has_balance_change = True
        oracle_has_balance_change = True
    elif opcode_type == "callcode" and value > 0:
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
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                oracle: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1, post_balance=oracle_final_balance
                        )
                    ]
                    if oracle_has_balance_change
                    else [],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            tx_index=1, post_balance=bob_final_balance
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
    tx_intrinsic_gas = intrinsic_gas_calculator(calldata=b"", access_list=[])

    # bob receives funds in tx0, then spends everything in tx1
    gas_price = 10
    tx1_gas_cost = tx_intrinsic_gas * gas_price
    spend_amount = 100
    funding_amount = tx1_gas_cost + spend_amount

    tx0 = Transaction(
        sender=alice,
        to=bob,
        value=funding_amount,
        gas_limit=tx_intrinsic_gas,
        gas_price=gas_price,
    )

    tx1 = Transaction(
        sender=bob,
        to=charlie,
        value=spend_amount,
        gas_limit=tx_intrinsic_gas,
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
                                BalNonceChange(tx_index=1, post_nonce=1)
                            ],
                        ),
                        bob: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(tx_index=2, post_nonce=1)
                            ],
                            balance_changes=[
                                BalBalanceChange(
                                    tx_index=1,
                                    post_balance=bob_balance_after_tx0,
                                ),
                                BalBalanceChange(
                                    tx_index=2,
                                    post_balance=bob_balance_after_tx1,
                                ),
                            ],
                        ),
                        charlie: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    tx_index=2, post_balance=spend_amount
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
                                BalNonceChange(tx_index=1, post_nonce=1),
                                BalNonceChange(tx_index=2, post_nonce=2),
                                BalNonceChange(tx_index=3, post_nonce=3),
                            ],
                        ),
                        contract: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=1,
                                    slot_changes=[
                                        BalStorageChange(
                                            tx_index=1, post_value=1
                                        ),
                                        BalStorageChange(
                                            tx_index=2, post_value=2
                                        ),
                                        BalStorageChange(
                                            tx_index=3, post_value=3
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
            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
        gas_limit=100_000,
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
        ),
        contract_address: BalAccountExpectation(
            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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


def test_bal_cross_tx_storage_revert_to_zero(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures storage changes when tx1 writes a non-zero value
    and tx2 reverts it back to zero. This is a regression test for the
    blobhash scenario where slot changes were being incorrectly filtered
    as net-zero across transaction boundaries.

    Tx1: slot 0 = 0x0 -> 0xABCD (change recorded at tx_index=1)
    Tx2: slot 0 = 0xABCD -> 0x0 (change MUST be recorded at tx_index=2)
    """
    alice = pre.fund_eoa()

    # Contract that writes to slot 0 based on calldata
    contract = pre.deploy_contract(code=Op.SSTORE(0, Op.CALLDATALOAD(0)))

    # Tx1: Write slot 0 = 0xABCD
    tx1 = Transaction(
        sender=alice,
        to=contract,
        data=Hash(0xABCD),
        gas_limit=100_000,
    )

    # Tx2: Write slot 0 = 0x0 (revert to zero)
    tx2 = Transaction(
        sender=alice,
        to=contract,
        data=Hash(0x0),
        gas_limit=100_000,
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(tx_index=1, post_nonce=1),
                BalNonceChange(tx_index=2, post_nonce=2),
            ],
        ),
        contract: BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    slot_changes=[
                        BalStorageChange(tx_index=1, post_value=0xABCD),
                        # CRITICAL: tx2's write to 0x0 MUST appear
                        # even though it returns slot to original value
                        BalStorageChange(tx_index=2, post_value=0x0),
                    ],
                ),
            ],
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
            contract: Account(storage={0: 0x0}),
        },
    )


@pytest.mark.pre_alloc_group(
    "ripemd160_state_leak",
    reason="Pre-funds RIPEMD-160, must be isolated in EngineX format",
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
        txs=[
            Transaction(
                sender=alice,
                to=ripemd_caller,
                gas_limit=100_000,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
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
        txs=[
            Transaction(
                sender=bob,
                to=exception_contract,
                gas_limit=100_000,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: None,
                bob: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
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
        gas_limit=100_000,
        gas_price=10,
        data=Hash(0x01),  # Value to store
    )

    # TX2: Type 1 - Access List transaction (EIP-2930)
    tx_type_1 = Transaction(
        ty=1,
        sender=sender_1,
        to=contract_1,
        gas_limit=100_000,
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
        gas_limit=100_000,
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
        gas_limit=100_000,
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
        gas_limit=100_000,
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
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                # Type 1 sender
                sender_1: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=2, post_nonce=1)],
                ),
                # Type 2 sender
                sender_2: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=3, post_nonce=1)],
                ),
                # Type 3 sender
                sender_3: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=4, post_nonce=1)],
                ),
                # Type 4 sender
                sender_4: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=5, post_nonce=1)],
                ),
                # Contract touched by Type 0
                contract_0: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0x01)
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
                                BalStorageChange(tx_index=2, post_value=0x02)
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
                                BalStorageChange(tx_index=3, post_value=0x03)
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
                                BalStorageChange(tx_index=4, post_value=0x04)
                            ],
                        )
                    ],
                ),
                # Alice (Type 4 delegation target, executes oracle code)
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=5, post_nonce=1)],
                    code_changes=[
                        BalCodeChange(
                            tx_index=5,
                            new_code=Spec7702.delegation_designation(oracle),
                        )
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(tx_index=5, post_value=0x05)
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


def test_bal_lexicographic_address_ordering(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL enforces strict lexicographic byte-wise address ordering.

    Addresses: addr_low (0x...01), addr_mid (0x...0100), addr_high (0x01...00).
    Endian-trap: addr_endian_low (0x01...02), addr_endian_high (0x02...01).
    Contract touches them in reverse order to verify sorting.

    Expected BAL order: low < mid < high < endian_low < endian_high.
    Catches endianness bugs in address comparison.
    """
    alice = pre.fund_eoa()

    # Create addresses with specific byte patterns for lexicographic testing
    # In lexicographic (byte-wise) order: low < mid < high
    # addr_low:  0x00...01 (rightmost byte = 0x01)
    # addr_mid:  0x00...0100 (second-rightmost byte = 0x01)
    # addr_high: 0x01...00 (leftmost byte = 0x01)
    addr_low = Address("0x0000000000000000000000000000000000000001")
    addr_mid = Address("0x0000000000000000000000000000000000000100")
    addr_high = Address("0x0100000000000000000000000000000000000000")

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

    tx = Transaction(
        sender=alice,
        to=contract,
        gas_limit=1_000_000,
    )

    # BAL must be sorted lexicographically by address bytes
    # Order: low < mid < high < endian_low < endian_high
    # (sorted by raw address bytes, regardless of access order)
    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
