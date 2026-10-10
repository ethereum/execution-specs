"""
Tests [EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).

Test that `BLOCKHASH` of an in-window block adds the `SLOAD` cost of its
history slot.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    Transaction,
)

from .helpers import history_staticcall
from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_from("EIP7709")


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


@pytest.mark.slow()
def test_blockhash_too_old_but_available_in_history_charges_base_only(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a BLOCKHASH query older than 256 blocks charges only the
    base opcode cost, even when EIP-2935 still serves the hash.
    """
    measured = Op.BLOCKHASH(1, in_window=False)
    code = CodeGasMeasure(code=measured, extra_stack_items=1)

    contract_address = pre.deploy_contract(
        code,
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    blocks = [Block() for _ in range(Spec.BLOCKHASH_SERVE_WINDOW + 1)]
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=contract_address,
                    gas_limit=1_000_000,
                    sender=sender,
                )
            ]
        )
    )

    post: Dict[Address, Account] = {
        contract_address: Account(storage={0: measured.gas_cost(fork)}),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
