"""
Verify a CALLCODE made from inside init code to an existing contract.

The existing contract's code runs in the created account's context: its
storage write lands there, while the existing contract keeps its own
storage and receives no value. Parametrized over the endowment and the
CALLCODE value, including an endowment too small for the transfer, so
the CALLCODE fails.

Ported from:
state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json

@manually-enhanced: Do not overwrite. The calldata-dispatch entry
contract is collapsed into a direct transaction to the create-runner,
sub-calls forward all gas (EIP-8037-proof), the post pins both the
created and the existing account, and the value cases are parametrized.
Widened down to TangerineWhistle, the EIP-150 floor for forwarding all
gas; CREATE2 rejoins at Constantinople.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Macros,
    Op,
    Opcodes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SUCCESS_FLAG_SLOT = 1
DELEGATE_SLOT = 2


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize(
    "create_endowment,callcode_value",
    [
        pytest.param(1, 1, id="1_wei_value"),
        pytest.param(0, 0, id="zero_value"),
        pytest.param(0, 1, id="1_wei_callcode_value_with_zero_balance"),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_callcode_in_initcode_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Opcodes,
    create_endowment: int,
    callcode_value: int,
) -> None:
    """Verify a CALLCODE in init code runs in the created account."""
    existing = pre.deploy_contract(
        code=Op.SSTORE(key=DELEGATE_SLOT, value=1) + Op.STOP,
    )

    initcode = (
        Op.SSTORE(
            key=SUCCESS_FLAG_SLOT,
            value=Op.CALLCODE(address=existing, value=callcode_value),
        )
        + Op.STOP
    )
    initcode_bytes = bytes(initcode)

    create_call = create_opcode(
        value=create_endowment,
        offset=0,
        size=len(initcode_bytes),
    )
    runner_balance = max(create_endowment, callcode_value) + 1
    runner = pre.deploy_contract(
        code=Macros.MSTORE(initcode_bytes) + create_call + Op.STOP,
        balance=runner_balance,
    )

    created = compute_create_address(
        address=runner,
        nonce=1,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=runner,
        protected=fork.supports_protected_txs(),
    )

    created_nonce = 1 if fork.is_eip_enabled(161) else 0
    callcode_success = create_endowment >= callcode_value
    post = {
        created: Account(
            code=b"",
            nonce=created_nonce,
            balance=create_endowment,
            storage={SUCCESS_FLAG_SLOT: 1, DELEGATE_SLOT: 1}
            if callcode_success
            else {SUCCESS_FLAG_SLOT: 0, DELEGATE_SLOT: 0},
        ),
        runner: Account(
            nonce=2,
            balance=runner_balance - create_endowment,
            storage={},
        ),
        existing: Account(balance=0, storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
