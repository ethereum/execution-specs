"""
abstract: Tests [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929)
    Test cases for [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929).
"""  # noqa: E501

from typing import Iterator, Tuple

import pytest

from ethereum_test_forks import (
    Fork,
    get_transition_fork_predecessor,
    get_transition_fork_successor,
)
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2929.md"
REFERENCE_SPEC_VERSION = "0e11417265a623adb680c527b15d0cb6701b870b"


def precompile_addresses_in_predecessor_successor(
    fork: Fork,
) -> Iterator[Tuple[Address, bool, bool]]:
    """
    Yield the addresses of precompiled contracts and whether they existed in the parent fork.

    Args:
        fork (Fork): The transition fork instance containing precompiled contract information.

    Yields:
        Iterator[Tuple[str, bool]]: A tuple containing the address in hexadecimal format and a
            boolean indicating whether the address has existed in the predecessor.

    """
    predecessor_precompiles = set(get_transition_fork_predecessor(fork).precompiles())
    successor_precompiles = set(get_transition_fork_successor(fork).precompiles())
    all_precompiles = successor_precompiles | predecessor_precompiles
    highest_precompile = int.from_bytes(max(all_precompiles))
    extra_range = 32
    extra_precompiles = {
        Address(i) for i in range(highest_precompile + 1, highest_precompile + extra_range)
    }
    all_precompiles = all_precompiles | extra_precompiles
    for address in sorted(all_precompiles):
        yield address, address in successor_precompiles, address in predecessor_precompiles


@pytest.mark.valid_at_transition_to("Paris", subsequent_forks=True)
@pytest.mark.parametrize_by_fork(
    "address,precompile_in_successor,precompile_in_predecessor",
    precompile_addresses_in_predecessor_successor,
)
def test_precompile_warming(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    address: Address,
    precompile_in_successor: bool,
    precompile_in_predecessor: bool,
    pre: Alloc,
):
    """
    Call BALANCE of a precompile addresses before and after a fork.

    According to EIP-2929, when a transaction begins, accessed_addresses is initialized to include:
    - tx.sender, tx.to
    - and the set of all precompiles

    This test verifies that:
    1. Precompiles that exist in the predecessor fork are always "warm" (lower gas cost)
    2. New precompiles added in a fork are "cold" before the fork and become "warm" after

    """
    sender = pre.fund_eoa()
    call_cost_slot = 0

    code = (
        Op.GAS
        + Op.BALANCE(address)
        + Op.POP
        + Op.SSTORE(call_cost_slot, Op.SUB(Op.SWAP1, Op.GAS))
        + Op.STOP
    )
    before = pre.deploy_contract(code, storage={call_cost_slot: 0xDEADBEEF})
    after = pre.deploy_contract(code, storage={call_cost_slot: 0xDEADBEEF})

    # Block before fork
    blocks = [
        Block(
            timestamp=10_000,
            txs=[
                Transaction(
                    sender=sender,
                    to=before,
                    gas_limit=1_000_000,
                )
            ],
        )
    ]

    # Block after fork
    blocks += [
        Block(
            timestamp=20_000,
            txs=[
                Transaction(
                    sender=sender,
                    to=after,
                    gas_limit=1_000_000,
                )
            ],
        )
    ]

    predecessor = get_transition_fork_predecessor(fork)
    successor = get_transition_fork_successor(fork)

    def get_expected_gas(precompile_present: bool, fork: Fork) -> int:
        gas_costs = fork.gas_costs()
        warm_access_cost = gas_costs.G_WARM_ACCOUNT_ACCESS
        cold_access_cost = gas_costs.G_COLD_ACCOUNT_ACCESS
        extra_cost = gas_costs.G_BASE * 2 + gas_costs.G_VERY_LOW
        if precompile_present:
            return warm_access_cost + extra_cost
        else:
            return cold_access_cost + extra_cost

    expected_gas_before = get_expected_gas(precompile_in_predecessor, predecessor)
    expected_gas_after = get_expected_gas(precompile_in_successor, successor)

    post = {
        before: Account(storage={call_cost_slot: expected_gas_before}),
        after: Account(storage={call_cost_slot: expected_gas_after}),
    }

    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
    )
