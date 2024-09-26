"""
Test interactions between CREATE, CREATE2, and EOFCREATE
"""


import pytest

from ethereum_test_tools import Account, Alloc, Environment
from ethereum_test_tools import Initcode as LegacyInitcode
from ethereum_test_tools import StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container
from ethereum_test_tools.vm.opcode import Opcodes
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import (
    slot_code_worked,
    slot_create_address,
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
    value_code_worked,
)
from .spec import EOFCREATE_FAILURE

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "52ddbcdddcf72dd72427c319f2beddeb468e1737"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "legacy_create_opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(Op.CREATE2, id="CREATE2"),
    ],
)
@pytest.mark.parametrize(
    "deploy_code",
    [
        pytest.param(smallest_initcode_subcontainer, id="deploy_eof_initcontainer"),
        pytest.param(smallest_runtime_subcontainer, id="deploy_eof_container"),
    ],
)
def test_cross_version_creates_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    legacy_create_opcode: Opcodes,
    deploy_code: Container,
):
    """
    Verifies that CREATE and CREATE2 cannot create EOF contracts
    """
    env = Environment()
    salt_param = [0] if legacy_create_opcode == Op.CREATE2 else []
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(slot_create_address, legacy_create_opcode(0, 0, Op.CALLDATASIZE, *salt_param))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP
    )

    # Storage in 0 should be empty as the create/create2 should fail,
    # and 1 in 1 to show execution continued and did not halt
    post = {
        contract_address: Account(
            storage={
                slot_create_address: EOFCREATE_FAILURE,
                slot_code_worked: value_code_worked,
            }
        )
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
        data=deploy_code,
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "legacy_create_opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(Op.CREATE2, id="CREATE2"),
    ],
)
@pytest.mark.parametrize(
    "deploy_code",
    [
        pytest.param(smallest_initcode_subcontainer, id="deploy_eof_initcontainer"),
        pytest.param(smallest_runtime_subcontainer, id="deploy_eof_container"),
    ],
)
def test_legacy_initcode_eof_contract_fails(
    state_test: StateTestFiller,
    pre: Alloc,
    legacy_create_opcode: Opcodes,
    deploy_code: Container,
):
    """
    Verifies that legacy initcode cannot create EOF
    """
    env = Environment()
    init_code = LegacyInitcode(deploy_code=deploy_code)
    salt_param = [0] if legacy_create_opcode == Op.CREATE2 else []
    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(slot_create_address, legacy_create_opcode(0, 0, Op.CALLDATASIZE, *salt_param))
        + Op.SSTORE(slot_code_worked, value_code_worked)
    )

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(code=factory_code)

    # Storage in 0 should be empty as the final CREATE filed
    # and 1 in 1 to show execution continued and did not halt
    post = {
        contract_address: Account(
            storage={slot_create_address: EOFCREATE_FAILURE, slot_code_worked: value_code_worked}
        )
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        gas_price=10,
        protected=False,
        data=init_code,
        sender=sender,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
