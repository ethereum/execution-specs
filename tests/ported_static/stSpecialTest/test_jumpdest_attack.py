"""
Recursively self-call a contract padded with 15000 JUMPDESTs.

Every call re-runs jump destination analysis over the padding.

Ported from:
state_tests/stSpecialTest/JUMPDEST_AttackFiller.json
state_tests/stSpecialTest/JUMPDEST_AttackwithJumpFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

RETAINED_GAS = 50_000
PADDING = 15_000


@pytest.mark.ported_from(
    [
        "state_tests/stSpecialTest/JUMPDEST_AttackFiller.json",
        "state_tests/stSpecialTest/JUMPDEST_AttackwithJumpFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "leading_jump",
    [
        pytest.param(False, id="jumpdest_attack"),
        pytest.param(True, id="jumpdest_attackwith_jump"),
    ],
)
def test_jumpdest_attack(
    state_test: StateTestFiller,
    pre: Alloc,
    leading_jump: bool,
) -> None:
    """Call itself with all but 50000 gas until the gas runs out."""
    sender = pre.fund_eoa()

    code = Bytecode()
    if leading_jump:
        code = Op.JUMP(pc=0x3) + Op.JUMPDEST
    code += (
        Op.CALL(gas=Op.SUB(Op.GAS, RETAINED_GAS), address=Op.ADDRESS)
        + Op.STOP
        + Op.JUMPDEST * PADDING
    )
    target = pre.deploy_contract(code=code)

    tx = Transaction(sender=sender, to=target, gas_limit=2**24, value=0x186A0)

    post = {
        target: Account(balance=tx.value),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
