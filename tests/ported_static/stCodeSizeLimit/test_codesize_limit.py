"""
Deploy code below, at and over the maximum code size from a creation tx.

Ported from:
state_tests/stCodeSizeLimit/codesizeValidFiller.json
state_tests/stCodeSizeLimit/codesizeOOGInvalidSizeFiller.json
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCodeSizeLimit/codesizeValidFiller.json",
        "state_tests/stCodeSizeLimit/codesizeOOGInvalidSizeFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "size_delta",
    [
        pytest.param(-299, id="below_limit"),
        pytest.param(0, id="at_limit"),
        pytest.param(1, id="over_limit_by_1"),
        pytest.param(13, id="over_limit_by_13"),
    ],
)
def test_codesize_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    size_delta: int,
) -> None:
    """Deploy code below, at and over the maximum code size."""
    sender = pre.fund_eoa()
    code_size = fork.max_code_size() + size_delta
    code_offset = 0xD
    initcode: Bytecode = Op.CODECOPY(
        dest_offset=0, offset=code_offset, size=code_size
    ) + Op.RETURN(offset=0, size=code_size)
    tx_value = 1

    tx = Transaction(sender=sender, to=None, data=initcode, value=tx_value)

    created = compute_create_address(address=sender, nonce=0)
    post: dict
    if size_delta > 0:
        post = {created: Account.NONEXISTENT}
    else:
        code = bytes(initcode)[code_offset:].ljust(code_size, b"\0")
        post = {created: Account(balance=tx_value, code=code)}

    state_test(pre=pre, post=post, tx=tx)
