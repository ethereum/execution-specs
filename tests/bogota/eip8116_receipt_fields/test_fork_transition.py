"""Pin receipt encoding across EIP-8116 activation."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    FixtureTransactionReceipt,
    Header,
    Transaction,
    TransactionReceipt,
    TransitionFork,
)
from execution_testing.base_types import Bloom
from execution_testing.vm import Op

from .spec import ref_spec_8116

REFERENCE_SPEC_GIT_PATH = ref_spec_8116.git_path
REFERENCE_SPEC_VERSION = ref_spec_8116.version


@pytest.mark.valid_at_transition_to("EIP8116")
@EIPChecklist.BlockHeaderField.Test.ForkTransition.Before()
@EIPChecklist.BlockHeaderField.Test.ForkTransition.After()
def test_receipt_encoding_at_activation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """Switch the receipt root at activation without changing gas charges."""
    target = pre.deploy_contract(code=Op.STOP)
    blocks = []
    for timestamp in (14_999, 15_000, 15_001):
        active_fork = fork.fork_at(timestamp=timestamp)
        gas = active_fork.transaction_intrinsic_cost_calculator()()
        txs = [
            Transaction(
                sender=pre.fund_eoa(),
                to=target,
                gas_limit=100_000,
                expected_receipt=TransactionReceipt(
                    gas_used=gas, cumulative_gas_used=(index + 1) * gas
                ),
            )
            for index in range(2)
        ]
        receipts = [
            FixtureTransactionReceipt(
                transaction_hash=tx.with_signature_and_sender().hash,
                ty=tx.ty,
                status=True,
                gas_used=gas if active_fork.is_eip_enabled(8116) else None,
                cumulative_gas_used=None
                if active_fork.is_eip_enabled(8116)
                else (index + 1) * gas,
                bloom=Bloom(0),
                logs=[],
            )
            for index, tx in enumerate(txs)
        ]
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=txs,
                header_verify=Header(
                    receipts_root=FixtureTransactionReceipt.list_root(
                        receipts
                    ),
                    gas_used=2 * gas,
                ),
            )
        )
    blockchain_test(pre=pre, post={}, blocks=blocks)
