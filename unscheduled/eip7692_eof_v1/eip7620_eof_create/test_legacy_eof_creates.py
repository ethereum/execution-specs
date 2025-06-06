"""Test interactions between CREATE, CREATE2, and EOFCREATE."""

import pytest

from ethereum_test_base_types.base_types import Address, Bytes
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Initcode as LegacyInitcode
from ethereum_test_tools.vm.opcode import Opcodes
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import Container
from ethereum_test_types.helpers import compute_create_address
from tests.prague.eip7702_set_code_tx.spec import Spec

from .. import EOF_FORK_NAME
from .helpers import (
    slot_all_subcall_gas_gone,
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
    "initcode",
    [
        Bytes("0xEF00"),
        Bytes("0xEF0001"),
        pytest.param(smallest_initcode_subcontainer, id="deploy_eof_initcontainer"),
        pytest.param(smallest_runtime_subcontainer, id="deploy_eof_container"),
    ],
)
def test_cross_version_creates_fail_light(
    state_test: StateTestFiller,
    pre: Alloc,
    legacy_create_opcode: Opcodes,
    initcode: Bytes | Container,
):
    """Verifies that CREATE and CREATE2 cannot run EOF initcodes and fail early on attempt."""
    env = Environment()

    sender = pre.fund_eoa()

    tx_gas_limit = 10_000_000

    contract_address = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(slot_create_address, legacy_create_opcode(size=Op.CALLDATASIZE))
        # Approximates whether code until here consumed the 63/64th gas given to subcall
        + Op.SSTORE(slot_all_subcall_gas_gone, Op.LT(Op.GAS, tx_gas_limit // 64))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP
    )

    post = {
        contract_address: Account(
            storage={
                slot_create_address: EOFCREATE_FAILURE,
                slot_code_worked: value_code_worked,
                slot_all_subcall_gas_gone: 0,
            },
            nonce=1,
        ),
        # Double check no accounts were created
        compute_create_address(address=contract_address, nonce=1): Account.NONEXISTENT,
        compute_create_address(
            address=contract_address, initcode=initcode, salt=0, opcode=Op.CREATE2
        ): Account.NONEXISTENT,
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=tx_gas_limit,
        sender=sender,
        data=initcode,
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
    "initcode",
    [
        Bytes("0xEF"),
        Bytes("0xEF01"),
        Bytes("0xEF0101"),
        Spec.delegation_designation(Address(0xAA)),
        Bytes("0xEF02"),
    ],
)
def test_cross_version_creates_fail_hard(
    state_test: StateTestFiller,
    pre: Alloc,
    legacy_create_opcode: Opcodes,
    initcode: Bytes,
):
    """
    Verifies that CREATE and CREATE2 fail hard on attempt to run initcode starting with `EF` but
    not `EF00`.
    """
    env = Environment()

    sender = pre.fund_eoa()

    tx_gas_limit = 10_000_000

    contract_address = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(slot_create_address, legacy_create_opcode(size=Op.CALLDATASIZE))
        # Approximates whether code until here consumed the 63/64th gas given to subcall
        + Op.SSTORE(slot_all_subcall_gas_gone, Op.LT(Op.GAS, tx_gas_limit // 64))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP
    )

    post = {
        contract_address: Account(
            storage={
                slot_create_address: EOFCREATE_FAILURE,
                slot_code_worked: value_code_worked,
                slot_all_subcall_gas_gone: 1,
            },
            nonce=2,
        ),
        # Double check no accounts were created
        compute_create_address(address=contract_address, nonce=1): Account.NONEXISTENT,
        compute_create_address(
            address=contract_address, initcode=initcode, salt=0, opcode=Op.CREATE2
        ): Account.NONEXISTENT,
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=tx_gas_limit,
        sender=sender,
        data=initcode,
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
        Bytes("0xEF"),
        Bytes("0xEF00"),
        Bytes("0xEF0001"),
        Bytes("0xEF01"),
        pytest.param(smallest_initcode_subcontainer, id="deploy_eof_initcontainer"),
        pytest.param(smallest_runtime_subcontainer, id="deploy_eof_container"),
    ],
)
def test_legacy_initcode_eof_contract_fails(
    state_test: StateTestFiller,
    pre: Alloc,
    legacy_create_opcode: Opcodes,
    deploy_code: Bytes | Container,
):
    """
    Verifies that legacy initcode cannot create EOF.

    This tests only ensures EIP-3541 behavior is kept, not altered by EIP-7620.
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
        data=init_code,
        sender=sender,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
