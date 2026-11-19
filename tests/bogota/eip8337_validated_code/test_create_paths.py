"""
Validation runs on every creation path: CREATE and CREATE2 as well as
transaction initcode, and a failed validation costs only the child's gas.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .helpers import (
    SLOT_MARKER,
    SLOT_RESULT,
    TX_GAS_LIMIT,
    factory_code,
    magic,
)
from .spec import Spec, ref_spec_8337

REFERENCE_SPEC_GIT_PATH = ref_spec_8337.git_path
REFERENCE_SPEC_VERSION = ref_spec_8337.version

pytestmark = pytest.mark.valid_from("EIP8337")

VALID_BODY = Op.SSTORE(1, 1) + Op.STOP
INVALID_BODY = Op.POP + Op.STOP  # underflows


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "body,valid",
    [
        pytest.param(VALID_BODY, True, id="valid"),
        pytest.param(INVALID_BODY, False, id="invalid"),
    ],
)
def test_create_opcodes_validate(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    body: Op,
    valid: bool,
) -> None:
    """
    CREATE/CREATE2 of MAGIC code succeeds iff the code validates. A failed
    validation is an exceptional halt of the child frame: the factory gets
    0 and keeps its own gas.
    """
    code = magic(body)
    initcode = Initcode(deploy_code=code)
    factory = pre.deploy_contract(factory_code(create_opcode, len(initcode)))
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        data=initcode,
        gas_limit=TX_GAS_LIMIT,
    )
    if create_opcode == Op.CREATE:
        created = compute_create_address(address=factory, nonce=1)
    else:
        created = compute_create_address(
            address=factory, initcode=initcode, salt=0, opcode=Op.CREATE2
        )
    post = {
        factory: Account(
            storage={
                SLOT_RESULT: created if valid else 0,
                SLOT_MARKER: 1,  # factory still holds gas after either
            }
        ),
        created: Account(code=code) if valid else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


def test_magic_initcode_gets_no_entry_point(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Only created code is validated and given an entry point. Initcode that
    begins with the MAGIC bytes is executed from position 0 like any other
    initcode, where 0xEF is an invalid opcode, so the creation fails.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=magic(Initcode(deploy_code=Op.STOP)),
        gas_limit=TX_GAS_LIMIT,
    )
    created = compute_create_address(address=sender, nonce=0)
    state_test(pre=pre, post={created: Account.NONEXISTENT}, tx=tx)


def test_validation_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Creating MAGIC code costs VALIDATION_BYTE_COST per byte of code more
    than creating plain code of the same length, and nothing else differs.
    """
    body = Op.SSTORE(1, 1) + Op.STOP
    plain = Op.JUMPDEST * Spec.HEADER_LENGTH + body
    validated = magic(body)
    assert len(plain) == len(validated)
    initcode_plain = Initcode(deploy_code=plain)
    initcode_magic = Initcode(deploy_code=validated)
    assert len(initcode_plain) == len(initcode_magic)
    size = len(initcode_plain)

    # Store the initcodes in memory, create each, and record the gas each
    # CREATE consumed; then store the difference.
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(offset=0, size=size)
        + Op.CALLDATACOPY(dest_offset=size, offset=size, size=size)
        + Op.GAS
        + Op.CREATE(offset=0, size=size)
        + Op.POP
        + Op.GAS
        + Op.SWAP1
        + Op.SUB  # gas used by the plain create
        + Op.GAS
        + Op.CREATE(offset=size, size=size)
        + Op.POP
        + Op.GAS
        + Op.SWAP1
        + Op.SUB  # gas used by the magic create
        + Op.SUB  # magic - plain
        + Op.PUSH1(SLOT_RESULT)
        + Op.SSTORE
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        data=bytes(initcode_plain) + bytes(initcode_magic),
        gas_limit=TX_GAS_LIMIT,
    )
    post = {
        factory: Account(
            storage={SLOT_RESULT: Spec.VALIDATION_BYTE_COST * len(validated)}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)
