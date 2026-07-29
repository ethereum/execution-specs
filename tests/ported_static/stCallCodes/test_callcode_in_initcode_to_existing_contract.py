"""
Verify a CALLCODE made from inside init code to an existing contract.

The created account's init code CALLCODEs an already-deployed contract,
so that contract's code runs in the freshly created account's context:
its storage write lands in the created account (never in the existing
contract), and the transferred value stays with the created account.

Ported from:
state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json

@manually-enhanced: Do not overwrite. The calldata-dispatch entry
contract is collapsed into a direct transaction to the create-runner,
the init code is composed and shared with the CREATE2 address
computation, sub-calls forward all gas (EIP-8037-proof), and the post
also pins the created account's code/nonce/balance and that the
existing contract's own storage stays untouched.
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
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Endowment the runner sends into the creation; the init code's CALLCODE
# then names the same amount, a self-to-self transfer the created
# account's balance must cover and keep.
CREATE_ENDOWMENT = 1
CALLCODE_VALUE = CREATE_ENDOWMENT
RUNNER_BALANCE = 10_000
CREATE2_SALT = 0

# Written by the init code with the CALLCODE's success flag.
SUCCESS_FLAG_SLOT = 1
# Written by the existing contract's code, in the caller's context.
DELEGATE_SLOT = 2


def memory_stores(data: bytes) -> Bytecode:
    """Write the given bytes to memory starting at offset zero."""
    code = Bytecode()
    for offset in range(0, len(data), 32):
        chunk = data[offset : offset + 32].ljust(32, b"\x00")
        code += Op.MSTORE(offset, int.from_bytes(chunk, "big"))
    return code


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
def test_callcode_in_initcode_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Opcode,
) -> None:
    """A CALLCODE in init code runs in the created account's context."""
    existing = pre.deploy_contract(
        code=Op.SSTORE(key=DELEGATE_SLOT, value=1) + Op.STOP,
    )

    initcode = (
        Op.SSTORE(
            key=SUCCESS_FLAG_SLOT,
            value=Op.CALLCODE(address=existing, value=CALLCODE_VALUE),
        )
        + Op.STOP
    )
    initcode_bytes = bytes(initcode)

    if opcode == Op.CREATE2:
        create_call = Op.CREATE2(
            value=CREATE_ENDOWMENT,
            offset=0,
            size=len(initcode_bytes),
            salt=CREATE2_SALT,
        )
    else:
        create_call = Op.CREATE(
            value=CREATE_ENDOWMENT, offset=0, size=len(initcode_bytes)
        )
    runner = pre.deploy_contract(
        code=memory_stores(initcode_bytes) + create_call + Op.STOP,
        balance=RUNNER_BALANCE,
    )

    if opcode == Op.CREATE2:
        created = compute_create_address(
            address=runner,
            salt=CREATE2_SALT,
            initcode=initcode,
            opcode=Op.CREATE2,
        )
    else:
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
            storage={SUCCESS_FLAG_SLOT: 1, DELEGATE_SLOT: 1},
        ),
        runner: Account(
            nonce=2,
            balance=RUNNER_BALANCE - CREATE_ENDOWMENT,
            storage={},
        ),
        # The existing contract's own storage must stay untouched.
        existing: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
