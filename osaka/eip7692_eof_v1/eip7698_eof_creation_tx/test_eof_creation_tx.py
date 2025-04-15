"""Test execution of EOF creation txs."""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Environment,
    Initcode,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types.eof.v1 import Container, ContainerKind, Section
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
        pytest.param(Op.SELFBALANCE, "selfbalance"),
        pytest.param(Op.BALANCE(Op.CALLER), "senderbalance"),
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
    initial_sender_balance = 123412341234
    gas_limit = 10000000
    gas_price = 10
    sender = pre.fund_eoa(amount=initial_sender_balance)
    value = 0x1123

    initcode = Container(
        sections=[
            Section.Code(Op.SSTORE(slot_call_result, destination_code) + Op.RETURNCODE[0](0, 0)),
            Section.Container(smallest_runtime_subcontainer),
        ]
    )

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=gas_limit,
        gas_price=gas_price,
        value=value,
        input=initcode,
    )

    destination_contract_address = tx.created_contract

    expected_bytes: Address | int
    if expected_result == "destination":
        expected_bytes = destination_contract_address
    elif expected_result == "sender":
        expected_bytes = sender
    elif expected_result == "value":
        expected_bytes = value
    elif expected_result == "selfbalance":
        expected_bytes = value
    elif expected_result == "senderbalance":
        expected_bytes = initial_sender_balance - gas_limit * gas_price - value
    else:
        raise TypeError("Unexpected expected_result", expected_result)

    destination_contract_storage = {
        slot_call_result: expected_bytes,
    }

    post = {
        destination_contract_address: Account(storage=destination_contract_storage, balance=value),
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

    tx = Transaction(sender=sender, to=None, gas_limit=100000, data=initcode)

    destination_contract_address = tx.created_contract

    post = {
        destination_contract_address: Account.NONEXISTENT,
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "reason",
    [
        "valid",
        "invalid_deploy_container",
        "invalid_initcode",
        "invalid_opcode_during_initcode",
        "invalid_opcode_with_sstore_during_initcode",
        "revert_opcode_during_initcode",
        "out_of_gas_during_initcode",
        "out_of_gas_when_returning_contract",
        "out_of_gas_when_returning_contract_due_to_memory_expansion",
    ],
)
def test_invalid_container_deployment(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    reason: str,
):
    """Verify nonce is not incremented when an invalid container deployment is attempted."""
    env = Environment()
    sender = pre.fund_eoa()

    # Valid defaults
    deployed_container = Container(
        sections=[
            Section.Code(code=Op.CALLF[1](Op.PUSH0, Op.PUSH0) + Op.STOP),
            Section.Code(code=Op.ADD + Op.RETF, code_inputs=2, code_outputs=1),
        ]
    )
    init_container: Container = Container(
        sections=[
            Section.Code(code=Op.RETURNCODE[0](0, 0)),
            Section.Container(deployed_container),
        ],
        kind=ContainerKind.INITCODE,
    )
    tx_gas_limit = 1_000_000
    fork_intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    fork_gas_costs = fork.gas_costs()

    # Modify defaults based on invalidity reason
    if reason == "invalid_deploy_container":
        deployed_container = Container(
            sections=[
                Section.Code(code=Op.CALLF[1](Op.PUSH0, Op.PUSH0) + Op.STOP),
                Section.Code(code=Op.ADD + Op.RETF, code_outputs=0),
            ]
        )
        init_container = Container(
            sections=[
                Section.Code(code=Op.RETURNCODE[0](0, 0)),
                Section.Container(deployed_container),
            ],
        )
    elif reason == "invalid_initcode":
        init_container = Container(
            sections=[
                Section.Code(code=Op.RETURNCODE[1](0, 0)),
                Section.Container(deployed_container),
            ],
        )
    elif (
        reason == "invalid_opcode_during_initcode"
        or reason == "invalid_opcode_with_sstore_during_initcode"
        or reason == "revert_opcode_during_initcode"
        or reason == "out_of_gas_during_initcode"
    ):
        invalid_code_path: Bytecode
        if reason == "invalid_opcode_during_initcode":
            invalid_code_path = Op.SSTORE(0, 1) + Op.INVALID
        elif reason == "revert_opcode_during_initcode":
            invalid_code_path = Op.REVERT(0, 0)
        elif reason == "out_of_gas_during_initcode":
            invalid_code_path = Op.MSTORE(0xFFFFFFFFFFFFFFFFFFFFFFFFFFF, 1)
        else:
            invalid_code_path = Op.INVALID
        init_container = Container(
            sections=[
                Section.Code(
                    code=Op.RJUMPI[len(invalid_code_path)](Op.PUSH0)
                    + invalid_code_path
                    + Op.RETURNCODE[0](0, 0)
                ),
                Section.Container(deployed_container),
            ],
        )
    elif reason == "out_of_gas_when_returning_contract":
        gas_cost = (
            # Transaction intrinsic gas cost
            fork_intrinsic_gas_calculator(calldata=init_container, contract_creation=True)
            # Code deposit gas cost
            + len(deployed_container) * fork_gas_costs.G_CODE_DEPOSIT_BYTE
            # Two push opcodes
            + 2 * fork_gas_costs.G_VERY_LOW
        )
        tx_gas_limit = gas_cost - 1
    elif reason == "out_of_gas_when_returning_contract_due_to_memory_expansion":
        gas_cost = (
            # Transaction intrinsic gas cost
            fork_intrinsic_gas_calculator(calldata=init_container, contract_creation=True)
            # Code deposit gas cost
            + (len(deployed_container) + 1) * fork_gas_costs.G_CODE_DEPOSIT_BYTE
            # Two push opcodes
            + 2 * fork_gas_costs.G_VERY_LOW
        )
        tx_gas_limit = gas_cost
        init_container = Container(
            sections=[
                Section.Code(code=Op.RETURNCODE[0](0, 1)),
                Section.Container(deployed_container),
            ],
        )
    elif reason == "valid":
        pass
    else:
        raise TypeError("Unexpected reason", reason)

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=tx_gas_limit,
        data=init_container,
    )

    destination_contract_address = tx.created_contract

    post = {
        destination_contract_address: Account.NONEXISTENT
        if reason != "valid"
        else Account(nonce=1, code=deployed_container),
        sender: Account(
            nonce=sender.nonce,
        ),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


def test_short_data_subcontainer(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Deploy a subcontainer where the data is "short" and filled by deployment code."""
    env = Environment()
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=100000,
        data=Container(
            name="Runtime Subcontainer with truncated data",
            sections=[
                Section.Code(code=Op.RETURNCODE[0](0, 1)),
                Section.Container(
                    Container(
                        sections=[
                            Section.Code(Op.STOP),
                            Section.Data(data="001122", custom_size=4),
                        ]
                    )
                ),
            ],
        ),
    )

    destination_contract_address = tx.created_contract

    post = {
        destination_contract_address: Account(nonce=1),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
