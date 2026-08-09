"""
Fork-transition tests for
[EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
    Initcode,
    Op,
    Transaction,
    compute_create2_address,
)
from execution_testing.test_types.block_access_list.account_changes import (
    BalNonceChange,
)
from execution_testing.test_types.block_access_list.expectations import (
    BalAccountExpectation,
    BlockAccessListExpectation,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

FORK_TIMESTAMP = 15_000


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("pre_fork_nonce", [1, 2, 32])
def test_factory_deploys_across_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_fork_nonce: int,
) -> None:
    """
    A pre-existing factory keeps deploying contracts across the Amsterdam
    transition, with its nonce accruing normally.

    Asserting that final nonce is what catches the glamsterdam-devnet-6 bug: a
    client that re-injects EIP-7997 at the transition resets the already-used
    factory back to nonce 1, diverging the post-state root. Deployment success
    alone cannot catch it, since the `CREATE2` address does not depend on the
    factory nonce.
    """
    factory = pre.deploy_contract(
        code=Spec.FACTORY_BYTECODE,
        address=Address(Spec.FACTORY_ADDRESS),
        nonce=pre_fork_nonce,
    )
    sender = pre.fund_eoa()

    runtime_code = Op.RETURN(0, 1)
    initcode = Initcode(deploy_code=runtime_code)

    timestamps = [FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1]

    blocks = []
    deployed = {}
    for i, timestamp in enumerate(timestamps):
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        sender=sender,
                        to=factory,
                        data=Hash(timestamp) + bytes(initcode),
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1,
                                    post_nonce=pre_fork_nonce + i + 1,
                                )
                            ],
                        ),
                    }
                ),
            )
        )
        deployed[compute_create2_address(factory, timestamp, initcode)] = (
            Account(nonce=1, code=bytes(runtime_code))
        )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            **deployed,
            factory: Account(
                nonce=pre_fork_nonce + len(timestamps),
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
def test_factory_absent_across_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A chain that never deployed the factory transitions to Amsterdam
    through valid blocks, and the factory address stays nonexistent.

    The client MUST NOT check for the existence of the contract at
    the fork boundary. Therefore, we verify that the BAL does
    not contain the factory account read.
    The block itself is valid. It is the responsibility of the
    chain activating EIP-7997 to ensure the factory is valid
    at the start of the fork block.
    """
    factory = Address(Spec.FACTORY_ADDRESS)
    # Merging an all-zero account into the fork's pre-allocation removes
    # the factory predeploy from the genesis allocation entirely.
    pre[factory] = Account(nonce=0, balance=0, code=b"")

    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)
    transfer_value = 1

    timestamps = [FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1]

    blocks = []
    for i, timestamp in enumerate(timestamps):
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        sender=sender,
                        to=receiver,
                        value=transfer_value,
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: None,
                        sender: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1,
                                    post_nonce=i + 1,
                                )
                            ],
                        ),
                    }
                )
                if timestamp >= FORK_TIMESTAMP
                else None,
            )
        )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            factory: Account.NONEXISTENT,
            receiver: Account(balance=len(timestamps) * transfer_value),
        },
    )
