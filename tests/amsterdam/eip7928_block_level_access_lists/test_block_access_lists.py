"""Tests for EIP-7928 using the consistent data class pattern."""

from typing import Callable, Dict

import pytest

from ethereum_test_base_types import AccessList, Address, Hash
from ethereum_test_forks import Fork
from ethereum_test_specs.blockchain import Header
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Initcode,
    Transaction,
    compute_create_address,
)
from ethereum_test_types import Environment
from ethereum_test_types.block_access_list import (
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
)
from ethereum_test_vm import Opcodes as Op

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
    alice_final_balance = alice_initial_balance - 100 - (intrinsic_gas_cost * 1_000_000_000)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=alice_final_balance)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=100)],
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
        + Op.PUSH1(32 - len(init_code_bytes))  # offset in memory (account for padding)
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

    created_contract = compute_create_address(address=factory_contract, nonce=1)

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
                    code_changes=[BalCodeChange(tx_index=1, new_code=runtime_code_bytes)],
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


@pytest.mark.parametrize("self_destruct_in_same_tx", [True, False], ids=["same_tx", "new_tx"])
@pytest.mark.parametrize("pre_funded", [True, False], ids=["pre_funded", "not_pre_funded"])
def test_bal_self_destruct(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    self_destruct_in_same_tx: bool,
    pre_funded: bool,
) -> None:
    """Ensure BAL captures balance changes caused by `SELFDESTRUCT`."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    selfdestruct_code = (
        Op.SLOAD(0x01)  # Read from storage slot 0x01
        + Op.SSTORE(0x02, 0x42)  # Write to storage slot 0x02
        + Op.SELFDESTRUCT(bob)
    )
    # A pre existing self-destruct contract with initial storage
    kaboom = pre.deploy_contract(code=selfdestruct_code, storage={0x01: 0x123})

    # A template for self-destruct contract
    self_destruct_init_code = Initcode(deploy_code=selfdestruct_code)
    template = pre.deploy_contract(code=self_destruct_init_code)

    transfer_amount = expected_recipient_balance = 100
    pre_fund_amount = 10

    if self_destruct_in_same_tx:
        # The goal is to create a self-destructing contract in the same
        # transaction to trigger deletion of code as per EIP-6780.
        # The factory contract below creates a new self-destructing
        # contract and calls it in this transaction.

        bytecode_size = len(self_destruct_init_code)
        factory_bytecode = (
            # Clone template memory
            Op.EXTCODECOPY(template, 0, 0, bytecode_size)
            # Fund 100 wei and deploy the clone
            + Op.CREATE(transfer_amount, 0, bytecode_size)
            # Call the clone, which self-destructs
            + Op.CALL(100_000, Op.DUP6, 0, 0, 0, 0, 0)
            + Op.STOP
        )

        factory = pre.deploy_contract(code=factory_bytecode)
        kaboom_same_tx = compute_create_address(address=factory, nonce=1)

    # Determine which account will be self-destructed
    self_destructed_account = kaboom_same_tx if self_destruct_in_same_tx else kaboom

    if pre_funded:
        expected_recipient_balance += pre_fund_amount
        pre.fund_address(address=self_destructed_account, amount=pre_fund_amount)

    tx = Transaction(
        sender=alice,
        to=factory if self_destruct_in_same_tx else kaboom,
        value=transfer_amount,
        gas_limit=1_000_000,
        gas_price=0xA,
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
                        BalBalanceChange(tx_index=1, post_balance=expected_recipient_balance)
                    ]
                ),
                self_destructed_account: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=0)]
                    if pre_funded
                    else [],
                    # Accessed slots for same-tx are recorded as reads (0x02)
                    storage_reads=[0x01, 0x02] if self_destruct_in_same_tx else [0x01],
                    # Storage changes are recorded for non-same-tx
                    # self-destructs
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x02, slot_changes=[BalStorageChange(tx_index=1, post_value=0x42)]
                        )
                    ]
                    if not self_destruct_in_same_tx
                    else [],
                    code_changes=[],  # should not be present
                    nonce_changes=[],  # should not be present
                ),
            }
        ),
    )

    post: Dict[Address, Account] = {
        alice: Account(nonce=1),
        bob: Account(balance=expected_recipient_balance),
    }

    # If the account was self-destructed in the same transaction,
    # we expect the account to non-existent and its balance to be 0.
    if self_destruct_in_same_tx:
        post.update(
            {
                factory: Account(
                    nonce=2,  # incremented after CREATE
                    balance=0,  # spent on CREATE
                    code=factory_bytecode,
                ),
                kaboom_same_tx: Account.NONEXISTENT,  # type: ignore
                # The pre-existing contract remains unaffected
                kaboom: Account(balance=0, code=selfdestruct_code, storage={0x01: 0x123}),
            }
        )
    else:
        post.update(
            {
                # This contract was self-destructed in a separate tx.
                # From EIP 6780: `SELFDESTRUCT` does not delete any data
                # (including storage keys, code, or the account itself).
                kaboom: Account(
                    balance=0, code=selfdestruct_code, storage={0x01: 0x123, 0x2: 0x42}
                ),
            }
        )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


@pytest.mark.parametrize(
    "account_access_opcode",
    [
        pytest.param(lambda target_addr: Op.BALANCE(target_addr), id="balance"),
        pytest.param(lambda target_addr: Op.EXTCODESIZE(target_addr), id="extcodesize"),
        pytest.param(lambda target_addr: Op.EXTCODECOPY(target_addr, 0, 0, 32), id="extcodecopy"),
        pytest.param(lambda target_addr: Op.EXTCODEHASH(target_addr), id="extcodehash"),
        pytest.param(lambda target_addr: Op.CALL(0, target_addr, 0, 0, 0, 0, 0), id="call"),
        pytest.param(
            lambda target_addr: Op.CALLCODE(0, target_addr, 0, 0, 0, 0, 0), id="callcode"
        ),
        pytest.param(
            lambda target_addr: Op.DELEGATECALL(0, target_addr, 0, 0, 0, 0), id="delegatecall"
        ),
        pytest.param(
            lambda target_addr: Op.STATICCALL(0, target_addr, 0, 0, 0, 0), id="staticcall"
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

    tx = Transaction(sender=alice, to=oracle_contract, gas_limit=5_000_000, gas_price=0xA)

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

    tx = Transaction(sender=alice, to=oracle_contract, gas_limit=1_000_000, gas_price=0xA)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                oracle_contract: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=100)],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=100)],
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

    tx = Transaction(sender=alice, to=oracle_contract, gas_limit=1_000_000, gas_price=0xA)

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                ),
                oracle_contract: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=100)],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=100)],
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
            lambda target_addr: Op.DELEGATECALL(50000, target_addr, 0, 0, 0, 0), id="delegatecall"
        ),
        pytest.param(
            lambda target_addr: Op.CALLCODE(50000, target_addr, 0, 0, 0, 0, 0), id="callcode"
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
                            slot_changes=[BalStorageChange(tx_index=1, post_value=0x42)],
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
            lambda target_addr: Op.DELEGATECALL(50000, target_addr, 0, 0, 0, 0), id="delegatecall"
        ),
        pytest.param(
            lambda target_addr: Op.CALLCODE(50000, target_addr, 0, 0, 0, 0, 0), id="callcode"
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
    oracle_contract = pre.deploy_contract(code=oracle_code, storage={0x01: 0x42})

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
                        BalBalanceChange(tx_index=1, post_balance=alice_final_balance)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=100)],
                ),
                charlie: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=tip_to_charlie)],
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

    tx = Transaction(ty=1, sender=alice, to=bob, gas_limit=gas_limit, access_list=[access_list])

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
        ty=1, sender=alice, to=pure_calculator, gas_limit=gas_limit, access_list=[access_list]
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
    storage_writer = pre.deploy_contract(code=Op.SSTORE(0x01, 0x42) + Op.SSTORE(0x02, 0x43))

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
        ty=1, sender=alice, to=storage_writer, gas_limit=gas_limit, access_list=[access_list]
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
                            slot_changes=[BalStorageChange(tx_index=1, post_value=0x42)],
                        ),
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[BalStorageChange(tx_index=1, post_value=0x43)],
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
        ty=1, sender=alice, to=storage_reader, gas_limit=gas_limit, access_list=[access_list]
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
        sender=alice, to=alice, gas_limit=intrinsic_gas_cost, value=100, gas_price=0xA
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

    tx = Transaction(sender=alice, to=bob, gas_limit=intrinsic_gas_cost, value=0, gas_price=0xA)

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
        pytest.param(0, 0, "selfdestruct", id="zero_balance_zero_transfer_selfdestruct"),
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
                    storage_reads=[0x00] if expected_balance_in_slot == 0 else [],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=expected_balance_in_slot)
                            ],
                        )
                    ]
                    if expected_balance_in_slot > 0
                    else [],
                ),
                # recipient receives transfer_amount
                recipient: BalAccountExpectation(
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=transfer_amount)]
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
                storage={0x00: expected_balance_in_slot} if expected_balance_in_slot > 0 else {},
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

    tx = Transaction(sender=alice, to=pure_contract, gas_limit=gas_limit, gas_price=0xA)

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
    storage_contract = pre.deploy_contract(code=Op.SSTORE(0x01, 0x42), storage={0x01: 0x42})

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_limit = (
        intrinsic_gas_calculator()
        # Sufficient gas for write
        + fork.gas_costs().G_COLD_SLOAD
        + fork.gas_costs().G_COLD_ACCOUNT_ACCESS
        + fork.gas_costs().G_STORAGE_SET
        + fork.gas_costs().G_BASE * 10  # Buffer for push
    )

    tx = Transaction(sender=alice, to=storage_contract, gas_limit=gas_limit, gas_price=0xA)

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

    tx = Transaction(sender=alice, to=storage_contract, gas_limit=5_000_000, gas_price=0xA)

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
        pytest.param(lambda target_addr: Op.BALANCE(target_addr), id="balance"),
        pytest.param(lambda target_addr: Op.EXTCODESIZE(target_addr), id="extcodesize"),
        pytest.param(lambda target_addr: Op.EXTCODECOPY(target_addr, 0, 0, 32), id="extcodecopy"),
        pytest.param(lambda target_addr: Op.EXTCODEHASH(target_addr), id="extcodehash"),
        pytest.param(lambda target_addr: Op.CALL(0, target_addr, 50, 0, 0, 0, 0), id="call"),
        pytest.param(
            lambda target_addr: Op.CALLCODE(0, target_addr, 50, 0, 0, 0, 0), id="callcode"
        ),
        pytest.param(
            lambda target_addr: Op.DELEGATECALL(0, target_addr, 0, 0, 0, 0), id="delegatecall"
        ),
        pytest.param(
            lambda target_addr: Op.STATICCALL(0, target_addr, 0, 0, 0, 0), id="staticcall"
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

    tx = Transaction(sender=alice, to=abort_contract, gas_limit=5_000_000, gas_price=0xA)

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

    tx = Transaction(sender=alice, to=oracle, gas_limit=1_000_000, value=0, gas_price=0xA)

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
