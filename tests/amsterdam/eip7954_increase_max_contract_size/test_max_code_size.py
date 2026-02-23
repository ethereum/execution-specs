"""
Test [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_from("Amsterdam")

CREATE2_SALT = 0xC0FFEE

DEPLOY_CODE_SIZE_PARAMS = [
    pytest.param(lambda f: f.parent().max_code_size(), id="prev_max"),
    pytest.param(lambda f: f.max_code_size(), id="at_max"),
    pytest.param(lambda f: f.max_code_size() + 1, id="over_max"),
]


@pytest.mark.parametrize("deploy_code_size", DEPLOY_CODE_SIZE_PARAMS)
def test_deploy_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    deploy_code_size,
) -> None:
    """Ensure the new max code size boundary is enforced."""
    code_size = deploy_code_size(fork)
    deploy_code = Op.JUMPDEST * code_size

    sender = pre.fund_eoa()
    initcode = Initcode(deploy_code=deploy_code)
    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    if code_size <= fork.max_code_size():
        post = {create_address: Account(code=deploy_code)}
    else:
        post = {create_address: Account.NONEXISTENT}

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("deploy_code_size", DEPLOY_CODE_SIZE_PARAMS)
@pytest.mark.with_all_create_opcodes()
def test_create_opcode_deploy_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    deploy_code_size,
    create_opcode,
) -> None:
    """Ensure the new max code size boundary is enforced via create opcodes."""
    code_size = deploy_code_size(fork)
    deploy_code = Op.JUMPDEST * code_size
    initcode = Initcode(deploy_code=deploy_code)
    initcode_bytes = bytes(initcode)

    sender = pre.fund_eoa()

    # Extra kwargs for CREATE2 (salt); empty for CREATE
    extra_create_kwargs = (
        {"salt": CREATE2_SALT} if create_opcode == Op.CREATE2 else {}
    )

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            0,
            create_opcode(
                value=0, offset=0, size=Op.CALLDATASIZE, **extra_create_kwargs
            ),
        )
        + Op.STOP
    )

    factory = pre.deploy_contract(factory_code)

    create_address = (
        compute_create2_address(
            address=factory, salt=CREATE2_SALT, initcode=initcode
        )
        if create_opcode == Op.CREATE2
        else compute_create_address(address=factory, nonce=1)
    )

    tx = Transaction(
        sender=sender,
        to=factory,
        data=initcode_bytes,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = (
        {create_address: Account(code=deploy_code)}
        if code_size <= fork.max_code_size()
        else {create_address: Account.NONEXISTENT}
    )

    state_test(pre=pre, tx=tx, post=post)
