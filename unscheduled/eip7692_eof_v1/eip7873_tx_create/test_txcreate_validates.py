"""Test bad TXCREATE cases."""

from enum import Enum, auto, unique
from typing import Tuple

import pytest

from ethereum_test_base_types import Bytes
from ethereum_test_base_types.base_types import Address, Hash
from ethereum_test_base_types.composite_types import AccessList
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    EVMCodeType,
    StateTestFiller,
    Transaction,
    compute_eofcreate_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import Container, Section
from ethereum_test_vm.bytecode import Bytecode
from tests.prague.eip7702_set_code_tx.spec import Spec

from .. import EOF_FORK_NAME
from ..eip7620_eof_create.helpers import (
    slot_a,
    slot_b,
    slot_code_worked,
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
    value_code_worked,
)
from .spec import TXCREATE_FAILURE

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7873.md"
REFERENCE_SPEC_VERSION = "1115fe6110fcc0efc823fb7f8f5cd86c42173efe"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@unique
class ValidatedCode(Enum):
    """Kinds of valid/invalid EOF."""

    LEGACY = auto()
    EF = auto()
    EOFV1_RUNTIME = auto()
    EOFV1_RUNTIME_INVALID = auto()
    EOFV1_INITCODE = auto()
    EOFV2 = auto()
    DELEGATION = auto()
    SUBCONTAINER_INVALID = auto()

    def bytecode(self) -> Bytecode | Container | Bytes:
        """Bytecode for the code to validate."""
        match self:
            case ValidatedCode.LEGACY:
                return Op.STOP
            case ValidatedCode.EF:
                return Bytes("0xEF")
            case ValidatedCode.EOFV1_RUNTIME:
                return smallest_runtime_subcontainer
            case ValidatedCode.EOFV1_RUNTIME_INVALID:
                return Container.Code(Op.ADD)
            case ValidatedCode.EOFV1_INITCODE:
                return smallest_initcode_subcontainer
            case ValidatedCode.EOFV2:
                return Bytes("0xEF0002")
            case ValidatedCode.DELEGATION:
                return Bytes(Spec.DELEGATION_DESIGNATION + Bytes("".join(20 * ["ab"])))
            case ValidatedCode.SUBCONTAINER_INVALID:
                return Container(
                    sections=[
                        Section.Code(Op.RETURNCODE[0](0, 0)),
                        Section.Container(Container.Code(Op.ADD)),
                    ]
                )

    def valid(self) -> bool:
        """Whether the code is valid in EOF v1."""
        return self in [ValidatedCode.EOFV1_INITCODE]

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return f"{self.name}"


class Factory(Enum):
    """
    Kinds of systems leading up to a call to TXCREATE. DIRECT just puts the TXCREATE in the
    code it generates, while *CALL ones call into another account which does the TXCREATE.
    """

    DIRECT = auto()
    WITH_CALL = auto()
    WITH_DELEGATECALL = auto()
    WITH_STATICCALL = auto()

    def creation_snippet(
        self,
        initcode_hash: Hash,
        pre: Alloc,
        salt: int,
        evm_code_type: EVMCodeType,
        value: int,
        input_size: int,
    ) -> Tuple[Bytecode, Address | None]:
        """
        Return snippet to cause TXCREATE to be called along with an address which
        will end up in the `compute_eofcreate_address`, or None if that would be the snippet
        itself.
        """
        if evm_code_type not in [EVMCodeType.LEGACY, EVMCodeType.EOF_V1]:
            raise Exception(f"Test needs to be updated for {evm_code_type}")
        # Snippet which invokes the TXCREATE itself
        txcreate_code = Op.TXCREATE(
            tx_initcode_hash=initcode_hash, salt=salt, value=value, input_size=input_size
        )
        # Snippet which returns the TXCREATE result to caller
        callee_txcreate_code = Op.MSTORE(0, txcreate_code) + Op.RETURN(0, 32)
        # Snippet which recovers the TXCREATE result from returndata (wipes memory afterwards)
        returndataload_code = (
            Op.RETURNDATALOAD
            if evm_code_type == EVMCodeType.EOF_V1
            else Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE) + Op.MLOAD(0) + Op.MSTORE(0, 0)
        )
        match self:
            case Factory.DIRECT:
                return txcreate_code, None
            case Factory.WITH_CALL:
                callee_address = pre.deploy_contract(callee_txcreate_code)
                if evm_code_type == EVMCodeType.EOF_V1:
                    return Op.EXTCALL(address=callee_address) + returndataload_code, callee_address
                else:
                    return Op.CALL(address=callee_address) + returndataload_code, callee_address
            case Factory.WITH_DELEGATECALL:
                callee_address = pre.deploy_contract(callee_txcreate_code)
                if evm_code_type == EVMCodeType.EOF_V1:
                    return Op.EXTDELEGATECALL(address=callee_address) + returndataload_code, None
                else:
                    return Op.DELEGATECALL(address=callee_address) + returndataload_code, None
            case Factory.WITH_STATICCALL:
                callee_address = pre.deploy_contract(callee_txcreate_code)
                if evm_code_type == EVMCodeType.EOF_V1:
                    return Op.EXTSTATICCALL(address=callee_address) + returndataload_code, None
                else:
                    return Op.STATICCALL(address=callee_address) + returndataload_code, None

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return f"{self.name}"


