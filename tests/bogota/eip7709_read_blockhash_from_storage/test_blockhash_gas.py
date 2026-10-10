"""
Tests [EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).

Test that `BLOCKHASH` of an in-window block adds the `SLOAD` cost of its
history slot.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    EIPChecklist,
    Fork,
    Op,
    Storage,
    Transaction,
)

from .helpers import history_staticcall
from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_from("EIP7709")


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "empty_blocks,warm_up,measured",
    [
        pytest.param(1, Bytecode(), Op.BLOCKHASH(0), id="cold"),
        pytest.param(
            1,
            Op.POP(Op.BLOCKHASH(0)),
            Op.BLOCKHASH(0, key_warm=True),
            id="repeat_is_warm",
        ),
        pytest.param(
            1,
            Op.POP(history_staticcall(1)),
            Op.BLOCKHASH(1, key_warm=True),
            id="history_call_warms",
        ),
        pytest.param(
            2,
            Op.POP(Op.BLOCKHASH(0)),
            Op.BLOCKHASH(1),
            id="other_slot_stays_cold",
        ),
        pytest.param(
            0,
            Bytecode(),
            Op.BLOCKHASH(0xFFFFFF, in_window=False),
            id="future_block",
        ),
        pytest.param(
            1,
            # Aliases block 1's slot but lies in the future.
            Op.POP(Op.BLOCKHASH(1 + Spec.HISTORY_SERVE_WINDOW)),
            Op.BLOCKHASH(1),
            id="aliased_future_block_does_not_warm",
        ),
    ],
)
def test_blockhash_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    empty_blocks: int,
    warm_up: Bytecode,
    measured: Bytecode,
) -> None:
    """
    Test that `BLOCKHASH` adds the cold or warm `SLOAD` cost of its
    history slot, and only for blocks inside the serve window.
    """
    contract = pre.deploy_contract(
        warm_up + CodeGasMeasure(code=measured, extra_stack_items=1),
        storage={0: 0xDEADBEEF},
    )
    blocks = [Block() for _ in range(empty_blocks)]
    blocks.append(Block(txs=[Transaction(to=contract, sender=pre.fund_eoa())]))
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage={0: measured.gas_cost(fork)})},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "first_read,key_warm",
    [
        pytest.param("access_list", True, id="access_list"),
        pytest.param("successful_call", True, id="successful_call"),
        pytest.param("reverted_call", False, id="reverted_call"),
        pytest.param("earlier_transaction", False, id="earlier_transaction"),
    ],
)
def test_blockhash_warmth_scope(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    first_read: str,
    key_warm: bool,
) -> None:
    """
    Test that the history slot's warmth follows the transaction's accessed
    storage keys: the access list adds to them, a reverted call's additions
    are dropped, and each transaction starts afresh.
    """
    query_block = 0
    reader_code = Op.POP(Op.BLOCKHASH(query_block))

    warm_up = Bytecode()
    access_list: list[AccessList] | None = None
    txs: list[Transaction] = []
    if first_read == "access_list":
        access_list = [
            AccessList(
                address=Address(Spec.HISTORY_STORAGE_ADDRESS),
                storage_keys=[query_block % Spec.HISTORY_SERVE_WINDOW],
            )
        ]
    elif first_read == "successful_call":
        reader = pre.deploy_contract(reader_code)
        warm_up = Op.POP(Op.CALL(address=reader))
    elif first_read == "reverted_call":
        reader = pre.deploy_contract(reader_code + Op.REVERT(0, 0))
        warm_up = Op.POP(Op.CALL(address=reader))
    elif first_read == "earlier_transaction":
        reader = pre.deploy_contract(reader_code)
        txs.append(Transaction(to=reader, sender=pre.fund_eoa()))
    else:
        raise ValueError(f"Unknown first read: {first_read}")

    measured = Op.BLOCKHASH(query_block, key_warm=key_warm)
    contract = pre.deploy_contract(
        warm_up + CodeGasMeasure(code=measured, extra_stack_items=1),
        storage={0: 0xDEADBEEF},
    )
    txs.append(
        Transaction(
            to=contract, sender=pre.fund_eoa(), access_list=access_list
        )
    )
    blockchain_test(
        pre=pre,
        blocks=[Block(), Block(txs=txs)],
        post={contract: Account(storage={0: measured.gas_cost(fork)})},
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "sufficient_gas", [True, False], ids=["exact_gas", "one_gas_short"]
)
def test_blockhash_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficient_gas: bool,
) -> None:
    """
    Test that `BLOCKHASH` runs out of gas one short of its cold cost, and
    does so before it reads the history slot.
    """
    query_block = 0
    reader_code = Op.BLOCKHASH(query_block)
    reader = pre.deploy_contract(reader_code)
    reader_gas = reader_code.gas_cost(fork)
    if not sufficient_gas:
        reader_gas -= 1

    storage = Storage()
    caller = pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(1 if sufficient_gas else 0),
            Op.CALL(gas=reader_gas, address=reader),
        ),
        storage=storage.canary(),
    )

    # A failed frame's reads still reach the block access list, so the
    # starved read is absent only because the charge comes first.
    history_reads = (
        [query_block % Spec.HISTORY_SERVE_WINDOW] if sufficient_gas else []
    )
    history_contract = Address(Spec.HISTORY_STORAGE_ADDRESS)
    blockchain_test(
        pre=pre,
        blocks=[
            # Makes block 0 older than the parent: the system call writes
            # only the parent's slot, and a written slot hides a read.
            Block(),
            Block(
                txs=[Transaction(to=caller, sender=pre.fund_eoa())],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        history_contract: BalAccountExpectation(
                            storage_reads=history_reads
                        ),
                    }
                ),
            ),
        ],
        post={caller: Account(storage=storage)},
    )
