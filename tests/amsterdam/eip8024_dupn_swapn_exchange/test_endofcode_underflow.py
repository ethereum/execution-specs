"""
EIP-8024 end-of-code stack underflow regression tests.

When DUPN/SWAPN/EXCHANGE is the last byte of code, the missing immediate
byte decodes to `0` per EIP-8024, and the opcode must still execute with
that zero-decoded immediate. When the stack is short of the resulting
required depth, execution must halt with stack underflow — clients must
not treat the missing immediate as a graceful STOP.

See:
- EIP-8024: https://eips.ethereum.org/EIPS/eip-8024
- Bounty: https://github.com/ethereum-bounty/nethermind/issues/12
- Fix:    https://github.com/NethermindEth/nethermind/pull/11178
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("EIP8024")


@pytest.mark.parametrize(
    "eip8024_opcode,pushed_items",
    [
        # DUPN: decode_single(0) = 145, needs 145 items — push 144.
        pytest.param(Op.DUPN, 144, id="dupn"),
        # SWAPN: decode_single(0) = 145, needs 146 items — push 145.
        pytest.param(Op.SWAPN, 145, id="swapn"),
        # EXCHANGE: decode_pair(0) = (9, 16), needs 17 items — push 16.
        pytest.param(Op.EXCHANGE, 16, id="exchange"),
    ],
)
def test_end_of_code_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
    eip8024_opcode: Op,
    pushed_items: int,
) -> None:
    """
    Test EIP-8024 opcodes at end of code with one fewer stack item than
    required by the zero-decoded immediate.

    Per EIP-8024, `code[pc + 1]` evaluates to `0` when beyond end of code.
    The opcode must still execute and, with insufficient stack depth for
    the decoded immediate, must halt with stack underflow.

    A buggy implementation that treats the missing immediate as an
    implicit STOP would incorrectly succeed and persist the marker
    stored before the opcode.
    """
    sender = pre.fund_eoa()
    marker_value = 0x42

    code = (
        # store marker that must not persist if the opcode underflows
        Op.SSTORE(0, marker_value)
        # one fewer item than the zero-decoded immediate requires
        + Op.PUSH0 * pushed_items
        # end-of-code EIP-8024 opcode, no immediate byte
        + eip8024_opcode
    )
    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction must fail (stack underflow), leaving storage untouched.
    post = {contract_address: Account(storage={})}
    state_test(pre=pre, post=post, tx=tx)
