"""Test execution of EOF creation txs."""

import pytest

from ethereum_test_base_types.base_types import Address
from ethereum_test_tools import Account, Alloc, Environment, Initcode, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.helpers import compute_create_address
from ethereum_test_vm.bytecode import Bytecode

from .. import EOF_FORK_NAME
from .helpers import slot_call_result, smallest_runtime_subcontainer

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7698.md"
REFERENCE_SPEC_VERSION = "ff544c14889aeb84be214546a09f410a67b919be"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    ["destination_code", "expected_result"],
    [
        pytest.param(Op.ADDRESS, "destination"),
        pytest.param(Op.CALLER, "sender"),
        pytest.param(Op.CALLVALUE, "value"),
        pytest.param(Op.ORIGIN, "sender"),
    ],
)
def test_eof_creation_tx_context(
    state_test: StateTestFiller,
    pre: Alloc,
    destination_code: Bytecode,
    expected_result: str,
):
    """Test EOF creation txs' initcode context instructions."""
    env = Environment()
    sender = pre.fund_eoa()
    value = 0x1123

    initcode = Container(
        sections=[
            Section.Code(
                Op.SSTORE(slot_call_result, destination_code) + Op.RETURNCONTRACT[0](0, 0)
            ),
            Section.Container(smallest_runtime_subcontainer),
        ]
    )

    destination_contract_address = compute_create_address(address=sender, nonce=sender.nonce)

    tx = Transaction(sender=sender, to=None, gas_limit=100000, value=value, input=initcode)

    expected_bytes: Address | int
    if expected_result == "destination":
        expected_bytes = destination_contract_address
    elif expected_result == "sender":
        expected_bytes = sender
    elif expected_result == "value":
        expected_bytes = value
    else:
        raise TypeError("Unexpected expected_result", expected_result)

    destination_contract_storage = {
        slot_call_result: expected_bytes,
    }

    post = {
        destination_contract_address: Account(storage=destination_contract_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


def test_lecacy_cannot_create_eof(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test that a legacy contract creation initcode cannot deploy an EOF contract."""
    env = Environment()
    sender = pre.fund_eoa()

    initcode = Initcode(deploy_code=smallest_runtime_subcontainer)

    destination_contract_address = compute_create_address(address=sender, nonce=sender.nonce)

    tx = Transaction(sender=sender, to=None, gas_limit=100000, data=initcode)

    post = {
        destination_contract_address: Account.NONEXISTENT,
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
