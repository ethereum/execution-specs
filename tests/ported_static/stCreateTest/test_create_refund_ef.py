"""
Earn a gas refund in init code that then returns 0xEF-prefixed code.

Ported from:
state_tests/stCreateTest/CreateTransactionRefundEFFiller.yml
state_tests/stCreateTest/CREATE2_RefundEFFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def create2_deployer(initcode: Bytecode, offset: int) -> Bytecode:
    """Return code that runs CREATE2 on `initcode` appended at `offset`."""
    return (
        Op.CODECOPY(dest_offset=0, offset=offset, size=len(initcode))
        + Op.SSTORE(
            key=0,
            value=Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0),
        )
        + Op.STOP
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CreateTransactionRefundEFFiller.yml",
        "state_tests/stCreateTest/CREATE2_RefundEFFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("create_kind", ["create_transaction", "create2"])
def test_create_refund_ef(
    state_test: StateTestFiller,
    pre: Alloc,
    create_kind: str,
) -> None:
    """Earn a gas refund in init code that returns 0xEF-prefixed code."""
    sender = pre.fund_eoa()
    # Source: yul
    # london {
    #   sstore(0,0)
    # }
    refund_provider = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=0) + Op.STOP,
        storage={0: 1},
    )
    initcode = (
        Op.POP(Op.CALL(address=refund_provider))
        + Op.MSTORE8(offset=0x0, value=0xEF)
        + Op.RETURN(offset=0x0, size=0x1)
    )

    post: dict = {refund_provider: Account(storage={0: 1})}
    if create_kind == "create_transaction":
        tx = Transaction(sender=sender, to=None, data=initcode)
        created = compute_create_address(address=sender, nonce=0)
    elif create_kind == "create2":
        offset = len(create2_deployer(initcode, 0))
        creator = pre.deploy_contract(
            code=create2_deployer(initcode, offset) + initcode
        )
        tx = Transaction(sender=sender, to=creator)
        created = compute_create_address(
            address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
        )
        post[creator] = Account(storage={}, nonce=2)
    else:
        raise ValueError(f"Unknown create kind: {create_kind}")
    post[created] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)
