"""Test good TXCREATE cases."""

import pytest

from ethereum_test_base_types import Storage
from ethereum_test_base_types.base_types import Address
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

from .. import EOF_FORK_NAME
from ..eip7069_extcall.spec import EXTCALL_SUCCESS, LEGACY_CALL_SUCCESS
from ..eip7620_eof_create.helpers import (
    slot_call_result,
    slot_calldata,
    slot_code_worked,
    slot_create_address,
    slot_data_load,
    slot_last_slot,
    slot_returndata_size,
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
    value_canary_to_be_overwritten,
    value_code_worked,
    value_long_value,
)
from .spec import TXCREATE_FAILURE

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7873.md"
REFERENCE_SPEC_VERSION = "1115fe6110fcc0efc823fb7f8f5cd86c42173efe"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.with_all_evm_code_types
@pytest.mark.parametrize("tx_initcode_count", [1, 255, 256])
def test_simple_txcreate(state_test: StateTestFiller, pre: Alloc, tx_initcode_count: int):
    """Verifies a simple TXCREATE case."""
    env = Environment()
    sender = pre.fund_eoa()
    initcode_hash = smallest_initcode_subcontainer.hash
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.TXCREATE(tx_initcode_hash=initcode_hash)) + Op.STOP,
        storage={0: 0xB17D},  # a canary to be overwritten
    )
    # Storage in 0 should have the address,
    post = {contract_address: Account(storage={0: compute_eofcreate_address(contract_address, 0)})}
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[smallest_initcode_subcontainer] * tx_initcode_count,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_txcreate_then_dataload(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies that a contract returned with auxdata does not overwrite the parent data."""
    env = Environment()
    sender = pre.fund_eoa()
    small_auxdata_container = Container(
        sections=[
            Section.Code(code=Op.RETURNCODE[0](0, 32)),
            Section.Container(container=smallest_runtime_subcontainer),
        ],
    )
    initcode_hash = small_auxdata_container.hash
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(0, Op.TXCREATE(tx_initcode_hash=initcode_hash))
                    + Op.SSTORE(slot_data_load, Op.DATALOAD(0))
                    + Op.STOP,
                ),
                Section.Data(data=value_long_value),
            ],
        ),
        storage={slot_data_load: value_canary_to_be_overwritten},
    )

    post = {
        contract_address: Account(
            storage={
                0: compute_eofcreate_address(contract_address, 0),
                slot_data_load: value_long_value,
            }
        )
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[small_auxdata_container],
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
def test_txcreate_then_call(state_test: StateTestFiller, pre: Alloc, evm_code_type: EVMCodeType):
    """Verifies a simple TXCREATE case, and then calls the deployed contract."""
    env = Environment()
    callable_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
            ),
        ]
    )
    callable_contract_initcode = Container(
        sections=[
            Section.Code(
                code=Op.RETURNCODE[0](0, 0),
            ),
            Section.Container(container=callable_contract),
        ]
    )
    initcode_hash = callable_contract_initcode.hash

    sender = pre.fund_eoa()
    opcode = Op.EXTCALL if evm_code_type == EVMCodeType.EOF_V1 else Op.CALL
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(slot_create_address, Op.TXCREATE(tx_initcode_hash=initcode_hash))
        + opcode(address=Op.SLOAD(slot_create_address))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )

    callable_address = compute_eofcreate_address(contract_address, 0)

    # Storage in 0 should have the address,
    #
    post = {
        contract_address: Account(
            storage={slot_create_address: callable_address, slot_code_worked: value_code_worked}
        ),
        callable_address: Account(storage={slot_code_worked: value_code_worked}),
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[callable_contract_initcode],
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
@pytest.mark.parametrize(
    "auxdata_bytes",
    [
        pytest.param(b"", id="zero"),
        pytest.param(b"aabbcc", id="short"),
        pytest.param(b"aabbccddeef", id="one_byte_short"),
        pytest.param(b"aabbccddeeff", id="exact"),
        pytest.param(b"aabbccddeeffg", id="one_byte_long"),
        pytest.param(b"aabbccddeeffgghhii", id="extra"),
    ],
)
def test_auxdata_variations(state_test: StateTestFiller, pre: Alloc, auxdata_bytes: bytes):
    """Verifies that auxdata bytes are correctly handled in RETURNCODE."""
    env = Environment()
    auxdata_size = len(auxdata_bytes)
    pre_deploy_header_data_size = 18
    pre_deploy_data = b"AABBCC"
    deploy_success = len(auxdata_bytes) + len(pre_deploy_data) >= pre_deploy_header_data_size

    runtime_subcontainer = Container(
        name="Runtime Subcontainer with truncated data",
        sections=[
            Section.Code(code=Op.STOP),
            Section.Data(data=pre_deploy_data, custom_size=pre_deploy_header_data_size),
        ],
    )

    initcode_subcontainer = Container(
        name="Initcode Subcontainer",
        sections=[
            Section.Code(
                code=Op.MSTORE(0, Op.PUSH32(auxdata_bytes.ljust(32, b"\0")))
                + Op.RETURNCODE[0](0, auxdata_size),
            ),
            Section.Container(container=runtime_subcontainer),
        ],
    )
    initcode_hash = initcode_subcontainer.hash

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(slot_create_address, Op.TXCREATE(tx_initcode_hash=initcode_hash)) + Op.STOP,
        storage={slot_create_address: value_canary_to_be_overwritten},
    )

    # Storage in 0 should have the address,
    post = {
        contract_address: Account(
            storage={
                slot_create_address: compute_eofcreate_address(contract_address, 0)
                if deploy_success
                else b"\0"
            }
        )
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[initcode_subcontainer],
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
def test_calldata(state_test: StateTestFiller, pre: Alloc):
    """Verifies CALLDATA passing through TXCREATE."""
    env = Environment()

    initcode_subcontainer = Container(
        name="Initcode Subcontainer",
        sections=[
            Section.Code(
                code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                + Op.SSTORE(slot_calldata, Op.MLOAD(0))
                + Op.RETURNCODE[0](0, Op.CALLDATASIZE),
            ),
            Section.Container(container=smallest_runtime_subcontainer),
        ],
    )
    initcode_hash = initcode_subcontainer.hash

    calldata_size = 32
    calldata = b"\x45" * calldata_size
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.MSTORE(0, Op.PUSH32(calldata))
        + Op.SSTORE(
            slot_create_address,
            Op.TXCREATE(tx_initcode_hash=initcode_hash, input_size=calldata_size),
        )
        + Op.STOP,
    )

    # deployed contract is smallest plus data
    deployed_contract = Container(
        name="deployed contract",
        sections=[
            *smallest_runtime_subcontainer.sections,
            Section.Data(data=calldata),
        ],
    )
    # factory contract Storage in 0 should have the created address,
    # created contract storage in 0 should have the calldata
    created_address = compute_eofcreate_address(contract_address, 0)
    post = {
        contract_address: Account(storage={slot_create_address: created_address}),
        created_address: Account(code=deployed_contract, storage={slot_calldata: calldata}),
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[initcode_subcontainer],
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("outer_create_opcode", [Op.TXCREATE, Op.EOFCREATE])
@pytest.mark.parametrize("inner_create_opcode", [Op.TXCREATE, Op.EOFCREATE])
@pytest.mark.parametrize("outer_create_reverts", [True, False])
def test_txcreate_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    outer_create_opcode: Op,
    inner_create_opcode: Op,
    outer_create_reverts: bool,
):
    """
    Verifies an TXCREATE occuring within initcode creates that contract.

    Via the `outer_create_reverts` also verifies a TXCREATE occuring in an initcode is rolled back
    when the initcode reverts.
    """
    smallest_initcode_subcontainer_hash = smallest_initcode_subcontainer.hash
    inner_create_bytecode = (
        Op.TXCREATE(tx_initcode_hash=smallest_initcode_subcontainer_hash)
        if inner_create_opcode == Op.TXCREATE
        else Op.EOFCREATE[1](0, 0, 0, 0)
    )
    # The terminating code of the inner initcontainer, the RJUMPI is a trick to not need to deal
    # with the subcontainer indices
    revert_code = Op.REVERT(0, 0)
    terminating_code = (
        Op.RJUMPI[len(revert_code)](0) + revert_code + Op.RETURNCODE[0](0, 0)
        if outer_create_reverts
        else Op.RETURNCODE[0](0, 0)
    )
    nested_initcode_subcontainer = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_create_address, inner_create_bytecode)
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + terminating_code,
            ),
            Section.Container(container=smallest_runtime_subcontainer),
        ]
        + (
            [Section.Container(container=smallest_initcode_subcontainer)]
            if inner_create_opcode == Op.EOFCREATE
            else []
        )
    )
    nested_initcode_subcontainer_hash = nested_initcode_subcontainer.hash

    outer_create_bytecode = (
        Op.TXCREATE(tx_initcode_hash=nested_initcode_subcontainer_hash)
        if outer_create_opcode == Op.TXCREATE
        else Op.EOFCREATE[0](0, 0, 0, 0)
    )

    env = Environment()
    sender = pre.fund_eoa()
    contract_code = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_create_address, outer_create_bytecode)
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            ),
        ]
        + (
            [Section.Container(container=nested_initcode_subcontainer)]
            if outer_create_opcode == Op.EOFCREATE
            else []
        )
    )
    contract_address = pre.deploy_contract(code=contract_code)

    outer_address = compute_eofcreate_address(contract_address, 0)
    inner_address = compute_eofcreate_address(outer_address, 0)
    post = {
        contract_address: Account(
            storage={
                slot_create_address: outer_address if not outer_create_reverts else 0,
                slot_code_worked: value_code_worked,
            }
        ),
        outer_address: Account(
            storage={slot_create_address: inner_address, slot_code_worked: value_code_worked}
        )
        if not outer_create_reverts
        else Account.NONEXISTENT,
        inner_address: Account() if not outer_create_reverts else Account.NONEXISTENT,
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[nested_initcode_subcontainer, smallest_initcode_subcontainer],
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
def test_return_data_cleared(
    state_test: StateTestFiller,
    pre: Alloc,
    evm_code_type: EVMCodeType,
):
    """Verifies the return data is not re-used from a extcall but is cleared upon TXCREATE."""
    env = Environment()
    value_return_canary = 0x4158675309
    value_return_canary_size = 5
    callable_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.MSTORE(0, value_return_canary)
                    + Op.RETURN(0, value_return_canary_size),
                )
            ]
        )
    )
    initcode_hash = smallest_initcode_subcontainer.hash

    slot_returndata_size_2 = slot_last_slot * 2 + slot_returndata_size
    sender = pre.fund_eoa()
    opcode = Op.EXTCALL if evm_code_type == EVMCodeType.EOF_V1 else Op.CALL
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(slot_call_result, opcode(address=callable_address))
        + Op.SSTORE(slot_returndata_size, Op.RETURNDATASIZE)
        + Op.SSTORE(slot_create_address, Op.TXCREATE(tx_initcode_hash=initcode_hash))
        + Op.SSTORE(slot_returndata_size_2, Op.RETURNDATASIZE)
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )

    new_contract_address = compute_eofcreate_address(contract_address, 0)
    post = {
        contract_address: Account(
            storage={
                slot_call_result: EXTCALL_SUCCESS
                if evm_code_type == EVMCodeType.EOF_V1
                else LEGACY_CALL_SUCCESS,
                slot_returndata_size: value_return_canary_size,
                slot_create_address: new_contract_address,
                slot_returndata_size_2: 0,
                slot_code_worked: value_code_worked,
            },
            nonce=2,
        ),
        callable_address: Account(nonce=1),
        new_contract_address: Account(nonce=1),
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[smallest_initcode_subcontainer],
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
def test_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Tests address collision."""
    env = Environment()

    slot_create_address_2 = slot_last_slot * 2 + slot_create_address
    slot_create_address_3 = slot_last_slot * 3 + slot_create_address
    sender = pre.fund_eoa()
    initcode_hash = smallest_initcode_subcontainer.hash
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(slot_create_address, Op.TXCREATE(tx_initcode_hash=initcode_hash))
        + Op.SSTORE(slot_create_address_2, Op.TXCREATE(tx_initcode_hash=initcode_hash))
        + Op.SSTORE(slot_create_address_3, Op.TXCREATE(tx_initcode_hash=initcode_hash, salt=1))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )
    salt_zero_address = compute_eofcreate_address(contract_address, 0)
    salt_one_address = compute_eofcreate_address(contract_address, 1)

    # Hard-code address for collision, no other way to do this.
    # We should mark tests that do this, and fail on unmarked tests.
    pre[salt_one_address] = Account(balance=1, nonce=1)

    post = {
        contract_address: Account(
            storage={
                slot_create_address: salt_zero_address,
                slot_create_address_2: TXCREATE_FAILURE,  # had an in-transaction collision
                slot_create_address_3: TXCREATE_FAILURE,  # had a pre-existing collision
                slot_code_worked: value_code_worked,
            }
        )
    }

    # Multiple create fails is expensive, use an absurd amount of gas
    tx = Transaction(
        to=contract_address,
        gas_limit=300_000_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[smallest_initcode_subcontainer],
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
def test_txcreate_revert_eof_returndata(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies the return data is not being deployed, even if happens to be valid EOF."""
    env = Environment()
    code_reverts_with_calldata = Container(
        name="Initcode Subcontainer reverting with its calldata",
        sections=[
            Section.Code(
                code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.REVERT(0, Op.CALLDATASIZE),
            ),
        ],
    )
    initcode_hash = code_reverts_with_calldata.hash

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            slot_create_address,
            Op.TXCREATE(tx_initcode_hash=initcode_hash, input_size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(slot_returndata_size, Op.RETURNDATASIZE)
        + Op.STOP,
        storage={slot_create_address: value_canary_to_be_overwritten},
    )
    new_address = compute_eofcreate_address(contract_address, 0)

    post = {
        contract_address: Account(
            storage={
                slot_create_address: 0,
                slot_returndata_size: len(smallest_runtime_subcontainer),
            },
        ),
        new_address: Account.NONEXISTENT,
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=1_000_000,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        sender=sender,
        initcodes=[code_reverts_with_calldata],
        # Simplest possible valid EOF container, which is going to be
        # revert-returned from initcode and must not end up being deployed.
        data=smallest_runtime_subcontainer,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
@pytest.mark.parametrize(
    ["destination_code", "expected_result"],
    [
        pytest.param(Op.ADDRESS, "destination"),
        pytest.param(Op.CALLER, "caller"),
        pytest.param(Op.CALLVALUE, "eofcreate_value"),
        pytest.param(Op.ORIGIN, "sender"),
        pytest.param(Op.SELFBALANCE, "selfbalance"),
        pytest.param(Op.BALANCE(Op.CALLER), "factorybalance"),
    ],
)
def test_txcreate_context(
    state_test: StateTestFiller,
    pre: Alloc,
    destination_code: Bytecode,
    expected_result: str,
):
    """Test TXCREATE's initcode context instructions."""
    env = Environment()
    sender = pre.fund_eoa()
    value = 0x1123
    txcreate_value = 0x13

    initcode = Container(
        sections=[
            Section.Code(Op.SSTORE(slot_call_result, destination_code) + Op.RETURNCODE[0](0, 0)),
            Section.Container(smallest_runtime_subcontainer),
        ]
    )
    initcode_hash = initcode.hash

    factory_address = pre.deploy_contract(
        code=Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.TXCREATE(tx_initcode_hash=initcode_hash, value=txcreate_value)
        + Op.STOP
    )

    destination_contract_address = compute_eofcreate_address(factory_address, 0)

    tx = Transaction(
        sender=sender,
        to=factory_address,
        gas_limit=200_000,
        value=value,
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        initcodes=[initcode],
    )

    expected_bytes: Address | int
    if expected_result == "destination":
        expected_bytes = destination_contract_address
    elif expected_result == "caller":
        expected_bytes = factory_address
    elif expected_result == "sender":
        expected_bytes = sender
    elif expected_result == "eofcreate_value":
        expected_bytes = txcreate_value
    elif expected_result == "selfbalance":
        expected_bytes = txcreate_value
    elif expected_result == "factorybalance":
        # Factory receives value from sender and passes on eofcreate_value as endowment.
        expected_bytes = value - txcreate_value
    else:
        raise TypeError("Unexpected expected_result", expected_result)

    calling_storage = {
        slot_code_worked: value_code_worked,
    }
    destination_contract_storage = {
        slot_call_result: expected_bytes,
    }

    post = {
        factory_address: Account(storage=calling_storage, balance=value - txcreate_value),
        destination_contract_address: Account(
            storage=destination_contract_storage, balance=txcreate_value
        ),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.with_all_evm_code_types
def test_txcreate_memory_context(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies an TXCREATE frame enjoys a separate EVM memory from its caller frame."""
    env = Environment()
    destination_storage = Storage()
    contract_storage = Storage()
    initcontainer = Container(
        sections=[
            Section.Code(
                Op.SSTORE(destination_storage.store_next(value_code_worked), value_code_worked)
                + Op.SSTORE(destination_storage.store_next(0), Op.MSIZE())
                + Op.SSTORE(destination_storage.store_next(0), Op.MLOAD(0))
                + Op.MSTORE(0, 2)
                + Op.MSTORE(32, 2)
                + Op.RETURNCODE[0](0, 0)
            ),
            Section.Container(smallest_runtime_subcontainer),
        ]
    )
    initcode_hash = initcontainer.hash
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(contract_storage.store_next(value_code_worked), value_code_worked)
        + Op.MSTORE(0, 1)
        + Op.TXCREATE(tx_initcode_hash=initcode_hash)
        + Op.SSTORE(contract_storage.store_next(32), Op.MSIZE())
        + Op.SSTORE(contract_storage.store_next(1), Op.MLOAD(0))
        + Op.SSTORE(contract_storage.store_next(0), Op.MLOAD(32))
        + Op.STOP,
    )
    destination_contract_address = compute_eofcreate_address(contract_address, 0)
    post = {
        contract_address: Account(storage=contract_storage),
        destination_contract_address: Account(storage=destination_storage),
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=200_000,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=10,
        max_fee_per_gas=10,
        initcodes=[initcontainer],
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_evm_code_types
def test_short_data_subcontainer(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Deploy a subcontainer where the data is "short" and filled by deployment code."""
    env = Environment()
    sender = pre.fund_eoa()

    deploy_container = Container(
        sections=[
            Section.Code(Op.STOP),
            Section.Data(data="001122", custom_size=4),
        ]
    )
    initcontainer = Container(
        sections=[
            Section.Code(code=Op.RETURNCODE[0](0, 5)),
            Section.Container(deploy_container),
        ],
    )
    initcode_hash = initcontainer.hash
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.TXCREATE(tx_initcode_hash=initcode_hash)) + Op.STOP,
        storage={0: 0xB17D},  # a canary to be overwritten
    )
    # Storage in 0 should have the address,
    destination_address = compute_eofcreate_address(contract_address, 0)
    destination_code = deploy_container.copy()
    destination_code.sections[1] = Section.Data(data="0011220000000000")
    post = {
        contract_address: Account(storage={0: compute_eofcreate_address(contract_address, 0)}),
        destination_address: Account(code=destination_code),
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=100_000,
        sender=sender,
        initcodes=[initcontainer],
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
