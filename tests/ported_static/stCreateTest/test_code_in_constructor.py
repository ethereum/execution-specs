"""
Inspect PC, ADDRESS, CODESIZE and code copies from inside a constructor.

Ported from:
state_tests/stCreateTest/CodeInConstructorFiller.yml
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

BUFFER_LENGTH = 0x200
DATA_LOCATION = 0x460


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CodeInConstructorFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [pytest.param(Op.CREATE, id="d0"), pytest.param(Op.CREATE2, id="d1")],
)
def test_code_in_constructor(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """Inspect PC, ADDRESS, CODESIZE and code copies in a constructor."""
    sender = pre.fund_eoa()
    salt = 0x5A17

    # Source: lll
    # {
    #     (def 'counterLoc 0)
    #     (def 'counterVal @@counterLoc)
    #     [[counterVal]] $0
    #     [[counterLoc]] (+ counterVal 1)
    # }
    logger = pre.deploy_contract(
        code=Op.SSTORE(
            key=Op.SLOAD(key=0x0), value=Op.CALLDATALOAD(offset=0x0)
        )
        + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STOP,
        storage={0: 1},
    )

    def send_data(value: Bytecode | int) -> Bytecode:
        return Op.MSTORE(offset=DATA_LOCATION, value=value) + Op.POP(
            Op.CALL(address=logger, args_offset=DATA_LOCATION, args_size=0x20)
        )

    contract_code = Op.SSTORE(key=0x0, value=0xFF) + Op.STOP

    copy_contract = Op.CODECOPY(
        dest_offset=BUFFER_LENGTH, offset=BUFFER_LENGTH, size=BUFFER_LENGTH
    )
    before_last_pc = (
        copy_contract
        + send_data(Op.PC)
        + send_data(Op.ADDRESS)
        + send_data(Op.CODESIZE)
        + send_data(Op.EXTCODESIZE(address=Op.ADDRESS))
        + Op.CODECOPY(dest_offset=BUFFER_LENGTH, offset=0x0, size=0x20)
        + send_data(Op.MLOAD(offset=BUFFER_LENGTH))
        + Op.EXTCODECOPY(
            address=Op.ADDRESS, dest_offset=BUFFER_LENGTH, offset=0, size=0x20
        )
        + send_data(Op.MLOAD(offset=BUFFER_LENGTH))
    )
    constructor = (
        before_last_pc
        + send_data(Op.PC)
        + Op.RETURN(
            offset=BUFFER_LENGTH, size=Op.SUB(Op.CODESIZE, BUFFER_LENGTH)
        )
        + Op.STOP
    )
    assert len(constructor) <= BUFFER_LENGTH
    initcode = bytes(constructor).ljust(BUFFER_LENGTH, b"\0") + bytes(
        contract_code
    )

    def creator_code(initcode_offset: int) -> Bytecode:
        copy = Op.CODECOPY(
            dest_offset=0, offset=initcode_offset, size=len(initcode)
        )
        if opcode == Op.CREATE2:
            create = Op.CREATE2(
                value=0, offset=0, size=len(initcode), salt=salt
            )
        else:
            create = Op.CREATE(value=0, offset=0, size=len(initcode))
        return copy + Op.POP(create) + Op.STOP

    initcode_offset = len(creator_code(0))
    creator = pre.deploy_contract(
        code=bytes(creator_code(initcode_offset)) + initcode
    )
    created = compute_create_address(
        address=creator, nonce=1, salt=salt, initcode=initcode, opcode=opcode
    )

    post = {
        logger: Account(
            storage={
                0: 8,
                1: len(copy_contract),
                2: created,
                3: len(initcode),
                4: 0,
                5: int.from_bytes(initcode[:0x20], "big"),
                6: 0,
                7: len(before_last_pc),
            },
        ),
        created: Account(code=bytes(len(contract_code))),
    }

    tx = Transaction(sender=sender, to=creator)

    state_test(pre=pre, post=post, tx=tx)
