"""Fork-transition tests for EIP-8337: no MAGIC code before the fork."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)

from .helpers import TX_GAS_LIMIT, magic
from .spec import ref_spec_8337

REFERENCE_SPEC_GIT_PATH = ref_spec_8337.git_path
REFERENCE_SPEC_VERSION = ref_spec_8337.version

FORK_TIMESTAMP = 15_000


@pytest.mark.valid_at_transition_to("EIP8337")
def test_magic_creation_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Before the fork, code beginning with 0xEF is rejected at creation
    (EIP-3541); from the fork onward, valid MAGIC code is created.
    """
    sender = pre.fund_eoa()
    code = magic(Op.SSTORE(1, 1) + Op.STOP)
    blocks = [
        Block(
            timestamp=ts,
            txs=[
                Transaction(
                    sender=sender,
                    to=None,
                    data=Initcode(deploy_code=code),
                    gas_limit=TX_GAS_LIMIT,
                )
            ],
        )
        for ts in (FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1)
    ]
    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        compute_create_address(address=sender, nonce=1): Account(code=code),
        compute_create_address(address=sender, nonce=2): Account(code=code),
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
