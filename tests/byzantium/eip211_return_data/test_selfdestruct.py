"""Test SELFDESTRUCT return data buffer behavior."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_211

REFERENCE_SPEC_GIT_PATH = ref_spec_211.git_path
REFERENCE_SPEC_VERSION = ref_spec_211.version


@pytest.mark.valid_from("Byzantium")
def test_selfdestruct_clears_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SELFDESTRUCT returns empty data after an inner call returns data.

    The selfdestructing contract first performs a call that leaves 32 bytes in
    its own return-data buffer. The outer caller must still observe empty
    return data from the selfdestructing call.
    """
    returns_32 = pre.deploy_contract(
        code=Op.MSTORE(0, 0x112233) + Op.RETURN(0, 32)
    )

    selfdestructs = pre.deploy_contract(
        code=Op.POP(Op.CALL(address=returns_32, ret_size=0))
        + Op.SELFDESTRUCT(Op.CALLER)
    )

    caller = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            Op.CALL(address=selfdestructs, ret_size=0),
        )
        + Op.SSTORE(1, Op.RETURNDATASIZE)
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    state_test(
        pre=pre,
        tx=tx,
        post={caller: Account(storage={0: 1, 1: 0})},
    )
