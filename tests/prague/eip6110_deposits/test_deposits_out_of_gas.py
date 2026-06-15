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
    Header,
    Requests,
)
from execution_testing.base_types import HexNumber

from .helpers import DepositContract, DepositRequest, DepositTransaction
from .spec import ref_spec_6110

REFERENCE_SPEC_GIT_PATH = ref_spec_6110.git_path
REFERENCE_SPEC_VERSION = ref_spec_6110.version

pytestmark = pytest.mark.valid_from("Prague")


@pytest.mark.parametrize(
    "requests",
    [
        pytest.param(
            [
                DepositTransaction(
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
                DepositTransaction(
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
                DepositContract(
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
                DepositContract(
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
) -> None:
    """
    Test that a relay-contract transaction with an insufficient gas limit runs
    out of gas, so none of the deposit requests it would trigger are included.

    The transaction gas limit is applied directly to the prepared transaction
    rather than through the request helper, keeping the gas concern isolated to
    this dedicated test.
    """
    deposit_contract = DepositContract(
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

    # A 10M gas limit is insufficient to process all 450 deposits, so the
    # transaction runs out of gas and emits no deposit requests.
    txs = deposit_contract.transactions()
    txs[0].gas_limit = HexNumber(10_000_000)

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
