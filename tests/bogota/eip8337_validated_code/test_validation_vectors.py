"""
The EIP's validation vectors, deployed as MAGIC code by a creation
transaction: valid code is stored, invalid code halts the creation.

Vectors are written for code starting at position 0; behind the 3-byte
header every PUSH1 destination is shifted by 3 (see ``spec.relocate``).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .helpers import TX_GAS_LIMIT, magic
from .spec import VECTORS, ref_spec_8337, relocate

REFERENCE_SPEC_GIT_PATH = ref_spec_8337.git_path
REFERENCE_SPEC_VERSION = ref_spec_8337.version

pytestmark = pytest.mark.valid_from("EIP8337")


@pytest.mark.parametrize(
    "body_hex,valid",
    [pytest.param(body, valid, id=name) for name, body, valid in VECTORS],
)
def test_validation_vectors(
    state_test: StateTestFiller,
    pre: Alloc,
    body_hex: str,
    valid: bool,
) -> None:
    """
    Deploy each vector behind the MAGIC header; the account exists iff
    the code is valid.
    """
    code = magic(relocate(body_hex))
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=Initcode(deploy_code=code),
        gas_limit=TX_GAS_LIMIT,
    )
    created = compute_create_address(address=sender, nonce=0)
    post = {
        created: Account(code=code) if valid else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


def test_push0_destination_is_the_header(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    The EIP's "PUSH0-preceded JUMP" vector (JUMPDEST, PUSH0, JUMP) is valid
    bare, where position 0 is the JUMPDEST. Behind a header position 0 is
    a MAGIC byte, not an instruction, so the same body is invalid.
    """
    code = magic(bytes.fromhex("5B5F56"))
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=Initcode(deploy_code=code),
        gas_limit=TX_GAS_LIMIT,
    )
    created = compute_create_address(address=sender, nonce=0)
    state_test(pre=pre, post={created: Account.NONEXISTENT}, tx=tx)
