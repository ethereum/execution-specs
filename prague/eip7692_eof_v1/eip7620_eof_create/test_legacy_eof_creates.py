"""
Test interactions between CREATE, CREATE2, and EOFCREATE
"""

from typing import SupportsBytes

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Initcode as LegacyInitcode
from ethereum_test_tools import StateTestFiller, TestAddress
from ethereum_test_tools.vm.opcode import Opcodes
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import (
    default_address,
    simple_transaction,
    slot_code_worked,
    slot_create_address,
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
    value_code_worked,
    value_create_failed,
)
from .spec import EOF_FORK_NAME

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
    legacy_create_opcode: Opcodes,
    deploy_code: SupportsBytes,
):
    """
    Verifies that CREATE and CREATE2 cannot create EOF contracts
    """
    env = Environment()
    salt_param = [0] if legacy_create_opcode == Op.CREATE2 else []
    pre = {
        TestAddress: Account(balance=10**21, nonce=1),
        default_address: Account(
            code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.SSTORE(
                slot_create_address, legacy_create_opcode(0, 0, Op.CALLDATASIZE, *salt_param)
            )
            + Op.SSTORE(slot_code_worked, value_code_worked)
            + Op.STOP
        ),
    }
    # Storage in 0 should be empty as the create/create2 should fail,
    # and 1 in 1 to show execution continued and did not halt
    post = {
        default_address: Account(
            storage={
                slot_create_address: value_create_failed,
                slot_code_worked: value_code_worked,
            }
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=simple_transaction(payload=bytes(deploy_code)),
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
    legacy_create_opcode: Opcodes,
    deploy_code: SupportsBytes,
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

    pre = {
        TestAddress: Account(balance=10**21, nonce=1),
        default_address: Account(code=factory_code),
    }
    # Storage in 0 should be empty as the final CREATE filed
    # and 1 in 1 to show execution continued and did not halt
    post = {
        default_address: Account(
            storage={slot_create_address: value_create_failed, slot_code_worked: value_code_worked}
        )
    }

    state_test(env=env, pre=pre, post=post, tx=simple_transaction(payload=bytes(init_code)))
