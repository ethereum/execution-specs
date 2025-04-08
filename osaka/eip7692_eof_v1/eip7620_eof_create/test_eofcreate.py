"""Test good and bad EOFCREATE cases."""

import pytest

from ethereum_test_base_types import Storage
from ethereum_test_base_types.base_types import Address
from ethereum_test_exceptions import EOFException
from ethereum_test_specs import EOFTestFiller
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_eofcreate_address,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_vm.bytecode import Bytecode

from .. import EOF_FORK_NAME
from ..eip7069_extcall.spec import EXTCALL_SUCCESS
from .helpers import (
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
from .spec import EOFCREATE_FAILURE

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "52ddbcdddcf72dd72427c319f2beddeb468e1737"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_simple_eofcreate(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies a simple EOFCREATE case."""
    env = Environment()
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(0, Op.EOFCREATE[0](0, 0, 0, 0)) + Op.STOP,
                ),
                Section.Container(container=smallest_initcode_subcontainer),
            ],
        ),
        storage={0: 0xB17D},  # a canary to be overwritten
    )
    # Storage in 0 should have the address,
    post = {contract_address: Account(storage={0: compute_eofcreate_address(contract_address, 0)})}
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_eofcreate_then_dataload(
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
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(0, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.SSTORE(slot_data_load, Op.DATALOAD(0))
                    + Op.STOP,
                ),
                Section.Container(
                    container=small_auxdata_container,
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
        gas_price=10,
        protected=False,
        sender=sender,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_eofcreate_then_call(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies a simple EOFCREATE case, and then calls the deployed contract."""
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

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.EXTCALL(Op.SLOAD(slot_create_address), 0, 0, 0)
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=callable_contract_initcode),
            ],
        )
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
        gas_price=10,
        protected=False,
        sender=sender,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


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

    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0)) + Op.STOP,
                ),
                Section.Container(container=initcode_subcontainer),
            ]
        ),
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
        gas_price=10,
        protected=False,
        sender=sender,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


def test_calldata(state_test: StateTestFiller, pre: Alloc):
    """Verifies CALLDATA passing through EOFCREATE."""
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

    calldata_size = 32
    calldata = b"\x45" * calldata_size
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.MSTORE(0, Op.PUSH32(calldata))
                    + Op.SSTORE(slot_create_address, Op.EOFCREATE[0](input_size=calldata_size))
                    + Op.STOP,
                ),
                Section.Container(container=initcode_subcontainer),
            ]
        )
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
        gas_price=10,
        protected=False,
        sender=sender,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


