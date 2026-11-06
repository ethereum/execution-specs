"""
Send a creation tx with init code at and one byte over the size limit.

Ported from:
state_tests/Shanghai/stEIP3860_limitmeterinitcode/creationTxInitCodeSizeLimitFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/Shanghai/stEIP3860_limitmeterinitcode/creationTxInitCodeSizeLimitFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "oversize",
    [
        pytest.param(0, id="valid"),
        pytest.param(1, id="invalid", marks=pytest.mark.exception_test),
    ],
)
def test_creation_tx_init_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    oversize: int,
) -> None:
    """Send a creation tx with init code at and over the size limit."""
    sender = pre.fund_eoa()
    runtime_code = bytes.fromhex("60606040523615610074576000357c01")
    deployer_size = 12
    deployer = Op.CODECOPY(
        dest_offset=0, offset=deployer_size, size=len(runtime_code)
    ) + Op.RETURN(offset=0, size=len(runtime_code))
    assert len(deployer) == deployer_size
    initcode = (bytes(deployer) + runtime_code).ljust(
        fork.max_initcode_size() + oversize, b"\0"
    )

    created = compute_create_address(address=sender, nonce=0)
    post: dict
    if oversize:
        post = {
            sender: Account(nonce=0),
            created: Account.NONEXISTENT,
        }
        error = TransactionException.INITCODE_SIZE_EXCEEDED
    else:
        post = {
            sender: Account(nonce=1),
            created: Account(
                storage={}, code=runtime_code, balance=0, nonce=1
            ),
        }
        error = None

    tx = Transaction(sender=sender, to=None, data=initcode, error=error)

    state_test(pre=pre, post=post, tx=tx)
