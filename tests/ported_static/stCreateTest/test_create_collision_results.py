"""
Check the results of CREATE and CREATE2 colliding with existing contracts.

Ported from:
state_tests/stCreateTest/CreateCollisionResultsFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

UNTOUCHED = 0x60A7


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateCollisionResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "use_create",
    [pytest.param(True, id="d0"), pytest.param(False, id="d1")],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_results(
    state_test: StateTestFiller,
    pre: Alloc,
    use_create: bool,
) -> None:
    """Check results of CREATE and CREATE2 colliding with contracts."""
    sender = pre.fund_eoa()
    salt = 0x5A17
    collider_code = Op.SSTORE(key=0x0, value=0x1D) + Op.STOP
    initcode = Op.MSTORE8(offset=0, value=0) + Op.RETURN(offset=0, size=1)

    create_collider = Op.CALLDATALOAD(offset=0x20)
    create2_collider = Op.CALLDATALOAD(offset=0x40)
    create_and_store = Conditional(
        condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 1),
        if_true=Op.MSTORE(
            offset=0x600,
            value=Op.CREATE(value=0, offset=0x300, size=len(initcode)),
        ),
        if_false=Op.MSTORE(
            offset=0x600,
            value=Op.CREATE2(
                value=0, offset=0x300, size=len(initcode), salt=salt
            ),
        ),
    )

    def creator_code(initcode_offset: int) -> list[Bytecode]:
        return [
            Op.CODECOPY(
                dest_offset=0x300, offset=initcode_offset, size=len(initcode)
            )
            + create_and_store,
            Op.SSTORE(key=0x20, value=Op.PC)
            + Op.SSTORE(key=0x10, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x11, value=Op.MLOAD(offset=0x600))
            + Op.MSTORE(offset=0x640, value=Op.CALL(address=create_collider)),
            Op.SSTORE(key=0x21, value=Op.PC)
            + Op.SSTORE(key=0x12, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
            + Op.SSTORE(key=0x13, value=Op.RETURNDATASIZE)
            + Op.MSTORE(offset=0x640, value=Op.CALL(address=create2_collider)),
            Op.SSTORE(key=0x22, value=Op.PC)
            + Op.SSTORE(key=0x14, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
            + Op.SSTORE(key=0x15, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x30, value=Op.EXTCODESIZE(create_collider))
            + Op.EXTCODECOPY(
                address=create_collider,
                dest_offset=0x660,
                offset=0x0,
                size=Op.SLOAD(key=0x30),
            )
            + Op.SSTORE(key=0x31, value=Op.MLOAD(offset=0x660))
            + Op.SSTORE(key=0x32, value=Op.EXTCODESIZE(create2_collider))
            + Op.EXTCODECOPY(
                address=create2_collider,
                dest_offset=0x660,
                offset=0x0,
                size=Op.SLOAD(key=0x32),
            )
            + Op.SSTORE(key=0x33, value=Op.MLOAD(offset=0x660))
            + Op.STOP,
        ]

    pieces = creator_code(0)
    pieces = creator_code(sum(len(piece) for piece in pieces))
    creator = pre.deploy_contract(
        code=sum(pieces, Bytecode()) + initcode,
        storage=dict.fromkeys(
            (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x20, 0x21, 0x22), UNTOUCHED
        ),
    )

    colliders = [
        compute_create_address(address=creator, nonce=1),
        compute_create_address(
            address=creator, salt=salt, initcode=initcode, opcode=Op.CREATE2
        ),
    ]
    for collider in colliders:
        pre.deploy_contract(
            code=collider_code, storage={0: UNTOUCHED}, address=collider
        )

    tx = Transaction(
        sender=sender,
        to=creator,
        data=Hash(1 if use_create else 2)
        + Hash(colliders[0], left_padding=True)
        + Hash(colliders[1], left_padding=True),
    )

    collider_word = int.from_bytes(bytes(collider_code).ljust(32, b"\0"))
    post = {
        creator: Account(
            storage={
                0x20: len(pieces[0]),
                0x21: len(pieces[0]) + len(pieces[1]),
                0x22: len(pieces[0]) + len(pieces[1]) + len(pieces[2]),
                0x30: len(collider_code),
                0x31: collider_word,
                0x32: len(collider_code),
                0x33: collider_word,
            },
            nonce=2,
        ),
    }
    for collider in colliders:
        post[collider] = Account(storage={0: 0x1D}, code=collider_code)

    state_test(pre=pre, post=post, tx=tx)
