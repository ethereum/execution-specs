"""
CALLSUB, CALLDEST and RETURNSUB in initcode and in delegated code.

The message-frame tests are in ``test_returnsub.py``; these cover the two
other places code runs: contract creation (transaction initcode and
CREATE/CREATE2) and an EIP-7702 delegated EOA.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .helpers import (
    MARKER_IN_SUBROUTINE,
    SLOT_MARKER,
    TX_GAS_LIMIT,
    program,
    subroutine_storing_marker,
)
from .spec import ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

pytestmark = pytest.mark.valid_from("EIP7979")


def initcode_using_subroutine() -> Bytecode:
    """
    Return initcode that calls a subroutine which stores a marker, then
    returns a one-byte runtime code (STOP).
    """

    def main(offset: int) -> Bytecode:
        return (
            Op.CALLSUB(offset) + Op.MSTORE8(0, Op.STOP.int()) + Op.RETURN(0, 1)
        )

    code, _ = program(main, subroutine_storing_marker())
    return code


def test_subroutine_in_transaction_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A creation transaction's initcode may use subroutines."""
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode_using_subroutine(),
        gas_limit=TX_GAS_LIMIT,
    )
    created = compute_create_address(address=sender, nonce=0)
    post = {
        created: Account(
            code=Op.STOP, storage={SLOT_MARKER: MARKER_IN_SUBROUTINE}
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_subroutine_in_create_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """Initcode run by CREATE and CREATE2 may use subroutines."""
    initcode = initcode_using_subroutine()
    factory_code = Op.CALLDATACOPY(offset=0, size=len(initcode)) + Op.SSTORE(
        0, create_opcode(offset=0, size=len(initcode))
    )
    factory = pre.deploy_contract(factory_code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        data=initcode,
        gas_limit=TX_GAS_LIMIT,
    )
    if create_opcode == Op.CREATE:
        created = compute_create_address(address=factory, nonce=1)
    else:
        created = compute_create_address(
            address=factory, initcode=initcode, salt=0, opcode=Op.CREATE2
        )
    post = {
        factory: Account(storage={0: created}),
        created: Account(
            code=Op.STOP, storage={SLOT_MARKER: MARKER_IN_SUBROUTINE}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_subroutine_in_delegated_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    An EIP-7702 delegated EOA runs subroutines in its own storage
    context.
    """
    code, _ = program(
        lambda offset: Op.CALLSUB(offset), subroutine_storing_marker()
    )
    delegate_to = pre.deploy_contract(code)
    auth_signer = pre.fund_eoa(0)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=auth_signer,
        gas_limit=TX_GAS_LIMIT,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_to, nonce=0, signer=auth_signer
            ),
        ],
    )
    post = {
        auth_signer: Account(storage={SLOT_MARKER: MARKER_IN_SUBROUTINE}),
    }
    state_test(pre=pre, post=post, tx=tx)
