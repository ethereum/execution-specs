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
    BalCodeChange,
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
def test_factory_installed_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A chain without the factory installs it on the Amsterdam activation
    block, recording the nonce and code changes in that block's access
    list at the pre-execution index. Later blocks do not touch the
    account, and the installed factory is immediately usable.
    """
    factory = Address(Spec.FACTORY_ADDRESS)
    # Zero out the injected predeploy; the genesis allocation merge
    # drops the resulting empty account entirely.
    pre[factory] = Account(nonce=0, balance=0, code=b"")
    sender = pre.fund_eoa()

    runtime_code = Op.RETURN(0, 1)
    initcode = Initcode(deploy_code=runtime_code)
    salt = Hash(0)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(
                timestamp=FORK_TIMESTAMP,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=0, post_nonce=1
                                )
                            ],
                            code_changes=[
                                BalCodeChange(
                                    block_access_index=0,
                                    new_code=Spec.FACTORY_BYTECODE,
                                )
                            ],
                        ),
                    }
                ),
            ),
            Block(
                timestamp=FORK_TIMESTAMP + 1,
                txs=[
                    Transaction(
                        sender=sender,
                        to=factory,
                        data=salt + bytes(initcode),
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=2
                                )
                            ],
                            code_changes=[],
                        ),
                    }
                ),
            ),
        ],
        post={
            factory: Account(nonce=2, code=Spec.FACTORY_BYTECODE),
            compute_create2_address(factory, salt, initcode): Account(
                nonce=1, code=bytes(runtime_code)
            ),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("factory_nonce", [1, 5])
def test_factory_access_recorded_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    factory_nonce: int,
) -> None:
    """
    An already-deployed factory is left untouched by the activation
    block, which records only the access: the account appears in the
    activation block's access list with no changes, and not at all in
    later blocks' access lists.
    """
    factory = pre.deploy_contract(
        code=Spec.FACTORY_BYTECODE,
        address=Address(Spec.FACTORY_ADDRESS),
        nonce=factory_nonce,
    )
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=receiver, value=1)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: BalAccountExpectation.empty(),
                    }
                ),
            ),
            Block(
                timestamp=FORK_TIMESTAMP + 1,
                txs=[Transaction(sender=sender, to=receiver, value=1)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: None,
                    }
                ),
            ),
        ],
        post={
            factory: Account(
                nonce=factory_nonce, code=Spec.FACTORY_BYTECODE
            ),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "factory_nonce,post_nonce,expected_nonce_changes",
    [
        pytest.param(
            0,
            1,
            [BalNonceChange(block_access_index=0, post_nonce=1)],
            id="zero_nonce_set_to_one",
        ),
        pytest.param(7, 7, [], id="nonzero_nonce_preserved"),
    ],
)
def test_factory_code_reset_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    factory_nonce: int,
    post_nonce: int,
    expected_nonce_changes: list,
) -> None:
    """
    A factory account holding non-canonical code is reset to the
    canonical runtime code on the activation block. A zero nonce is set
    to one, a nonzero nonce and the balance are preserved, and only the
    resulting changes appear in the access list.
    """
    factory = pre.deploy_contract(
        code=Op.STOP,
        address=Address(Spec.FACTORY_ADDRESS),
        nonce=factory_nonce,
        balance=1000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(
                timestamp=FORK_TIMESTAMP,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: BalAccountExpectation(
                            nonce_changes=expected_nonce_changes,
                            code_changes=[
                                BalCodeChange(
                                    block_access_index=0,
                                    new_code=Spec.FACTORY_BYTECODE,
                                )
                            ],
                        ),
                    }
                ),
            ),
        ],
        post={
            factory: Account(
                nonce=post_nonce,
                code=Spec.FACTORY_BYTECODE,
                balance=1000,
            ),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
def test_factory_install_merged_with_same_block_use(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    The factory is installed and used within the activation block. The
    install and the transaction-driven use merge into a single access
    list entry: the code change at the pre-execution index and nonce
    changes at both indices.
    """
    factory = Address(Spec.FACTORY_ADDRESS)
    # Zero out the injected predeploy; the genesis allocation merge
    # drops the resulting empty account entirely.
    pre[factory] = Account(nonce=0, balance=0, code=b"")
    sender = pre.fund_eoa()

    runtime_code = Op.RETURN(0, 1)
    initcode = Initcode(deploy_code=runtime_code)
    salt = Hash(0)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[
                    Transaction(
                        sender=sender,
                        to=factory,
                        data=salt + bytes(initcode),
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        factory: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=0, post_nonce=1
                                ),
                                BalNonceChange(
                                    block_access_index=1, post_nonce=2
                                ),
                            ],
                            code_changes=[
                                BalCodeChange(
                                    block_access_index=0,
                                    new_code=Spec.FACTORY_BYTECODE,
                                )
                            ],
                        ),
                    }
                ),
            ),
        ],
        post={
            factory: Account(nonce=2, code=Spec.FACTORY_BYTECODE),
            compute_create2_address(factory, salt, initcode): Account(
                nonce=1, code=bytes(runtime_code)
            ),
        },
    )
