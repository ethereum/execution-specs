"""
EXTCODEHASH of an empty account touched as a SELFDESTRUCT beneficiary.

Found by fuzzing with EVMlab: geth reported a non-zero code hash for the
touched-but-empty beneficiary.

Ported from:
state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192Filler.json
state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192Filler.json",  # noqa: E501
        "state_tests/stBugs/randomStatetestDEFAULT-Tue_07_58_41-15153-575192_londonFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "gas_price",
    [pytest.param(11, id="legacy"), pytest.param(10, id="london")],
)
def test_random_statetest_default_minus_tue_07_58_41_minus_15153_minus_575192(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_price: int,
) -> None:
    """Store EXTCODEHASH of a beneficiary left empty by SELFDESTRUCT."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()

    self_destructor = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=beneficiary),
    )
    # The leading PUSH2 0xDEAD is a fuzzer leftover.
    target_code = (
        Op.PUSH2[0xDEAD]
        + Op.CALL(address=self_destructor)
        + Op.SSTORE(key=0x1, value=Op.EXTCODEHASH(address=beneficiary))
    )
    target = pre.deploy_contract(code=target_code)

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=6282759,
        gas_price=gas_price,
    )

    post = {
        target: Account(storage={}, code=target_code),
        beneficiary: Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(
        env=Environment(fee_recipient=target), pre=pre, post=post, tx=tx
    )
