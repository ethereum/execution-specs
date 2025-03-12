"""Tests interaction between edge case size CREATE / CREATE2 and EOF, including EIP-3860 limits."""

import itertools

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Bytecode,
    Environment,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1.constants import MAX_BYTECODE_SIZE, MAX_INITCODE_SIZE

from .spec import ref_spec_3860

REFERENCE_SPEC_GIT_PATH = ref_spec_3860.git_path
REFERENCE_SPEC_VERSION = ref_spec_3860.version

pytestmark = pytest.mark.valid_from("Shanghai")

_slot = itertools.count()
next(_slot)  # don't use slot 0
slot_code_worked = next(_slot)
slot_create_address = next(_slot)
value_code_worked = 0x2015


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CREATE,
        Op.CREATE2,
    ],
)
@pytest.mark.parametrize(
    "init_code",
    [
        pytest.param(Bytecode(), id="empty_initcode"),
        pytest.param(Initcode(initcode_length=MAX_INITCODE_SIZE), id="max_initcode"),
        pytest.param(Initcode(deploy_code=Bytecode()), id="empty_code"),
        pytest.param(Initcode(deploy_code=Op.STOP * MAX_BYTECODE_SIZE), id="max_code"),
    ],
)
def test_legacy_create_edge_code_size(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    init_code: Bytecode,
):
    """
    Verifies that legacy initcode/deploycode having 0 or max size continues to work in the fork
    where EOF is enabled. Handling of EOF magic prefix and version interferes with the handling
    of legacy creation, so a specific test was proposed to test behavior doesn't change.
    """
    env = Environment()

    salt_param = [0] if opcode == Op.CREATE2 else []
    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(slot_create_address, opcode(0, 0, Op.CALLDATASIZE, *salt_param))
        + Op.SSTORE(slot_code_worked, value_code_worked)
    )

    contract_address = pre.deploy_contract(code=factory_code)

    new_address = compute_create_address(
        address=contract_address, initcode=init_code, nonce=1, opcode=opcode
    )

    post = {
        contract_address: Account(
            storage={slot_create_address: new_address, slot_code_worked: value_code_worked}
        )
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        data=init_code,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
