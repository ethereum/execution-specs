"""
The first test case required here.

https://github.com/ethereum/tests/issues/431#issue-306081539

Implements: SUC007.0, SUC007.1, SUC007.2, SUC007.3,
            SUC008.0, SUC008.1, SUC008.2, SUC008.3

Ported from:
state_tests/stSystemOperationsTest/doubleSelfdestructTestFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Conditional,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 1_000_000
TX_VALUE = 1


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/doubleSelfdestructTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
    ids=["call", "callcode", "delegatecall", "staticcall"],
)
@pytest.mark.parametrize(
    "called_to_self",
    [False, True],
    ids=["called_self_destruct", "code_self_destruct"],
)
def test_double_selfdestruct_test(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    called_to_self: bool,
) -> None:
    """
    Call self with `opcode` to SELFDESTRUCT, then SELFDESTRUCT again.

    The called frame's beneficiary is another account or the contract
    itself; the caller's beneficiary is a third account. Under
    STATICCALL the called SELFDESTRUCT fails.
    """
    sender = pre.fund_eoa()
    caller_beneficiary = pre.nonexistent_account()
    other_beneficiary = pre.nonexistent_account()

    # Source: yul
    # berlin
    # {
    #    if gt(calldatasize(), 2) {
    #      ... call/callcode/delegatecall/staticcall(gas(), 0xc0de, ...)
    #      selfdestruct(caller_ff)
    #    }
    #    if eq(calldatasize(), 2) { selfdestruct(called_ff) }
    # }
    # The beneficiaries are now full 20-byte calldata fields: the
    # caller's at offset 0, the called frame's at offset 20.
    contract = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLDATASIZE, 20),
            if_true=Op.SELFDESTRUCT(Op.SHR(96, Op.CALLDATALOAD(0))),
            if_false=Op.CALLDATACOPY(0, 20, 20)
            + Op.POP(opcode(address=Op.ADDRESS, args_size=20))
            + Op.SELFDESTRUCT(Op.SHR(96, Op.CALLDATALOAD(0))),
        ),
        balance=CONTRACT_BALANCE,
    )
    called_beneficiary = contract if called_to_self else other_beneficiary

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes(caller_beneficiary) + bytes(called_beneficiary),
        value=TX_VALUE,
    )

    total = CONTRACT_BALANCE + TX_VALUE
    if opcode != Op.STATICCALL and not called_to_self:
        post = {
            caller_beneficiary: Account.NONEXISTENT,
            other_beneficiary: Account(balance=total),
            contract: Account(balance=0, nonce=1),
        }
    else:
        post = {
            caller_beneficiary: Account(balance=total, nonce=0),
            other_beneficiary: Account.NONEXISTENT,
            contract: Account(balance=0, nonce=1),
        }

    state_test(pre=pre, post=post, tx=tx)
