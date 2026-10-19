"""
Verify an out-of-gas contract creation leaves no account behind (the
Homestead-era bug left empty shells), while a sufficient budget creates a
codeless account whose init code called out to a storage writer.

Ported from:
state_tests/stHomesteadSpecific/contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json

@manually-enhanced: Do not overwrite. The ported single case had silently
become success-only (its OOG arm was gone); both arms are restored with
fork-derived budgets, the init code's call budget is derived (the writer's
store is state-priced under EIP-8037), and the writer's slot plus the
created account's fields are asserted.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

RETENTION_MARGIN = 64


@pytest.mark.ported_from(
    [
        "state_tests/stHomesteadSpecific/contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")  # Istanbul and before require EIP-2929
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(True, id="created"),
        pytest.param(False, id="oog_no_account"),
    ],
)
def test_contract_creation_oog_dont_leave_empty_contract_via_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    enough_gas: bool,
) -> None:
    """An OOG creation must not leave an account behind."""
    writer_store = Op.SSTORE(
        key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    writer = pre.deploy_contract(code=writer_store + Op.STOP)

    # The init code calls the writer and deposits nothing. The forwarded
    # budget is derived: with a zero reservoir the writer's state-priced
    # store must fit inside its grant.
    writer_needed = writer_store.gas_cost(fork)
    call_code = Op.CALL(
        gas=writer_needed,
        address=writer,
        args_size=0x40,
        ret_size=0x40,
        address_warm=False,
        value_transfer=False,
        account_new=False,
        new_memory_size=0x40,
    )
    padding_gas = -(-writer_needed // 63) + RETENTION_MARGIN
    padding = Op.JUMPDEST * padding_gas

    execution = call_code.gas_cost(fork) + writer_needed + padding_gas
    initcode = call_code + padding + Op.STOP

    overhead = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    ) + fork.transaction_top_frame_state_gas(contract_creation=True)
    gas_limit = overhead + execution
    if not enough_gas:
        gas_limit -= 1

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
    )

    created = compute_create_address(address=sender, nonce=0)
    if enough_gas:
        created_account: Account | None = Account(nonce=1, code=b"", balance=0)
        writer_storage = {1: 1}
    else:
        created_account = Account.NONEXISTENT
        writer_storage = {1: 0}
    post = {
        sender: Account(nonce=1),
        created: created_account,
        writer: Account(storage=writer_storage),
    }

    state_test(pre=pre, post=post, tx=tx)