@pytest.mark.with_all_evm_code_types
# Subset chosen to limit number of test cases
@pytest.mark.parametrize("code_a", [ValidatedCode.EOFV1_INITCODE, ValidatedCode.LEGACY])
@pytest.mark.parametrize("code_b", ValidatedCode)
# Subset chosen to limit number of test cases
@pytest.mark.parametrize("factory_a", [Factory.DIRECT, Factory.WITH_CALL])
@pytest.mark.parametrize("factory_b", Factory)
@pytest.mark.parametrize("value", [0, 1])
@pytest.mark.parametrize("input_size", [0, 31])
@pytest.mark.parametrize("access_list_a", [True, False])
def test_txcreate_validates(
    state_test: StateTestFiller,
    pre: Alloc,
    code_a: ValidatedCode,
    code_b: ValidatedCode,
    factory_a: Factory,
    factory_b: Factory,
    evm_code_type: EVMCodeType,
    value: int,
    input_size: int,
    access_list_a: bool,
):
    """
    Verifies proper validation of initcode on TXCREATE in various circumstances of the
    opcode.
    """
    env = Environment()
    snippet_a, factory_address_a = factory_a.creation_snippet(
        Bytes(code_a.bytecode()).keccak256(), pre, 0, evm_code_type, value, input_size
    )
    snippet_b, factory_address_b = factory_b.creation_snippet(
        Bytes(code_b.bytecode()).keccak256(), pre, 1, evm_code_type, value, input_size
    )

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=(
            Op.SSTORE(slot_code_worked, value_code_worked)
            + Op.SSTORE(slot_a, snippet_a)
            + Op.SSTORE(slot_b, snippet_b)
            + Op.STOP
        )
    )

    create_address_a = factory_address_a if factory_address_a else contract_address
    create_address_b = factory_address_b if factory_address_b else contract_address
    destination_address_a = compute_eofcreate_address(create_address_a, 0)
    destination_address_b = compute_eofcreate_address(create_address_b, 1)
    post = {
        contract_address: Account(
            storage={
                slot_a: destination_address_a
                if code_a.valid() and value == 0 and factory_a != Factory.WITH_STATICCALL
                else TXCREATE_FAILURE,
                slot_b: destination_address_b
                if code_b.valid() and value == 0 and factory_b != Factory.WITH_STATICCALL
                else TXCREATE_FAILURE,
                slot_code_worked: value_code_worked,
            }
        )
    }

    if access_list_a:
        access_list = [AccessList(address=destination_address_a, storage_keys=[Hash(0x0)])]
    else:
        access_list = []

    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        sender=sender,
        initcodes=[code_a.bytecode(), code_b.bytecode()],
        access_list=access_list,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)
