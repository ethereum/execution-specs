"""Test the SELFDESTRUCT opcode."""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Byzantium, Cancun
from execution_testing.forks.helpers import Fork


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize("same_tx_selfdestruct", [False, True])
@pytest.mark.parametrize("warm_beneficiary", [False, True])
@pytest.mark.valid_from("Homestead")
def test_selfdestruct_to_precompile_and_oog_at_minus_1(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    precompile: Address,
    same_tx_selfdestruct: bool,
    warm_beneficiary: bool,
) -> None:
    """
    Test successful SELFDESTRUCT to precompile with exact gas.

    Pre-Cancun: Contract is always destroyed.
    >=Cancun (EIP-6780): Contract only destroyed if created in same
    transaction.
    """
    alice = pre.fund_eoa()

    victim_balance = 100
    victim_code = Op.SELFDESTRUCT(precompile)

    gas_costs = fork.gas_costs()
    push_cost = gas_costs.G_VERY_LOW
    selfdestruct_cost = gas_costs.G_SELF_DESTRUCT
    new_account_cost = gas_costs.G_NEW_ACCOUNT
    if warm_beneficiary:
        warming_cost = 0
    else:
        warming_cost = gas_costs.G_COLD_ACCOUNT_ACCESS
    exact_gas = push_cost + selfdestruct_cost + new_account_cost + warming_cost

    if same_tx_selfdestruct:
        # Deploy and selfdestruct in same transaction
        # Factory creates victim via CREATE, then calls it
        initcode = Initcode(deploy_code=victim_code)
        initcode_bytes = bytes(initcode)

        # pre-calculate the factory and victim addresses
        factory_address = next(pre._contract_address_iterator)  # type: ignore
        victim = compute_create_address(address=factory_address, nonce=1)

        factory_code = (
            Op.MSTORE(0, Op.PUSH32(initcode_bytes))
            + Op.CREATE(
                value=victim_balance,
                offset=32 - len(initcode_bytes),
                size=len(initcode_bytes),
            )
            + Op.POP  # Discard CREATE result, we know the address
            + Op.CALL(gas=exact_gas, address=victim)
        )
        # actual deploy using known address
        factory = pre.deploy_contract(
            address=factory_address,
            code=factory_code,
            balance=victim_balance,
        )
        caller = factory
    else:
        # pre-existing contract
        victim = pre.deploy_contract(code=victim_code, balance=victim_balance)
        caller_code = Op.CALL(gas=exact_gas, address=victim)
        caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=200_000,
        protected=fork >= Byzantium,
    )

    # BAL expectations >= Amsterdam
    expected_block_access_list = None
    if fork.header_bal_hash_required():
        if same_tx_selfdestruct:
            # Factory does CREATE (nonce 1->2) and transfers balance to victim
            # Victim is created and destroyed in same tx - no net changes
            account_expectations: Dict[
                Address, BalAccountExpectation | None
            ] = {
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                caller: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0)
                    ],
                    code_changes=[],
                    storage_changes=[],
                    storage_reads=[],
                ),
                # Victim created and destroyed in same tx - empty changes
                victim: BalAccountExpectation.empty(),
                precompile: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=victim_balance
                        )
                    ],
                    nonce_changes=[],
                    code_changes=[],
                    storage_changes=[],
                    storage_reads=[],
                ),
            }
        else:
            account_expectations = {
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                caller: BalAccountExpectation.empty(),
                victim: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0)
                    ],
                    nonce_changes=[],
                    code_changes=[],
                    storage_changes=[],
                    storage_reads=[],
                ),
                precompile: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=victim_balance
                        )
                    ],
                    nonce_changes=[],
                    code_changes=[],
                    storage_changes=[],
                    storage_reads=[],
                ),
            }
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    # post state depends on fork and same_tx_selfdestruct
    contract_destroyed = fork < Cancun or same_tx_selfdestruct
    # Factory nonce is 2 after CREATE, otherwise caller nonce stays at 1
    caller_nonce = 2 if same_tx_selfdestruct else 1
    if contract_destroyed:
        post = {
            alice: Account(nonce=1),
            caller: Account(nonce=caller_nonce),
            victim: Account.NONEXISTENT,
            precompile: Account(balance=victim_balance),
        }
    else:
        # >=Cancun with pre-existing contract, code preserved
        post = {
            alice: Account(nonce=1),
            caller: Account(nonce=caller_nonce),
            victim: Account(balance=0, code=victim_code),
            precompile: Account(balance=victim_balance),
        }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=expected_block_access_list,
            )
        ],
        post=post,
    )
