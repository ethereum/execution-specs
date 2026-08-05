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
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

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


def memory_stores(data: bytes) -> Bytecode:
    """Write the given bytes to memory starting at offset zero."""
    code = Bytecode()
    for offset in range(0, len(data), 32):
        chunk = data[offset : offset + 32].ljust(32, b"\x00")
        code += Op.MSTORE(offset, int.from_bytes(chunk, "big"))
    return code


@pytest.mark.ported_from(
    [
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("SpuriousDragon")
def test_delegatecall_in_initcode_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A DELEGATECALL in init code runs in the created account."""
    existing = pre.deploy_contract(
        code=Op.SSTORE(key=DELEGATE_WRITE_SLOT, value=1)
        + Op.SSTORE(key=DELEGATE_CALLER_SLOT, value=Op.CALLER)
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
    initcode_bytes = bytes(initcode)

    runner = pre.deploy_contract(
        code=memory_stores(initcode_bytes)
        + Op.CREATE(value=CREATE_ENDOWMENT, offset=0, size=len(initcode_bytes))
        + Op.STOP,
        balance=RUNNER_BALANCE,
    )

    # Deployed contracts start at nonce 1.
    created = compute_create_address(address=runner, nonce=1)

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
