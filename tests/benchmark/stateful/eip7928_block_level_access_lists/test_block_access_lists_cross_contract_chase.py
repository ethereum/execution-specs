"""
Tests for EIP-7928 BAL with cross-contract pointer chasing.

Uses a **dispatcher contract** that all transactions call.  The
dispatcher reads a cursor (chain index) from CURSOR_SLOT, looks up
the chain entry-point address from its own storage, CALLs it, and
increments the cursor.

Each chain is a series of contracts linked through storage slot 0:
contract N stores the address of contract N+1.  The last contract
stores zero (sentinel).

The cursor mechanism ensures TX N+1 depends on TX N's state,
requiring the BAL to parallelize execution.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Op,
    Storage,
    Transaction,
)

from .helpers import CURSOR_SLOT
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

MAX_CALL_DEPTH = 100


def create_dispatcher_contract() -> Bytecode:
    """
    Create dispatcher that reads cursor, looks up entry address, CALLs it.

    1. chain_idx   = SLOAD(CURSOR_SLOT)
    2. entry_addr  = SLOAD(chain_idx)
    3. CALL(entry_addr)
    4. SSTORE(CURSOR_SLOT, chain_idx + 1)
    """
    code = (
        # 1. Read cursor (chain index)
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD  # stack: [chain_idx]
        # 2. Look up entry address
        + Op.DUP1
        + Op.SLOAD  # stack: [entry_addr, chain_idx]
        # 3. CALL(gas, entry_addr, 0, 0, 0, 0, 0)
        + Op.PUSH1(0x00)  # retSize
        + Op.PUSH1(0x00)  # retOffset
        + Op.PUSH1(0x00)  # argsSize
        + Op.PUSH1(0x00)  # argsOffset
        + Op.PUSH1(0x00)  # value
        + Op.DUP6  # entry_addr
        + Op.GAS
        + Op.CALL
        + Op.POP  # drop success
        + Op.POP  # drop entry_addr
        # 4. Increment cursor: chain_idx + 1
        + Op.PUSH1(0x01)
        + Op.ADD
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE
        + Op.STOP
    )
    return code


def create_chain_contract() -> Bytecode:
    """
    Create contract that reads slot 0 and CALLs that address.

    Reads next_addr from storage slot 0, then CALLs it with remaining gas.
    """
    end = 0x16
    code = (
        Op.PUSH1(0x00)
        + Op.SLOAD  # next_addr = SLOAD(0)
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH1(end)
        + Op.JUMPI
        + Op.PUSH1(0x00)  # retSize
        + Op.PUSH1(0x00)  # retOffset
        + Op.PUSH1(0x00)  # argsSize
        + Op.PUSH1(0x00)  # argsOffset
        + Op.PUSH1(0x00)  # value
        + Op.DUP6  # next_addr
        + Op.GAS
        + Op.CALL
        + Op.POP
        + Op.JUMPDEST  # end
        + Op.STOP
    )
    return code


def _calculate_params(block_gas_limit: int, fork: Fork) -> tuple[int, int]:
    """Return (num_transactions, chain_length)."""
    gas_costs = fork.gas_costs()
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None

    num_transactions = block_gas_limit // max_tx_gas
    dispatcher_cost = create_dispatcher_contract().gas_cost(fork)
    chain_hop_cost = create_chain_contract().gas_cost(fork)
    available_gas = max_tx_gas - gas_costs.G_TRANSACTION - dispatcher_cost
    chain_by_gas = available_gas // chain_hop_cost
    chain_length = min(chain_by_gas, MAX_CALL_DEPTH)
    return num_transactions, chain_length


def _run_cross_contract_chase(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    num_transactions: int,
    chain_length: int,
    gas_limit: int,
) -> None:
    """Run a cross-contract chase benchmark."""
    chain_code = create_chain_contract()
    total_contracts = num_transactions * chain_length

    # Deploy all chain contracts.
    contracts: list[Address] = []
    for _ in range(total_contracts):
        c = pre.deploy_contract(code=chain_code, storage=Storage({}))
        contracts.append(c)

    # Link contracts within each chain.
    for tx_idx in range(num_transactions):
        start = tx_idx * chain_length
        for i in range(chain_length - 1):
            current = contracts[start + i]
            next_addr = contracts[start + i + 1]
            pre[current].storage[0] = int.from_bytes(Address(next_addr), "big")

    # Deploy dispatcher with entry-point lookup table.
    entry_storage: dict[int, int] = {
        tx_idx: int.from_bytes(
            Address(contracts[tx_idx * chain_length]), "big"
        )
        for tx_idx in range(num_transactions)
    }
    entry_storage[CURSOR_SLOT] = 0
    dispatcher = pre.deploy_contract(
        code=create_dispatcher_contract(),
        storage=Storage(entry_storage),
    )

    # All TXs call the dispatcher with empty calldata.
    senders = [pre.fund_eoa() for _ in range(num_transactions)]
    transactions = [
        Transaction(
            sender=senders[i],
            to=dispatcher,
            gas_limit=gas_limit,
            data=b"",
        )
        for i in range(num_transactions)
    ]

    # Build expectations.
    account_expectations: dict[Address, BalAccountExpectation] = {}

    # Dispatcher: reads entry-point slots, writes cursor.
    account_expectations[dispatcher] = BalAccountExpectation(
        storage_reads=sorted(range(num_transactions)),
        storage_changes=[
            BalStorageSlot(
                slot=CURSOR_SLOT,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=tx_idx + 1,
                        post_value=tx_idx + 1,
                    )
                    for tx_idx in range(num_transactions)
                ],
            ),
        ],
    )

    # Senders: nonce changes.
    for tx_idx, sender in enumerate(senders):
        account_expectations[sender] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=tx_idx + 1, post_nonce=1)
            ],
        )

    # Chain contracts: each reads slot 0.
    for contract in contracts:
        account_expectations[contract] = BalAccountExpectation(
            storage_reads=[0]
        )

    block = Block(
        txs=transactions,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post: dict[Address, Account] = {}
    for sender in senders:
        post[sender] = Account(nonce=1)

    blockchain_test(pre=pre, blocks=[block], post=post)


def test_bal_cross_contract_chase(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with cross-contract pointer chasing via dispatcher."""
    env = Environment()
    block_gas_limit = int(env.gas_limit)
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None

    num_transactions, chain_length = _calculate_params(block_gas_limit, fork)
    _run_cross_contract_chase(
        pre, blockchain_test, num_transactions, chain_length, max_tx_gas
    )


def test_bal_cross_contract_chase_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Simple validation test with 10 contracts across 2 transactions."""
    _run_cross_contract_chase(
        pre,
        blockchain_test,
        num_transactions=2,
        chain_length=5,
        gas_limit=500_000,
    )
