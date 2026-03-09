"""
expect section set -indexes field by default equal to -1.

Ported from:
tests/static/state_tests/stExample/indexesOmitExampleFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stExample/indexesOmitExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_indexes_omit_example(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Expect section set -indexes field by default equal to -1."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (ADD 1 1)
    # }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xad21eb96c7a254c810474f7b1e1e66ca449a3426"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=400000,
        value=100000,
    )

    post = {
        contract: Account(storage={0: 2}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
