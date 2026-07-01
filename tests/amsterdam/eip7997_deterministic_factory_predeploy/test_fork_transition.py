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

    runtime_code = Op.RETURN(0, 1)  # Deploys contract only contains Op.STOP
    initcode = Initcode(deploy_code=runtime_code)

    timestamps = [FORK_TIMESTAMP - 1, FORK_TIMESTAMP]

    blocks = []
    deployed = {}
    for timestamp in timestamps:
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
