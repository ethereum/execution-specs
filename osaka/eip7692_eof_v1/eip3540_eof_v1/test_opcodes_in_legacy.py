"""
Tests all EOF-only opcodes in legacy contracts and expects failure.
"""
import pytest

from ethereum_test_base_types import Account
from ethereum_test_specs import StateTestFiller
from ethereum_test_tools import Initcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_types import Alloc, Environment, Transaction
from ethereum_test_vm import Opcodes

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7692.md"
REFERENCE_SPEC_VERSION = "f0e7661ee0d16e612e0931ec88b4c9f208e9d513"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

slot_code_executed = b"EXEC"
slot_code_worked = b"WORK"
slot_create_address = b"ADDR"

value_code_executed = b"exec"
value_code_worked = b"work"
value_non_execution_canary = b"brid"
value_create_failed = 0

eof_opcode_blocks = [
    pytest.param(Op.PUSH0 + Op.DUPN[0], id="DUPN"),
    pytest.param(Op.PUSH0 + Op.PUSH0 + Op.SWAPN[0], id="SWAPN"),
    pytest.param(Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.EXCHANGE[2, 3], id="EXCHANGE"),
    pytest.param(Op.RJUMP[0], id="RJUMP"),
    pytest.param(Op.PUSH0 + Op.RJUMPI[0], id="RJUMPI"),
    pytest.param(Op.PUSH0 + Op.RJUMPV[0, 0], id="RJUMPI"),
    pytest.param(Op.CALLF[1], id="CALLF"),
    pytest.param(Op.RETF, id="RETF"),
    pytest.param(Op.JUMPF[0], id="JUMPF"),
    pytest.param(Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH1(2) + Op.EXTCALL, id="EXTCALL"),
    pytest.param(
        Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH1(2) + Op.EXTDELEGATECALL, id="EXTDELEGATECALL"
    ),
    pytest.param(
        Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH1(2) + Op.EXTSTATICCALL, id="EXTSTATICCALL"
    ),
    pytest.param(Op.DATALOAD(0), id="DATALOAD"),
    pytest.param(Op.DATALOADN[0], id="DATALOADN"),
    pytest.param(Op.DATASIZE, id="DATASIZE"),
    pytest.param(Op.DATACOPY(0, 0, 32), id="DATACOPY"),
    pytest.param(Op.EOFCREATE[0](0, 0, 0, 0), id="EOFCREATE"),
    pytest.param(Op.RETURNCONTRACT[0], id="RETURNCONTRACT"),
]


@pytest.mark.parametrize(
    "code",
    eof_opcode_blocks,
)
def test_opcodes_in_legacy(state_test: StateTestFiller, pre: Alloc, code: Opcodes):
    """
    Test all EOF only opcodes in legacy contracts and expects failure.
    """
    env = Environment()

    address_test_contract = pre.deploy_contract(
        code=code + Op.SSTORE(slot_code_executed, value_code_executed),
        storage={slot_code_executed: value_non_execution_canary},
    )

    post = {
        # assert the canary is not over-written. If it was written then the EOF opcode was valid
        address_test_contract: Account(storage={slot_code_executed: value_non_execution_canary}),
    }

    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=address_test_contract,
        gas_limit=5_000_000,
        gas_price=10,
        protected=False,
        data="",
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "code",
    eof_opcode_blocks,
)
def test_opcodes_in_create_tx(state_test: StateTestFiller, pre: Alloc, code: Opcodes):
    """
    Test all EOF only opcodes in legacy contracts and expects failure.
    """
    env = Environment()

    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=5_000_000,
        gas_price=10,
        protected=False,
        data=code,
    )

    post = {
        # Should revert in initcode, which results in no contract created
        tx.created_contract: Account.NONEXISTENT
    }

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
    "code",
    eof_opcode_blocks,
)
def test_opcodes_in_create_operation(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Opcodes,
    legacy_create_opcode: Opcodes,
):
    """
    Test all EOF only opcodes in legacy contracts and expects failure.
    """
    env = Environment()

    init_code = Initcode(initcode_prefix=code, deploy_code=Op.RETURN(0, 0))
    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(slot_create_address, legacy_create_opcode(size=Op.CALLDATASIZE))
        + Op.SSTORE(slot_code_worked, value_code_worked)
    )

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(code=factory_code)

    post = {
        contract_address: Account(
            storage={slot_create_address: value_create_failed, slot_code_worked: value_code_worked}
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


@pytest.mark.parametrize(
    ("ext_call_opcode"),
    [
        pytest.param(Op.EXTCALL, id="EXTCALL"),
        pytest.param(Op.EXTDELEGATECALL, id="EXTDELEGATECALL"),
        pytest.param(Op.EXTSTATICCALL, id="EXTSTATICCALL"),
    ],
)
@pytest.mark.parametrize(
    "code",
    eof_opcode_blocks,
)
def test_opcodes_in_eof_calling_legacy(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Opcodes,
    ext_call_opcode: Op,
):
    """
    Test all EOF only opcodes in legacy contracts and expects failure.
    """
    env = Environment()

    address_test_contract = pre.deploy_contract(
        code=code + Op.SSTORE(slot_code_executed, value_code_executed),
        storage={slot_code_executed: value_non_execution_canary},
    )

    address_entry_contract = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    ext_call_opcode(address=address_test_contract)
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                )
            ]
        ),
        storage={slot_code_executed: value_non_execution_canary},
    )

    post = {
        # assert the canary is not over-written. If it was written then the EOF opcode was valid
        address_test_contract: Account(storage={slot_code_executed: value_non_execution_canary}),
        address_entry_contract: Account(
            storage={
                slot_code_executed: value_non_execution_canary,
                slot_code_worked: value_code_worked,
            }
        ),
    }

    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=address_entry_contract,
        gas_limit=5_000_000,
        gas_price=10,
        protected=False,
        data="",
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
