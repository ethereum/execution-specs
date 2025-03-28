"""abstract: Test delegatecall to Blake2B Precompile before and after it was added."""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_forks.forks.forks import Istanbul
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-152.md"
REFERENCE_SPEC_VERSION = "2762bfcff3e549ef263342e5239ef03ac2b07400"

BLAKE2_PRECOMPILE_ADDRESS = 0x09


@pytest.mark.valid_from("ConstantinopleFix")
def test_blake2_precompile_delegatecall(state_test: StateTestFiller, pre: Alloc, fork: Fork):
    """Test delegatecall consumes specified gas for the Blake2B precompile when it exists."""
    env = Environment()

    account = pre.deploy_contract(
        Op.SSTORE(
            0,
            Op.DELEGATECALL(
                gas=1,
                address=BLAKE2_PRECOMPILE_ADDRESS,
            ),
        )
        + Op.STOP,
        storage={0: 0xDEADBEEF},
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=90_000,
        protected=True,
    )

    # If precompile exists, DELEGATECALL will fail, otherwise DELEGATECALL will succeed
    post = {
        account: Account(
            storage={
                0: "0x00" if fork >= Istanbul else "0x01",
            }
        )
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
