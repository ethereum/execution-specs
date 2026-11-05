"""
Framing is a property of entries: an entry reached by a jump from an
unframed entry is unframed, and no unframed entry may contain a
RETURNSUB. Code shared between framed and unframed entries is otherwise
unconstrained.
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
from .spec import ref_spec_8337, relocate

REFERENCE_SPEC_GIT_PATH = ref_spec_8337.git_path
REFERENCE_SPEC_VERSION = ref_spec_8337.version

pytestmark = pytest.mark.valid_from("EIP8337")

# Written for code at position 0; PUSH1 destinations are relocated behind
# the header, like the vectors in ``spec.py``.
CASES = [
    # A revert block reached from the top level (by JUMPI, unframed) and
    # from a subroutine (by JUMP, framed): it contains no RETURNSUB, so it
    # is valid however it is reached.
    #   CALLDATASIZE PUSH1 rev JUMPI  PUSH1 sub CALLSUB  STOP
    #   sub: CALLDEST PUSH1 rev JUMP    rev: CALLDEST PUSH0 DUP1 REVERT
    (
        "shared_revert_block_both_framings",
        "36600C576008BC00BB600C56BB5F80FD",
        True,
    ),
    # A subroutine entered by JUMP from the top level and by CALLSUB: it
    # contains a RETURNSUB, which the unframed entry could reach with an
    # empty return stack.
    #   CALLDATASIZE PUSH1 sub JUMPI  PUSH1 sub CALLSUB  STOP
    #   sub: CALLDEST RETURNSUB
    (
        "entered_unframed_and_framed_with_returnsub",
        "366008576008BC00BBBF",
        False,
    ),
    # f is called; f jumps to g; g returns: g is framed through f.
    ("framed_chain_tail_call", "6004BC00BB600856BBBF", True),
    # The top level jumps to f; f jumps to g; g returns: unframed all the way.
    ("unframed_chain", "600356BB600756BBBF", False),
    # A longer unframed chain: the top level jumps to a, a jumps to b, b
    # jumps to c, c stops. Framing must propagate across three jump links;
    # none of the entries returns, so the code is valid.
    #   PUSH1 a JUMP  a: CALLDEST PUSH1 b JUMP
    #   b: CALLDEST PUSH1 c JUMP  c: CALLDEST STOP
    ("unframed_chain_three_links_stop", "600356BB600756BB600B56BB00", True),
    # The same chain ending in a RETURNSUB at the third entry: framing must
    # reach c to see that an unframed entry returns, so the code is invalid.
    #   ... c: CALLDEST RETURNSUB
    (
        "unframed_chain_three_links_returnsub",
        "600356BB600756BB600B56BBBF",
        False,
    ),
]


@pytest.mark.parametrize(
    "body_hex,valid",
    [pytest.param(body, valid, id=name) for name, body, valid in CASES],
)
def test_framing(
    state_test: StateTestFiller,
    pre: Alloc,
    body_hex: str,
    valid: bool,
) -> None:
    """
    Deploy each case behind the MAGIC header; the account exists iff the
    code is valid.
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
    post = {created: Account(code=code) if valid else Account.NONEXISTENT}
    state_test(pre=pre, post=post, tx=tx)
