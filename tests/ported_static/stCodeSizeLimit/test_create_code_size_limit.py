"""
Deploy code at and one byte over the maximum code size via CREATE/CREATE2.

Ported from:
state_tests/stCodeSizeLimit/createCodeSizeLimitFiller.yml
state_tests/stCodeSizeLimit/create2CodeSizeLimitFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
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
        "state_tests/stCodeSizeLimit/createCodeSizeLimitFiller.yml",
        "state_tests/stCodeSizeLimit/create2CodeSizeLimitFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
# Kept before EIP-7954: the fixed 15M gas transaction cannot fund the
# EIP-8037 code-deposit state gas of a max-size contract (about 100M at
# 64KiB). tests/amsterdam/eip7954_increase_max_contract_size covers the
# raised limit with fork-sized gas.
@pytest.mark.valid_before("EIP7954")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "oversize", [pytest.param(0, id="valid"), pytest.param(1, id="invalid")]
)
def test_create_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    oversize: int,
) -> None:
    """Deploy code at and one byte over the maximum code size."""
    sender = pre.fund_eoa()
    code_size = fork.max_code_size() + oversize
    initcode = Bytes(Op.RETURN(offset=0, size=code_size))

    if opcode == Op.CREATE2:
        create = Op.CREATE2(value=0, offset=0, size=Op.CALLDATASIZE, salt=0)
    else:
        create = Op.CREATE(value=0, offset=0, size=Op.CALLDATASIZE)
    creator = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
        + Op.SSTORE(key=0, value=create)
        + Op.SSTORE(key=1, value=1)
        + Op.STOP,
    )
    created = compute_create_address(
        address=creator, nonce=1, salt=0, initcode=initcode, opcode=opcode
    )

    post: dict = {sender: Account(nonce=1)}
    if oversize:
        post[creator] = Account(storage={0: 0, 1: 1}, nonce=2)
        post[created] = Account.NONEXISTENT
    else:
        post[creator] = Account(storage={0: created, 1: 1}, nonce=2)
        post[created] = Account(
            storage={}, balance=0, nonce=1, code=bytes(code_size)
        )

    tx = Transaction(
        sender=sender,
        to=creator,
        data=initcode,
        gas_limit=15_000_000,
    )

    state_test(pre=pre, post=post, tx=tx)
