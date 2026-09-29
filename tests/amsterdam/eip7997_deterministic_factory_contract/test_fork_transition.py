"""
Verify fork transitions for the Deterministic Factory Contract.

<https://eips.ethereum.org/EIPS/eip-7997>
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    EIPChecklist,
    Hash,
    Initcode,
    Op,
    Transaction,
    compute_create2_address,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

FORK_TIMESTAMP = 15_000


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("pre_fork_nonce", [1, 2, 32])
@EIPChecklist.SystemContract.Test.ForkTransition.CallBeforeFork()
def test_factory_deploys_across_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_fork_nonce: int,
) -> None:
    """
    Preserve normal deployment and nonce increments across the transition.

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
        balance=1,
        storage={0: 1},
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
                balance=1,
                storage={0: 1},
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "factory_pre_state",
    [
        pytest.param("absent", id="factory_absent"),
        pytest.param("foreign_code", id="factory_foreign_code"),
    ],
)
@EIPChecklist.SystemContract.Test.Deployment.Missing()
def test_factory_untouched_across_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    factory_pre_state: str,
) -> None:
    """
    Leave an absent or foreign factory account untouched at the transition.

    The client MUST NOT check for the contract at the fork boundary, so the
    block access list of the fork block and the one after it must not even
    contain a read of the factory account. Installing the canonical code
    over a missing or foreign account is a consensus split. Ensuring the
    account is valid is the job of the chain activating EIP-7997.
    """
    factory = Address(Spec.FACTORY_ADDRESS)
    if factory_pre_state == "absent":
        # Merging an all-zero account into the fork's pre-allocation removes
        # the factory contract from the genesis allocation entirely.
        pre[factory] = Account(nonce=0, balance=0, code=b"")
        factory_post = Account.NONEXISTENT
    elif factory_pre_state == "foreign_code":
        foreign_code = Op.SSTORE(0, 1) + Op.STOP
        pre.deploy_contract(
            code=foreign_code,
            address=factory,
            nonce=7,
            balance=1,
            storage={0: 1},
        )
        factory_post = Account(
            nonce=7, balance=1, code=foreign_code, storage={0: 1}
        )
    else:
        raise ValueError(factory_pre_state)

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
            factory: factory_post,
            receiver: Account(balance=len(timestamps) * transfer_value),
        },
    )
