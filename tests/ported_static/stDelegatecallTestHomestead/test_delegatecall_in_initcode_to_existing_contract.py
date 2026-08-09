"""
Verify a DELEGATECALL made from inside init code to an existing
contract.

The created account's init code DELEGATECALLs an already-deployed
contract, so that contract's code runs in the freshly created account's
context with the init frame's caller preserved: both the delegate and
the init code itself observe the creating contract as CALLER, and every
storage write lands in the created account, never in the delegate.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json

@manually-enhanced: Do not overwrite. The port's unused second creator
contract is deleted, the raw-word init code is composed, the delegate
call forwards all gas (EIP-8037-proof), the transaction budget is
maxed, and the post also pins the created account's code/nonce/balance
and that the delegate's own storage stays untouched.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Macros,
    Op,
    Opcodes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CREATE_ENDOWMENT = 1
RUNNER_BALANCE = 10_000

# Written by the init code with the DELEGATECALL's success flag.
DELEGATE_RESULT_SLOT = 0
# Written by the init code with the CALLER it observes (the runner).
INITCODE_CALLER_SLOT = 1
# Written by the delegate's code, in the created account's context.
DELEGATE_WRITE_SLOT = 2
# Written by the delegate with the CALLER it observes (still the
# runner: DELEGATECALL preserves the init frame's caller).
DELEGATE_CALLER_SLOT = 0xB
DELEGATE_VALUE_SLOT = 0xC


@pytest.mark.ported_from(
    [
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("SpuriousDragon")
def test_delegatecall_in_initcode_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Opcodes,
) -> None:
    """A DELEGATECALL in init code runs in the created account."""
    existing = pre.deploy_contract(
        code=Op.SSTORE(key=DELEGATE_WRITE_SLOT, value=1)
        + Op.SSTORE(key=DELEGATE_CALLER_SLOT, value=Op.CALLER)
        + Op.SSTORE(key=DELEGATE_VALUE_SLOT, value=Op.CALLVALUE)
        + Op.STOP,
    )

    initcode = (
        Op.SSTORE(
            key=DELEGATE_RESULT_SLOT,
            value=Op.DELEGATECALL(address=existing),
        )
        + Op.SSTORE(key=INITCODE_CALLER_SLOT, value=Op.CALLER)
        + Op.STOP
    )

    runner = pre.deploy_contract(
        code=Macros.MSTORE(initcode)
        + create_opcode(value=CREATE_ENDOWMENT, offset=0, size=len(initcode))
        + Op.STOP,
        balance=RUNNER_BALANCE,
    )

    # Deployed contracts start at nonce 1.
    created = compute_create_address(
        address=runner, nonce=1, initcode=initcode, opcode=create_opcode
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=runner,
    )

    post = {
        created: Account(
            # The init code deploys no code but writes its own storage.
            code=b"",
            nonce=1,
            balance=CREATE_ENDOWMENT,
            storage={
                DELEGATE_RESULT_SLOT: 1,
                INITCODE_CALLER_SLOT: runner,
                DELEGATE_WRITE_SLOT: 1,
                DELEGATE_CALLER_SLOT: runner,
                DELEGATE_VALUE_SLOT: CREATE_ENDOWMENT,
            },
        ),
        runner: Account(
            nonce=2,
            balance=RUNNER_BALANCE - CREATE_ENDOWMENT,
            storage={},
        ),
        # The delegate's own storage must stay untouched.
        existing: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
