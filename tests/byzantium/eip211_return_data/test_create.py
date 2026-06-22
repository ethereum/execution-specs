"""Test CREATE/CREATE2 return data buffer behavior on pre-check failure."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_211

REFERENCE_SPEC_GIT_PATH = ref_spec_211.git_path
REFERENCE_SPEC_VERSION = ref_spec_211.version


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(
            Op.CREATE2,
            id="CREATE2",
            marks=pytest.mark.valid_from("Constantinople"),
        ),
    ],
)
def test_create_clears_return_data_on_insufficient_balance(
    create_opcode: Op,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test that entering CREATE/CREATE2 clears the return-data buffer even when
    the create fails a pre-execution check (insufficient balance) and the
    initcode never runs.

    Existing return-data tests for CREATE/CREATE2 always execute the initcode
    (which RETURNs or REVERTs), covering only the post-initcode path. Entering
    a CREATE must reset the return-data buffer unconditionally, including the
    depth/nonce/balance pre-checks that abort before any initcode runs. A
    client that clears the buffer only after those pre-checks would leave stale
    return data from a preceding CALL via RETURNDATASIZE/RETURNDATACOPY.

    The caller performs a CALL that leaves 32 bytes of return data, then a
    create with value exceeding its balance (failing the balance pre-check
    before initcode), and asserts RETURNDATASIZE is 0 afterward.

    Storage layout:
      slot N = RETURNDATASIZE after the CALL    (expected 32)
      slot N+1 = RETURNDATASIZE after the create  (expected 0)
      slot N+2 = the create result address        (expected 0, i.e. failure)
    """
    storage = Storage()

    # Callee returns 32 bytes, so the caller's return-data buffer is 32 bytes.
    callee = pre.deploy_contract(
        code=Op.MSTORE(0, 0x11223344) + Op.RETURN(0, 32),
    )

    init_balance = 1
    create_op = create_opcode(value=init_balance + 1)

    # Caller has balance 1, so a create with value 2 fails the balance
    # pre-check before executing any initcode.
    caller = pre.deploy_contract(
        balance=init_balance,
        code=(
            Op.CALL(gas=Op.GAS, address=callee, ret_size=32)
            + Op.SSTORE(
                storage.store_next(32, "rds_after_call"), Op.RETURNDATASIZE
            )
            + Op.SSTORE(storage.store_next(0, "create_result"), create_op)
            + Op.SSTORE(
                storage.store_next(0, "rds_after_create"), Op.RETURNDATASIZE
            )
            + Op.STOP
        ),
        storage=dict.fromkeys(storage, 0xFF),
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
    )

    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
    )
