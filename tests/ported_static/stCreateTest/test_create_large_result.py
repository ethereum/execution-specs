"""
Return or revert results at and around the code size limit from CREATE(2).

Ported from:
state_tests/stCreateTest/createLargeResultFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
    keccak256,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

UNTOUCHED = 0x60A7


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/createLargeResultFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("ending", [Op.RETURN, Op.REVERT])
@pytest.mark.parametrize("size", ["small", "max", "too_big", "huge"])
def test_create_large_result(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    ending: Op,
    size: str,
) -> None:
    """Return or revert results around the code size limit."""
    sender = pre.fund_eoa()
    salt = 0x5A17
    result_size = {
        "small": 0x100,
        "max": fork.max_code_size(),
        "too_big": fork.max_code_size() + 1,
        "huge": fork.max_initcode_size(),
    }[size]

    initcode = Op.MSTORE(offset=0, value=Op.NOT(0)) + ending(
        offset=0, size=result_size
    )
    if opcode == Op.CREATE2:
        create = Op.CREATE2(value=0, offset=0, size=len(initcode), salt=salt)
    else:
        create = Op.CREATE(value=0, offset=0, size=len(initcode))
    deployed = ending == Op.RETURN and result_size <= fork.max_code_size()

    # slot 1: whether more than half of the gas is left after the CREATE,
    # i.e. the init code did not halt exceptionally.
    code: Bytecode = (
        Op.MSTORE(
            offset=0,
            value=int.from_bytes(bytes(initcode).ljust(32, b"\0"), "big"),
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.MSTORE(offset=0x40, value=create)
        + Op.SSTORE(
            key=1, value=Op.GT(Op.MUL(Op.GAS, 2), Op.MLOAD(offset=0x20))
        )
        + Op.SSTORE(key=0, value=Op.MLOAD(offset=0x40))
    )
    if deployed:
        code += Op.SSTORE(key=2, value=Op.EXTCODEHASH(Op.MLOAD(offset=0x40)))
    creator = pre.deploy_contract(
        code=code + Op.STOP, storage={0: UNTOUCHED, 1: UNTOUCHED}
    )
    created = compute_create_address(
        address=creator, nonce=1, salt=salt, initcode=initcode, opcode=opcode
    )

    tx = Transaction(sender=sender, to=creator)

    halted = ending == Op.RETURN and not deployed
    post: dict
    if deployed:
        created_code = (b"\xff" * 32).ljust(result_size, b"\0")
        post = {
            creator: Account(
                storage={0: created, 1: 1, 2: keccak256(created_code)},
                nonce=2,
            ),
            created: Account(code=created_code, nonce=1),
        }
    else:
        post = {
            creator: Account(storage={0: 0, 1: 0 if halted else 1}, nonce=2),
            created: Account.NONEXISTENT,
        }

    state_test(pre=pre, post=post, tx=tx)
