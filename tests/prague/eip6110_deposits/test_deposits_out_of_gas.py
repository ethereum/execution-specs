"""
Out-of-gas deposit tests.

Tests that deposit requests whose triggering call runs out of gas are not
included in the block, for
[EIP-6110: Supply validator deposits on chain](https://eips.ethereum.org/EIPS/eip-6110).

The gas limits are supplied via the interaction helpers (per-request
`gas_limits` or directly on the prepared transaction) rather than being baked
into the deposit request descriptor, keeping the gas concern isolated to these
dedicated tests.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    DepositRequest,
    Fork,
    Header,
    Requests,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
)
from execution_testing.base_types import HexNumber

from .spec import ref_spec_6110

REFERENCE_SPEC_GIT_PATH = ref_spec_6110.git_path
REFERENCE_SPEC_VERSION = ref_spec_6110.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "requests",
    [
        pytest.param(
            [
                SystemContractInteractionTransaction(
                    requests=[
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=32_000_000_000,
                            signature=0x03,
                            index=0x0,
                            valid=False,
                        ),
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=32_000_000_000,
                            signature=0x03,
                            index=0x0,
                        ),
                    ],
                    # From traces, gas used by the first tx is 82,718
                    # so reduce by one here
                    gas_limits=[0x1431D, None],
                ),
            ],
            id="multiple_deposit_from_same_eoa_first_oog",
        ),
        pytest.param(
            [
                SystemContractInteractionTransaction(
                    requests=[
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=32_000_000_000,
                            signature=0x03,
                            index=0x0,
                        ),
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=32_000_000_000,
                            signature=0x03,
                            index=0x0,
                            valid=False,
                        ),
                    ],
                    # From traces, gas used by the second tx is 68,594,
                    # reduce by one here
                    gas_limits=[None, 0x10BF1],
                ),
            ],
            id="multiple_deposit_from_same_eoa_last_oog",
        ),
        pytest.param(
            [
                SystemContractInteractionContract(
                    requests=[
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=1_000_000_000,
                            signature=0x03,
                            index=0x0,
                            valid=False,
                        ),
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=1_000_000_000,
                            signature=0x03,
                            index=0x0,
                        ),
                    ],
                    # Starve the first inner call of gas
                    gas_limits=[100, None],
                ),
            ],
            id="multiple_deposits_from_contract_first_oog",
        ),
        pytest.param(
            [
                SystemContractInteractionContract(
                    requests=[
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=1_000_000_000,
                            signature=0x03,
                            index=0x0,
                        ),
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=1_000_000_000,
                            signature=0x03,
                            index=0x0,
                            valid=False,
                        ),
                    ],
                    # Starve the last inner call of gas
                    gas_limits=[None, 100],
                ),
            ],
            id="multiple_deposits_from_contract_last_oog",
        ),
    ],
)
@pytest.mark.slow()
def test_deposit_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """
    Test that a deposit request whose triggering call runs out of gas is not
    included, while the other requests in the block are.

    The gas limits are supplied per-request via the interaction's `gas_limits`
    list rather than being baked into the deposit request descriptor, keeping
    the gas concern isolated to these dedicated tests.
    """
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
    )


@pytest.mark.slow()
def test_deposit_from_contract_transaction_out_of_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a relay-contract transaction with an insufficient gas limit runs
    out of gas, so none of the deposit requests it would trigger are included.

    The transaction gas limit is applied directly to the prepared transaction
    rather than through the request helper, keeping the gas concern isolated to
    this dedicated test.
    """
    deposit_contract = SystemContractInteractionContract(
        requests=[
            DepositRequest(
                pubkey=0x01,
                withdrawal_credentials=0x02,
                amount=1_000_000_000,
                signature=0x03,
                index=i,
                valid=False,
            )
            for i in range(450)
        ],
    ).update_pre(pre)

    # A 10M gas limit is far too little to process all 450 deposits, so the
    # transaction runs out of gas and emits no deposit requests. The limit is
    # raised to the fork's calldata floor when that is higher (EIP-7623 /
    # EIP-7976), so the transaction stays valid rather than being rejected for
    # being below the floor; even then it is nowhere near enough to execute.
    txs = deposit_contract.transactions()
    floor_cost = fork.transaction_data_floor_cost_calculator()
    txs[0].gas_limit = HexNumber(
        max(10_000_000, floor_cost(data=txs[0].data) + 1)
    )

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(requests_hash=Requests()),
            )
        ],
    )