def test_eofcreate_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies an EOFCREATE occuring within initcode creates that contract."""
    nested_initcode_subcontainer = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.RETURNCODE[1](0, 0),
            ),
            Section.Container(container=smallest_initcode_subcontainer),
            Section.Container(container=smallest_runtime_subcontainer),
        ]
    )

    env = Environment()
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=nested_initcode_subcontainer),
            ]
        )
    )

    outer_address = compute_eofcreate_address(contract_address, 0)
    inner_address = compute_eofcreate_address(outer_address, 0)
    post = {
        contract_address: Account(
            storage={slot_create_address: outer_address, slot_code_worked: value_code_worked}
        ),
        outer_address: Account(
            storage={slot_create_address: inner_address, slot_code_worked: value_code_worked}
        ),
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


def test_eofcreate_in_initcode_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies an EOFCREATE occuring in an initcode is rolled back when the initcode reverts."""
    nested_initcode_subcontainer = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.REVERT(0, 0),
            ),
            Section.Container(container=smallest_initcode_subcontainer),
        ]
    )

    env = Environment()
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=nested_initcode_subcontainer),
            ]
        ),
        storage={slot_create_address: value_canary_to_be_overwritten},
    )

    outer_address = compute_eofcreate_address(contract_address, 0)
    inner_address = compute_eofcreate_address(outer_address, 0)
    post = {
        contract_address: Account(
            storage={
                slot_create_address: 0,
                slot_code_worked: value_code_worked,
            }
        ),
        outer_address: Account.NONEXISTENT,
        inner_address: Account.NONEXISTENT,
    }
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_return_data_cleared(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies the return data is not re-used from a extcall but is cleared upon eofcreate."""
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

    slot_returndata_size_2 = slot_last_slot * 2 + slot_returndata_size
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_call_result, Op.EXTCALL(callable_address, 0, 0, 0))
                    + Op.SSTORE(slot_returndata_size, Op.RETURNDATASIZE)
                    + Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.SSTORE(slot_returndata_size_2, Op.RETURNDATASIZE)
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=smallest_initcode_subcontainer),
            ],
        )
    )

    new_contract_address = compute_eofcreate_address(contract_address, 0)
    post = {
        contract_address: Account(
            storage={
                slot_call_result: EXTCALL_SUCCESS,
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
        gas_price=10,
        protected=False,
        sender=sender,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


def test_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Tests address collision."""
    env = Environment()

    slot_create_address_2 = slot_last_slot * 2 + slot_create_address
    slot_create_address_3 = slot_last_slot * 3 + slot_create_address
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.SSTORE(slot_create_address_2, Op.EOFCREATE[0](0, 0, 0, 0))
                    + Op.SSTORE(slot_create_address_3, Op.EOFCREATE[0](salt=1))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=smallest_initcode_subcontainer),
            ],
        )
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
                slot_create_address_2: EOFCREATE_FAILURE,  # had an in-transaction collision
                slot_create_address_3: EOFCREATE_FAILURE,  # had a pre-existing collision
                slot_code_worked: value_code_worked,
            }
        )
    }

    # Multiple create fails is expensive, use an absurd amount of gas
    tx = Transaction(
        to=contract_address,
        gas_limit=300_000_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
    )
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_eofcreate_revert_eof_returndata(
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

    sender = pre.fund_eoa()
    salt = 0
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                    + Op.SSTORE(
                        slot_create_address, Op.EOFCREATE[0](salt=salt, input_size=Op.CALLDATASIZE)
                    )
                    + Op.SSTORE(slot_returndata_size, Op.RETURNDATASIZE)
                    + Op.STOP,
                ),
                Section.Container(container=code_reverts_with_calldata),
            ],
        ),
        storage={slot_create_address: value_canary_to_be_overwritten},
    )
    eof_create_address = compute_eofcreate_address(contract_address, salt)

    post = {
        contract_address: Account(
            storage={
                slot_create_address: 0,
                slot_returndata_size: len(smallest_runtime_subcontainer),
            },
        ),
        eof_create_address: Account.NONEXISTENT,
    }

    tx = Transaction(
        to=contract_address,
        gas_limit=1_000_000,
        sender=sender,
        # Simplest possible valid EOF container, which is going to be
        # revert-returned from initcode and must not end up being deployed.
        data=smallest_runtime_subcontainer,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("index", [0, 1, 255], ids=lambda x: x)
def test_eofcreate_invalid_index(
    eof_test: EOFTestFiller,
    index: int,
):
    """EOFCREATE referring non-existent container section index."""
    container = Container.Code(code=Op.EOFCREATE[index](0, 0, 0, 0) + Op.STOP)
    if index != 0:
        container.sections.append(Section.Container(container=Container.Code(Op.INVALID)))

    eof_test(
        container=container,
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )


def test_eofcreate_invalid_truncated_immediate(
    eof_test: EOFTestFiller,
):
    """EOFCREATE instruction with missing immediate byte."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(Op.PUSH0 * 4 + Op.EOFCREATE),
                Section.Container(Container.Code(Op.INVALID)),
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


@pytest.mark.parametrize(
    ["data_len", "data_section_size"],
    [
        (0, 1),
        (0, 0xFFFF),
        (2, 3),
        (2, 0xFFFF),
    ],
)
def test_eofcreate_truncated_container(
    eof_test: EOFTestFiller,
    data_len: int,
    data_section_size: int,
):
    """EOFCREATE instruction targeting a container with truncated data section."""
    assert data_len < data_section_size
    eof_test(
        container=Container(
            sections=[
                Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section.Container(
                    Container(
                        sections=[
                            Section.Code(Op.INVALID),
                            Section.Data(b"\xda" * data_len, custom_size=data_section_size),
                        ],
                    )
                ),
            ],
        ),
        expect_exception=EOFException.EOFCREATE_WITH_TRUNCATED_CONTAINER,
    )


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
def test_eofcreate_context(
    state_test: StateTestFiller,
    pre: Alloc,
    destination_code: Bytecode,
    expected_result: str,
):
    """Test EOFCREATE's initcode context instructions."""
    env = Environment()
    sender = pre.fund_eoa()
    value = 0x1123
    eofcreate_value = 0x13

    initcode = Container(
        sections=[
            Section.Code(Op.SSTORE(slot_call_result, destination_code) + Op.RETURNCODE[0](0, 0)),
            Section.Container(smallest_runtime_subcontainer),
        ]
    )

    factory_contract = Container(
        sections=[
            Section.Code(
                Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.EOFCREATE[0](value=eofcreate_value)
                + Op.STOP
            ),
            Section.Container(initcode),
        ]
    )
    factory_address = pre.deploy_contract(factory_contract)

    destination_contract_address = compute_eofcreate_address(factory_address, 0)

    tx = Transaction(sender=sender, to=factory_address, gas_limit=200_000, value=value)

    expected_bytes: Address | int
    if expected_result == "destination":
        expected_bytes = destination_contract_address
    elif expected_result == "caller":
        expected_bytes = factory_address
    elif expected_result == "sender":
        expected_bytes = sender
    elif expected_result == "eofcreate_value":
        expected_bytes = eofcreate_value
    elif expected_result == "selfbalance":
        expected_bytes = eofcreate_value
    elif expected_result == "factorybalance":
        # Factory receives value from sender and passes on eofcreate_value as endowment.
        expected_bytes = value - eofcreate_value
    else:
        raise TypeError("Unexpected expected_result", expected_result)

    calling_storage = {
        slot_code_worked: value_code_worked,
    }
    destination_contract_storage = {
        slot_call_result: expected_bytes,
    }

    post = {
        factory_address: Account(storage=calling_storage, balance=value - eofcreate_value),
        destination_contract_address: Account(
            storage=destination_contract_storage, balance=eofcreate_value
        ),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


def test_eofcreate_memory_context(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Verifies an EOFCREATE frame enjoys a separate EVM memory from its caller frame."""
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
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    Op.SSTORE(contract_storage.store_next(value_code_worked), value_code_worked)
                    + Op.MSTORE(0, 1)
                    + Op.EOFCREATE[0](0, 0, 0, 0)
                    + Op.SSTORE(contract_storage.store_next(32), Op.MSIZE())
                    + Op.SSTORE(contract_storage.store_next(1), Op.MLOAD(0))
                    + Op.SSTORE(contract_storage.store_next(0), Op.MLOAD(32))
                    + Op.STOP,
                ),
                Section.Container(initcontainer),
            ],
        ),
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
    )
    state_test(env=env, pre=pre, post=post, tx=tx)
