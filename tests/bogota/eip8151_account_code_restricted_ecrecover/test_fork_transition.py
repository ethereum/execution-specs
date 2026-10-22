"""
Tests for the activation of
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

Before the fork, ecrecover returns any signer for the base fee alone and
reads no account. From the fork on, a recovery pays for the account access
and the code read, records the signer in the block access list, and
withholds a signer whose code is not a delegation designation.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Op,
    Storage,
    Transaction,
)

from .helpers import (
    INPUT_SIZE,
    OUTPUT_OFFSET,
    SENTINEL,
    fund_signer,
    recover,
    signed_input,
)
from .spec import ref_spec_8151

REFERENCE_SPEC_GIT_PATH = ref_spec_8151.git_path
REFERENCE_SPEC_VERSION = ref_spec_8151.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8151")

FORK_TIMESTAMP = 15_000


@pytest.mark.parametrize(
    "signer_has_code",
    [
        pytest.param(False, id="balance-only"),
        pytest.param(True, id="contract", marks=pytest.mark.pre_alloc_mutable),
    ],
)
def test_ecrecover_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    signer_has_code: bool,
) -> None:
    """
    Test that the account access, the code check and the block access list
    read start exactly at the fork.
    """
    signer = fund_signer(pre, has_code=signer_has_code)
    sender = pre.fund_eoa()

    blocks: list[Block] = []
    post: dict[Address, Account] = {}
    for timestamp in (FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1):
        block_fork = fork.fork_at(timestamp=timestamp)
        activated = timestamp >= FORK_TIMESTAMP
        if activated and signer_has_code:
            output_word = SENTINEL
        else:
            output_word = int.from_bytes(signer)

        # The base fee alone recovers the signer only before the fork.
        storage = Storage()
        caller = pre.deploy_contract(
            Op.CALLDATACOPY(0, 0, INPUT_SIZE)
            + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
            + Op.SSTORE(
                storage.store_next(int(not activated), "base_fee_call"),
                recover(
                    gas=block_fork.ecrecover_gas(
                        recovered=False, address_warm=False
                    )
                ),
            )
            + Op.SSTORE(
                storage.store_next(1, "cold_call"),
                recover(
                    gas=block_fork.ecrecover_gas(
                        recovered=True, address_warm=False
                    )
                ),
            )
            + Op.SSTORE(
                storage.store_next(output_word, "output"),
                Op.MLOAD(OUTPUT_OFFSET),
            ),
            storage=storage.canary(),
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        to=caller, data=signed_input(signer), sender=sender
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        signer: (
                            BalAccountExpectation.empty()
                            if activated
                            else None
                        )
                    }
                ),
            )
        )
        post[caller] = Account(storage=storage)

    blockchain_test(pre=pre, blocks=blocks, post=post)
