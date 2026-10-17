"""Test individual gas commitments and receipt-local log indices."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    EIPChecklist,
    FixtureTransactionReceipt,
    Fork,
    GasConsumer,
    Header,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    add_kzg_version,
)
from execution_testing.base_types import Bloom, EmptyTrieRoot
from execution_testing.vm import Op

from .spec import ref_spec_8116

REFERENCE_SPEC_GIT_PATH = ref_spec_8116.git_path
REFERENCE_SPEC_VERSION = ref_spec_8116.version


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.with_all_tx_types
@pytest.mark.parametrize(
    "outcome", ["success", "revert", "refund", "state_creation", "oog"]
)
@pytest.mark.parametrize(
    "invalid_root",
    [
        pytest.param(
            False,
            marks=EIPChecklist.BlockHeaderField.Test.ValueBehavior.Accept(),
        ),
        pytest.param(
            True,
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.BlockHeaderField.Test.ValueBehavior.Reject(),
            ],
        ),
    ],
)
def test_receipt_gas_commitment(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    outcome: str,
    invalid_root: bool,
) -> None:
    """Commit each transaction's post-refund gas after activation."""
    blocks = []
    post: dict[Address, Account] = {}
    for _ in range(2):
        if outcome == "success":
            code: Bytecode = Op.STOP
        elif outcome == "revert":
            code = Op.REVERT(0, 0)
        elif outcome == "refund":
            code = Op.SSTORE(0, 0, original_value=1, new_value=0) + Op.STOP
        elif outcome == "state_creation":
            code = Op.SSTORE(0, 1, original_value=0, new_value=1) + Op.STOP
        elif outcome == "oog":
            code = GasConsumer.out_of_gas(fork)
        else:
            raise ValueError(outcome)

        target = pre.deploy_contract(
            code=code, storage={0: 1} if outcome == "refund" else {}
        )
        stop = pre.deploy_contract(code=Op.STOP)
        authorizations = None
        if tx_type == 4:
            authority = pre.fund_eoa()
            authorizations = [
                AuthorizationTuple(
                    signer=authority, address=0, writes_delegation=False
                )
            ]
            post[authority] = Account(nonce=1)

        intrinsic = fork.transaction_intrinsic_cost_calculator()
        execution_gas = (
            intrinsic(
                authorization_list_or_count=authorizations,
                return_cost_deducted_prior_execution=True,
            )
            + fork.transaction_top_frame_execution_gas(
                authorizations=authorizations or ()
            )
            + (code.execution_cost(fork) if outcome != "oog" else 0)
        )
        state_gas = fork.transaction_top_frame_state_gas(
            authorizations=authorizations or ()
        ) + (code.state_cost(fork) if outcome != "oog" else 0)
        before_refund = execution_gas + state_gas
        if outcome == "oog":
            gas_used = before_refund = execution_gas = 100_000
        else:
            refund = min(
                code.refund(fork), before_refund // fork.max_refund_quotient()
            )
            gas_used = max(
                before_refund - refund,
                fork.transaction_data_floor_cost_calculator()(data=b""),
            )
            if outcome == "refund":
                assert gas_used < before_refund

        first = Transaction(
            ty=tx_type,
            sender=pre.fund_eoa(),
            to=target,
            gas_limit=max(100_000, before_refund + 1)
            if outcome != "oog"
            else 100_000,
            state_gas_reservoir=state_gas,
            authorization_list=authorizations,
            blob_versioned_hashes=add_kzg_version([1], 1)
            if tx_type == 3
            else None,
            max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas()
            if tx_type == 3
            else None,
            expected_receipt=TransactionReceipt(
                gas_used=gas_used, status=outcome not in ("revert", "oog")
            ),
        )
        trailing_gas = intrinsic(calldata=b"\x00")
        trailing = Transaction(
            sender=pre.fund_eoa(),
            to=stop,
            gas_limit=100_000,
            data=b"\x00",
            expected_receipt=TransactionReceipt(
                gas_used=trailing_gas,
                cumulative_gas_used=gas_used + trailing_gas,
            ),
        )
        receipts = []
        cumulative = 0
        for tx, used, status in (
            (first, gas_used, outcome not in ("revert", "oog")),
            (trailing, trailing_gas, True),
        ):
            cumulative += used
            receipts.append(
                FixtureTransactionReceipt(
                    transaction_hash=tx.with_signature_and_sender().hash,
                    ty=tx.ty,
                    gas_used=used if fork.is_eip_enabled(8116) else None,
                    cumulative_gas_used=None
                    if fork.is_eip_enabled(8116)
                    else cumulative,
                    status=status,
                    bloom=Bloom(0),
                    logs=[],
                )
            )
        wrong_receipts = (
            [
                receipt.model_copy(
                    update={
                        "gas_used": None
                        if fork.is_eip_enabled(8116)
                        else used,
                        "cumulative_gas_used": cumulative_used
                        if fork.is_eip_enabled(8116)
                        else None,
                    }
                )
                for receipt, used, cumulative_used in (
                    (receipts[0], gas_used, gas_used),
                    (receipts[1], trailing_gas, gas_used + trailing_gas),
                )
            ]
            if invalid_root
            else []
        )
        blocks.append(
            Block(
                txs=[first, trailing],
                header_verify=Header(
                    receipts_root=FixtureTransactionReceipt.list_root(
                        receipts
                    ),
                    gas_used=max(execution_gas + trailing_gas, state_gas),
                ),
                rlp_modifier=Header(
                    receipts_root=FixtureTransactionReceipt.list_root(
                        wrong_receipts
                    )
                )
                if invalid_root
                else None,
                exception=BlockException.INVALID_RECEIPTS_ROOT
                if invalid_root
                else None,
            )
        )
        post[target] = Account(
            storage={0: 1} if outcome == "state_creation" else {}
        )
    blockchain_test(pre=pre, post={} if invalid_root else post, blocks=blocks)


@pytest.mark.valid_from("Amsterdam")
def test_log_indices(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Restart log indices per receipt, excluding reverted logs."""
    logger = pre.deploy_contract(code=Op.LOG0(0, 0) + Op.LOG0(0, 0))
    reverter = pre.deploy_contract(code=Op.LOG0(0, 0) + Op.REVERT(0, 0))
    stop = pre.deploy_contract(code=Op.STOP)
    blocks = []
    for _ in range(2):
        txs = []
        for address, count, status in (
            (logger, 2, 1),
            (reverter, 0, 0),
            (stop, 0, 1),
            (logger, 2, 1),
        ):
            txs.append(
                Transaction(
                    sender=pre.fund_eoa(),
                    to=address,
                    expected_receipt=TransactionReceipt(
                        status=status,
                        logs=[
                            TransactionLog(
                                address=address,
                                topics=[],
                                data=b"",
                                log_index=index
                                if fork.is_eip_enabled(8116)
                                else None,
                            )
                            for index in range(count)
                        ],
                    ),
                )
            )
        blocks.append(Block(txs=txs))
    blockchain_test(pre=pre, post={}, blocks=blocks)


@pytest.mark.valid_from("Amsterdam")
def test_empty_receipt_trie(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """Keep empty blocks' receipt roots and gas accounting unchanged."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                header_verify=Header(receipts_root=EmptyTrieRoot, gas_used=0)
            )
        ],
    )
