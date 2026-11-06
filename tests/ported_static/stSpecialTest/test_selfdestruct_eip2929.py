"""
SELFDESTRUCT to warm, cold, existing, absent and precompile beneficiaries.

Ported from:
state_tests/stSpecialTest/selfdestructEIP2929Filler.json

@manually-enhanced: Do not overwrite. Calls the deployed self-destructor.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/selfdestructEIP2929Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_selfdestruct_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Self-destruct repeatedly into each beneficiary, cold then warm.

    `existing_*` beneficiaries exist (nonce 1), `absent_*` do not;
    `*_warm` ones are pre-warmed by a zero-gas CALL. Only the first
    SELFDESTRUCT moves the destructor's 1 wei.
    """
    sender = pre.fund_eoa()
    existing_cold = pre.deploy_contract(code=b"")
    absent_cold = pre.nonexistent_account()
    existing_warm = pre.deploy_contract(code=b"")
    absent_warm = pre.nonexistent_account()
    precompiles = [Address(1), Address(2), Address(3)]

    self_destructor_code = Op.SELFDESTRUCT(
        address=Op.AND(2**160 - 1, Op.CALLDATALOAD(offset=0x0))
    )
    self_destructor = pre.deploy_contract(code=self_destructor_code, balance=1)

    code = Bytecode()
    for warmed in [existing_warm, absent_warm, precompiles[2]]:
        code += Op.POP(Op.CALL(gas=0, address=warmed))
    beneficiaries = [
        existing_cold,
        absent_cold,
        existing_warm,
        absent_warm,
        *precompiles,
    ]
    for beneficiary in beneficiaries:
        repeats = 1 if beneficiary == precompiles[2] else 2
        for _ in range(repeats):
            code += Op.MSTORE(offset=0, value=beneficiary)
            code += Op.POP(
                Op.CALL(address=self_destructor, args_offset=0, args_size=32)
            )
    code += Op.SSTORE(key=0x1, value=0x1)
    target = pre.deploy_contract(code=code)

    tx = Transaction(sender=sender, to=target)

    post = {
        target: Account(storage={1: 1}),
        self_destructor: Account(code=self_destructor_code, balance=0),
        existing_cold: Account(balance=1, nonce=1),
        existing_warm: Account(balance=0, nonce=1),
        absent_cold: Account.NONEXISTENT,
        absent_warm: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
