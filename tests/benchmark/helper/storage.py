"""Storage initialization helpers for stateful benchmarks."""

from dataclasses import dataclass
from functools import partial

from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    RecipientType,
    Transaction,
)
from execution_testing.base_types.base_types import Number

from .transactions import pack_transactions_into_blocks

# keccak256("random") for non-existing slots, masked as address,
# Solidity does input checks on the size and throws if we input
# something different than an address
START_SLOT = (
    0xA4896A3F93BF4BF58378E579F3CF193BB4AF1022AF7D2089F37D8BAE7157B85F
    % (2**160)
)


def create_sstore_initializer(init_val: int) -> IteratingBytecode:
    """
    Create a contract that initializes storage slots from calldata.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] slot count (num)

    storage[i] = init_val for i in [index, index + num).
    """
    # Setup: [index, index + num]
    prefix = (
        Op.CALLDATALOAD(0)  # [index]
        + Op.DUP1  # [index, index]
        + Op.CALLDATALOAD(32)  # [index, index, num]
        + Op.ADD  # [index, index + num]
    )

    # Loop: decrement counter and store at current position
    # Stack after subtraction: [index, current]
    # where current goes from index+num-1 down to index
    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [index, current, 1]
        + Op.SWAP1  # [index, 1, current]
        + Op.SUB  # [index, current - 1]
        + Op.SSTORE(  # STORAGE[current-1] = initial_value
            Op.DUP2,
            init_val,
            key_warm=False,
            # gas accounting
            original_value=0,
            current_value=0,
            new_value=init_val,
        )
        # After SSTORE: [index, current - 1]
        # Continue while current - 1 > index
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP2, Op.DUP2))
    )

    return IteratingBytecode(setup=prefix, iterating=loop)


def initializer_calldata_generator(
    iteration_count: int, start_iteration: int
) -> bytes:
    """Generate calldata for the storage initializer."""
    return Hash(start_iteration) + Hash(iteration_count)


def create_sequential_sstore_initializer() -> IteratingBytecode:
    """
    Create a contract that initializes storage with slot-dependent values.

    - CALLDATA[0..32]  start slot (index)
    - CALLDATA[32..64] slot count (num)
    - CALLDATA[64..96] value offset

    storage[i] = i + offset for i in [index, index + num).
    """
    # Setup: [offset, index, index + num]
    prefix = (
        Op.CALLDATALOAD(64)  # [offset]
        + Op.CALLDATALOAD(0)  # [index, offset]
        + Op.DUP1  # [index, index, offset]
        + Op.CALLDATALOAD(32)  # [num, index, index, offset]
        + Op.ADD  # [num + index, index, offset]
    )

    # Loop: decrement current and store slot-dependent value
    # Stack: [current, index, offset]
    # current goes from index+num down; stores at current-1
    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [1, current, index, offset]
        + Op.SWAP1  # [current, 1, index, offset]
        + Op.SUB  # [current-1, index, offset]
        + Op.DUP1  # [current-1, current-1, index, offset]
        + Op.DUP1  # [current-1, current-1, current-1, index, offset]
        + Op.DUP5  # [offset, current-1, current-1, current-1, index, offset]
        + Op.ADD  # [current-1 + offset, current-1, current-1, index, offset]
        + Op.SWAP1  # [current-1, current-1 + offset, current-1, index, offset]
        + Op.SSTORE(  # SSTORE(current-1, current-1 + offset)
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )
        # Stack: [current-1, index, offset]
        # Continue while current-1 > index
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP2, Op.DUP2))
    )

    return IteratingBytecode(setup=prefix, iterating=loop)


def sequential_initializer_calldata_generator(
    iteration_count: int,
    start_iteration: int,
    *,
    offset: int = 0,
) -> bytes:
    """Generate calldata for the sequential storage initializer."""
    return Hash(start_iteration) + Hash(iteration_count) + Hash(offset)


@dataclass(frozen=True)
class StorageInitRange:
    """One contiguous range of storage to initialize."""

    start_slot: int
    num_slots: int
    offset: int


def build_sequential_storage_init(
    *,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    block_gas_budget: int,
    authority: EOA,
    storage_init_ranges: list[StorageInitRange],
) -> list[Block]:
    """
    Build blocks that initialize storage with slot-dependent values.

    Deploy a sequential-SSTORE initializer, delegate *authority* to it,
    and emit transactions that write
    ``storage[i] = i + range.offset`` for every range.  The authority's
    nonce is incremented in-place.
    """
    initializer_code = create_sequential_sstore_initializer()
    initializer_addr = pre.deploy_contract(code=initializer_code)

    delegation_sender = pre.fund_eoa()
    auth_tx = Transaction(
        to=delegation_sender,
        gas_limit=tx_gas_limit,
        sender=delegation_sender,
        authorization_list=[
            AuthorizationTuple(
                address=initializer_addr,
                nonce=authority.nonce,
                signer=authority,
            ),
        ],
    )
    authority.nonce = Number(authority.nonce + 1)

    init_txs: list[Transaction] = []
    for r in storage_init_ranges:
        if r.num_slots == 0:
            continue
        calldata_gen = partial(
            sequential_initializer_calldata_generator,
            offset=r.offset,
        )
        # transactions_by_total_iteration_count splits the range across
        # transactions capped by the fork gas limit; no manual chunking needed.
        init_txs.extend(
            initializer_code.transactions_by_total_iteration_count(
                fork=fork,
                total_iterations=r.num_slots,
                sender=pre.fund_eoa(),
                to=authority,
                start_iteration=r.start_slot,
                calldata=calldata_gen,
                recipient_type=RecipientType.DELEGATION_7702,
            )
        )

    blocks: list[Block] = [Block(txs=[auth_tx])]
    blocks.extend(pack_transactions_into_blocks(init_txs, block_gas_budget))
    return blocks


def access_list_generator(
    iteration_count: int,
    start_iteration: int,
    access_warm: bool,
    authority: Address,
) -> list[AccessList] | None:
    """Access list generator for warming storage slots."""
    if access_warm:
        storage_keys = [
            Hash(i)
            for i in range(start_iteration, start_iteration + iteration_count)
        ]
        return [AccessList(address=authority, storage_keys=storage_keys)]
    return None


def executor_calldata_generator(
    iteration_count: int,
    start_iteration: int,
    write_value: int | None = None,
) -> bytes:
    """
    Calldata generator for executor operations.

    Generates: Hash(start) + Hash(start + count) [+ Hash(write_value)]
    """
    result = Hash(start_iteration) + Hash(start_iteration + iteration_count)
    if write_value is not None:
        result += Hash(write_value)
    return result
