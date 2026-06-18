"""
Test EIP-8037 state-gas refund when a CREATE2 whose init created storage
fails its code deposit.

Under EIP-8037 a CREATE2 init that writes new storage slots is charged
state-creation gas (``STATE_BYTES_PER_STORAGE_SET * COST_PER_STATE_BYTE``
per slot) plus new-account state gas. If the deposit then fails -- because
the init returns ``0xEF``-prefixed code (EIP-3541) or because the code
deposit cost exceeds the available gas -- the create frame reverts and
ALL of the init's state-creation gas (account AND storage slots) must be
refunded, so the failing CREATE2 leaves no net state-gas charge.

The transaction's total gas used (and therefore the sender/coinbase
balances and the post-state root) is identical regardless of how much
storage the reverted init touched. A client that refunds the new-account
state gas but fails to refund the init's storage-slot state gas on the
create failure over-reports gas used and diverges on the post-state root.

The negative control ``slots=0`` (init creates the account but no storage)
must NOT diverge -- only the storage-slot refund is at issue.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import Spec, init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.parametrize("slots", [0, 1, 3])
@pytest.mark.parametrize("fail_mode", ["eip3541", "oog_deposit"])
@pytest.mark.valid_from("EIP8037")
def test_create2_failed_deposit_refunds_init_storage_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    slots: int,
    fail_mode: str,
) -> None:
    """
    Test a CREATE2 whose init creates ``slots`` storage slots then fails
    code deposit, asserting the failure fully refunds the init's
    state-creation gas (so total gas used is independent of ``slots``).

    The init writes ``slots`` fresh storage slots -- each charged
    ``STATE_BYTES_PER_STORAGE_SET * COST_PER_STATE_BYTE`` state gas -- and
    then fails its deposit, either by returning ``0xEF``-prefixed code
    (EIP-3541) or by returning code whose deposit cost cannot be paid
    (OOG). The create frame reverts; its account- and storage-creation
    state gas must be refunded. The factory records the CREATE2 result
    (``0``, failure).

    A client that does not refund the reverted init's storage-slot state
    gas reports a larger gas used for ``slots >= 1`` and diverges on the
    post-state root; ``slots == 0`` is the negative control and must not
    diverge.
    """
    # init: write `slots` new storage slots, then trigger a deposit failure
    init_code = Bytecode()
    for i in range(slots):
        init_code += Op.SSTORE(i, i + 1)
    if fail_mode == "eip3541":
        # return 0xEF -> EIP-3541 rejects the deposited code
        init_code += Op.MSTORE8(0, 0xEF) + Op.RETURN(0, 1)
    else:
        # return max-size code: the code-deposit state gas cannot be paid
        init_code += Op.RETURN(0, fork.max_code_size())
    mstore_value, size = init_code_at_high_bytes(init_code)

    storage = Storage()
    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, mstore_value)
            + Op.SSTORE(
                storage.store_next(0, "create2_failed"),
                Op.CREATE2(value=0, offset=0, size=size, salt=0),
            )
        ),
    )

    tx = Transaction(
        to=factory,
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={factory: Account(storage=storage)},
        tx=tx,
    )
