"""
abstract: Vector storage benchmark with single parametrized contract,
targeting SLOAD.

This parametrized test takes takes these arguments:
- The amount of slots to load
- The slot key incrementer

The final value is used in the test as boolean: if 0 is used,
the key is not incremented, and thus the same key is read each time.

Each test is also tested against these keys in the access list (or not).
This thus marks if the target slots are warm or cold.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Storage,
    Transaction,
    While
)

"""
abstract: Vector storage benchmark with single parametrized contract,
targeting SLOAD.

This parametrized test takes takes these arguments:
- The amount of slots to load
- The slot key incrementer

The final value is used in the test as boolean: if 0 is used,
the key is not incremented, and thus the same key is read each time.

Each test is also tested against these keys in the access list (or not).
This thus marks if the target slots are warm or cold.
"""

from typing import List

import pytest

from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Storage,
    Transaction,
)


def create_sload_contract() -> Bytecode:
    """
    Creates a storage contract.
    """
    bytecode = Bytecode()

    end_marker = 24
    start_marker = 4

    bytecode += Op.PUSH0
    bytecode += Op.CALLDATALOAD(Op.PUSH1(32))

    bytecode += Op.JUMPDEST

    bytecode += Op.DUP1

    bytecode += Op.ISZERO
    bytecode += Op.JUMPI(Op.PUSH1(end_marker))

    # Loop entry, stack (topmost item first): [entries_left, current_slot]

    bytecode += Op.PUSH1(1)
    bytecode += Op.SWAP1
    bytecode += Op.SUB

    bytecode += Op.SWAP1

    # Stack here: [current_slot, entries_left]

    bytecode += Op.DUP1

    bytecode += Op.SLOAD
    bytecode += Op.POP

    # Stack here: [current_slot, entries_left]

    bytecode += Op.ADD(Op.CALLDATALOAD(Op.PUSH0))

    bytecode += Op.SWAP1

    bytecode += Op.PUSH1(start_marker)

    bytecode += Op.JUMPDEST  # end_marker
    bytecode += Op.STOP

    return bytecode


# TODO: add a pointer to [empty, small, big, XEN] sized contracts
# See https://github.com/ethereum/execution-specs/issues/1755#issuecomment-3508963411
# for a way how I believe we can do this (using 7702 accounts with prefilled
# storage and then executing code on there, which we can change because its a 7702 account)
@pytest.mark.valid_from("Prague")
@pytest.mark.stateful  # Mark as stateful instead of benchmark
@pytest.mark.parametrize("num_slots", [1, 10, 50, 100, 200])
@pytest.mark.parametrize("warm_slots", [False, True])
@pytest.mark.parametrize("storage_keys_set", [False, True])
# NOTE: the 0 incrementer will thus SLOAD the same slot again
@pytest.mark.parametrize("incrementer", [0, 1])
def test_storage_sload_benchmark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    warm_slots: bool,
    storage_keys_set: bool,
    num_slots: int,
    incrementer: int,
) -> None:
    """ 
        TODO: write docs.
    """
    sender = pre.fund_eoa()

    initial_storage = Storage()
    slots: set[int] = set()
    if storage_keys_set:
        key = 0
        for i in range(num_slots):
            initial_storage[key] = 1
            slots.add(key)
            key += incrementer

    storage_contract = pre.deploy_contract(
        code=create_sload_contract(),
        storage=initial_storage,
    )

    calldata = incrementer.to_bytes(32, "big") + num_slots.to_bytes(32, "big")

    access_lists: List[AccessList] = []

    if warm_slots:
        access_lists = [
            AccessList(
                address=storage_contract,
                storage_keys=list(slots),
            ),
        ]

    # Create transaction to call the contract
    # Use a reasonable gas limit that covers the operation
    gas_limit = 21000 + 10000 + (num_slots * 50000)

    tx = Transaction(
        to=storage_contract,
        gas_limit=gas_limit,
        access_list=access_lists,
        data=calldata,
        sender=sender,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
    )