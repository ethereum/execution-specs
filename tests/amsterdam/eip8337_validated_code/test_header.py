"""
The MAGIC header at CREATE: which prefixes are accepted, which are
rejected, and the EIP-3541 boundary for other 0xEF code.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .helpers import TX_GAS_LIMIT, raw
from .spec import Spec, ref_spec_8337

REFERENCE_SPEC_GIT_PATH = ref_spec_8337.git_path
REFERENCE_SPEC_VERSION = ref_spec_8337.version

pytestmark = pytest.mark.valid_from("EIP8337")

BODY = bytes(Op.SSTORE(1, 1) + Op.STOP)


@pytest.mark.parametrize(
    "code,accepted",
    [
        pytest.param(Spec.MAGIC_HEADER + BODY, True, id="magic_valid_body"),
        pytest.param(Spec.MAGIC_HEADER, False, id="header_only"),
        pytest.param(Spec.MAGIC + b"\x02" + BODY, False, id="wrong_version"),
        pytest.param(Spec.MAGIC, False, id="magic_without_version"),
        pytest.param(b"\xef" + BODY, False, id="eip3541_bare_ef"),
        pytest.param(b"\xef\x00\x01" + BODY, False, id="eip3541_eof_prefix"),
        pytest.param(b"\xef\x01\x00" + BODY, False, id="eip3541_7702_prefix"),
        pytest.param(BODY, True, id="plain_code_unaffected"),
    ],
)
def test_created_code_prefix(
    state_test: StateTestFiller,
    pre: Alloc,
    code: bytes,
    accepted: bool,
) -> None:
    """
    Only a complete, correct MAGIC header with a valid body is accepted.
    Every other 0xEF prefix is still rejected as before (EIP-3541), and
    code that does not begin with 0xEF is unaffected.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=Initcode(deploy_code=raw(code)),
        gas_limit=TX_GAS_LIMIT,
    )
    created = compute_create_address(address=sender, nonce=0)
    post = {
        created: Account(code=code) if accepted else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)
