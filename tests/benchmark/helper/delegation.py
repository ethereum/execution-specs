"""EIP-7702 delegation helpers for stateful benchmarks."""

from collections.abc import Callable

from execution_testing import (
    EOA,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    RecipientType,
    TestPhaseManager,
    Transaction,
)
from execution_testing.base_types.base_types import Number

from .enums import CacheStrategy
from .storage import START_SLOT
from .transactions import (
    build_cache_strategy_blocks,
    pack_transactions_into_blocks,
)


def build_delegated_storage_setup(
    *,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    needs_init: bool,
    num_target_slots: int,
    initializer_code: IteratingBytecode,
    initializer_addr: Address,
    executor_addr: Address,
    authority: EOA,
    authority_nonce: int,
    delegation_sender: EOA,
    initializer_calldata_generator: Callable[[int, int], bytes],
) -> list[Block]:
    """
    Build setup blocks for delegated storage benchmarks.

    Use EIP-7702 authorization to delegate an authority EOA first to
    a storage-initializer contract (if *needs_init*), then to the
    benchmark executor contract.  Return the list of setup blocks.
    """
    blocks: list[Block] = []

    if needs_init:
        # Block 1: Authorize to initializer
        blocks.append(
            Block(
                txs=[
                    Transaction(
                        to=delegation_sender,
                        gas_limit=tx_gas_limit,
                        sender=delegation_sender,
                        authorization_list=[
                            AuthorizationTuple(
                                address=initializer_addr,
                                nonce=authority_nonce,
                                signer=authority,
                            ),
                        ],
                    )
                ]
            )
        )
        authority_nonce += 1

        # transactions_by_total_iteration_count splits the slots across
        # transactions capped by the fork gas limit, so no manual chunking
        # is required.
        init_txs: list[Transaction] = list(
            initializer_code.transactions_by_total_iteration_count(
                fork=fork,
                total_iterations=num_target_slots,
                sender=pre.fund_eoa(),
                to=authority,
                start_iteration=1,
                calldata=initializer_calldata_generator,
                recipient_type=RecipientType.DELEGATION_7702,
            )
        )

        # Pack init transactions into blocks
        blocks.extend(pack_transactions_into_blocks(init_txs, tx_gas_limit))

    # Final block: Authorize to executor
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=delegation_sender,
                    gas_limit=tx_gas_limit,
                    sender=delegation_sender,
                    authorization_list=[
                        AuthorizationTuple(
                            address=executor_addr,
                            nonce=authority_nonce,
                            signer=authority,
                        ),
                    ],
                )
            ]
        )
    )

    return blocks


def delegate_with_calldata(
    pre: Alloc,
    fork: Fork,
    authority: EOA,
    address: Address,
    calldata: Hash,
) -> Transaction:
    """
    Create a tx that delegates the authority and calls it with calldata.

    The delegated code determines what happens with the calldata.
    The authority nonce is incremented in-place.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(calldata),
        authorization_list_or_count=1,
    )
    gas_limit = intrinsic_gas + 500_000
    tx = Transaction(
        gas_limit=gas_limit,
        to=authority,
        value=0,
        data=calldata,
        sender=pre.fund_eoa(),
        authorization_list=[
            AuthorizationTuple(
                chain_id=0,
                address=address,
                nonce=authority.nonce,
                signer=authority,
            ),
        ],
    )
    authority.nonce = Number(authority.nonce + 1)
    return tx


def run_bloated_eoa_benchmark(
    *,
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    authority: EOA,
    existing_slots: bool,
    runtime_code: Bytecode,
    cache_strategy: CacheStrategy,
    tx_generator: Callable[[EOA], list[Transaction]] | None = None,
) -> None:
    """
    Run a bloated-EOA benchmark with the given runtime delegation code.
    """
    slot_0_value = Hash(1) if existing_slots else Hash(START_SLOT)

    setter_address = pre.deploy_contract(code=Op.SSTORE(0, Op.CALLDATALOAD(0)))
    runtime_address = pre.deploy_contract(code=runtime_code)

    with TestPhaseManager.setup():
        init_tx = delegate_with_calldata(
            pre,
            fork,
            authority,
            setter_address,
            slot_0_value,
        )
        runtime_tx = delegate_with_calldata(
            pre,
            fork,
            authority,
            runtime_address,
            Hash(0),
        )

    blocks: list[Block] = [Block(txs=[init_tx, runtime_tx])]

    sender = pre.fund_eoa()

    txs: list[Transaction] = []
    with TestPhaseManager.execution():
        if tx_generator is not None:
            txs = tx_generator(sender)
        else:
            gas_available = gas_benchmark_value
            intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
            while gas_available >= intrinsic_gas:
                tx_gas = min(gas_available, tx_gas_limit)
                txs.append(
                    Transaction(
                        gas_limit=tx_gas,
                        to=authority,
                        sender=sender,
                    )
                )
                gas_available -= tx_gas

    cache_txs: list[Transaction] = []
    if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
        with TestPhaseManager.setup():
            cache_sender = pre.fund_eoa()
            for tx in txs:
                cache_txs.append(
                    Transaction(
                        gas_limit=tx.gas_limit,
                        data=tx.data,
                        to=authority,
                        sender=cache_sender,
                    )
                )

    blocks += build_cache_strategy_blocks(cache_strategy, txs, cache_txs)

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )
