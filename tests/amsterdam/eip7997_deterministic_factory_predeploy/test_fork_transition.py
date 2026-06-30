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
    Transaction,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

FORK_TIMESTAMP = 15_000


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("pre_fork_nonce", [1, 2, 32])
def test_existing_factory_preserved_across_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    pre_fork_nonce: int,
) -> None:
    """
    A factory already present at `FACTORY_ADDRESS` must be left untouched by
    the Amsterdam transition.

    EIP-7997 requires the chain state to include the factory with nonce 1 and
    the canonical runtime code, but its Backwards Compatibility section states
    that on chains which already have the factory, satisfying the requirement
    is a no-op. A client that re-applies the requirement at the transition -
    resetting the nonce of an already-deployed (and possibly already-used)
    factory back to 1 - corrupts the state root at the transition block.

    The factory is seeded pre-fork with `pre_fork_nonce` (1 being the EIP
    value, and 2/32 representing nonces accrued from earlier CREATE2
    deployments) and must keep that exact nonce once the fork activates.
    """
    factory = pre.deploy_contract(
        code=Spec.FACTORY_BYTECODE,
        address=Address(Spec.FACTORY_ADDRESS),
        nonce=pre_fork_nonce,
    )
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    blocks = [
        Block(  # pre-fork block
            timestamp=FORK_TIMESTAMP - 1,
            txs=[
                Transaction(sender=sender, to=receiver, value=1, gas_price=10)
            ],
        ),
        Block(  # Amsterdam transition block
            timestamp=FORK_TIMESTAMP,
            txs=[
                Transaction(sender=sender, to=receiver, value=1, gas_price=10)
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            factory: Account(nonce=pre_fork_nonce, code=Spec.FACTORY_BYTECODE),
        },
    )
