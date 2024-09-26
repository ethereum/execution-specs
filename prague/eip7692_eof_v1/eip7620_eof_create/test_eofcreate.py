"""
Test good and bad EOFCREATE cases
"""

import pytest

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

from .. import EOF_FORK_NAME
from ..eip7069_extcall.spec import EXTCALL_SUCCESS
from .helpers import (
    slot_call_result,
    slot_calldata,
    slot_code_worked,
    slot_create_address,
    slot_last_slot,
    slot_returndata_size,
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
    value_canary_to_be_overwritten,
    value_code_worked,
)
from .spec import EOFCREATE_FAILURE

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "52ddbcdddcf72dd72427c319f2beddeb468e1737"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_simple_eofcreate(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Verifies a simple EOFCREATE case
    """
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
            data=b"abcdef",
        ),
        storage={0: 0xB17D},  # a canary to be overwritten
    )
    # Storage in 0 should have the address,
    post = {
        contract_address: Account(
            storage={
                0: compute_eofcreate_address(contract_address, 0, smallest_initcode_subcontainer)
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
    """
    Verifies a simple EOFCREATE case, and then calls the deployed contract
    """
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
                code=Op.RETURNCONTRACT[0](0, 0),
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

    callable_address = compute_eofcreate_address(contract_address, 0, callable_contract_initcode)

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
    """
    Verifies that auxdata bytes are correctly handled in RETURNCONTRACT
    """
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
                + Op.RETURNCONTRACT[0](0, auxdata_size),
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
                slot_create_address: compute_eofcreate_address(
                    contract_address, 0, initcode_subcontainer
                )
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
    """
    Verifies CALLDATA passing through EOFCREATE
    """
    env = Environment()

    initcode_subcontainer = Container(
        name="Initcode Subcontainer",
        sections=[
            Section.Code(
                code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                + Op.SSTORE(slot_calldata, Op.MLOAD(0))
                + Op.RETURNCONTRACT[0](0, Op.CALLDATASIZE),
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
                    + Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, calldata_size))
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
    created_address = compute_eofcreate_address(contract_address, 0, initcode_subcontainer)
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
    """
    Verifies an EOFCREATE occuring within initcode creates that contract
    """
    nested_initcode_subcontainer = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, 0, 0, 0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.RETURNCONTRACT[1](0, 0),
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

    outer_address = compute_eofcreate_address(contract_address, 0, nested_initcode_subcontainer)
    inner_address = compute_eofcreate_address(outer_address, 0, smallest_initcode_subcontainer)
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
    """
    Verifies an EOFCREATE occuring in an initcode is rolled back when the initcode reverts
    """
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

    outer_address = compute_eofcreate_address(contract_address, 0, nested_initcode_subcontainer)
    inner_address = compute_eofcreate_address(outer_address, 0, smallest_initcode_subcontainer)
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
    """
    Verifies the return data is not re-used from a extcall but is cleared upon eofcreate
    """
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

    new_contract_address = compute_eofcreate_address(
        contract_address, 0, smallest_initcode_subcontainer
    )
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
    """
    Verifies a simple EOFCREATE case
    """
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
                    + Op.SSTORE(slot_create_address_3, Op.EOFCREATE[0](0, 1, 0, 0))
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=smallest_initcode_subcontainer),
            ],
        )
    )
    salt_zero_address = compute_eofcreate_address(
        contract_address, 0, smallest_initcode_subcontainer
    )
    salt_one_address = compute_eofcreate_address(
        contract_address, 1, smallest_initcode_subcontainer
    )

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
    """
    Verifies the return data is not being deployed, even if happens to be valid EOF
    """
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
                    + Op.SSTORE(slot_create_address, Op.EOFCREATE[0](0, salt, 0, Op.CALLDATASIZE))
                    + Op.SSTORE(slot_returndata_size, Op.RETURNDATASIZE)
                    + Op.STOP,
                ),
                Section.Container(container=code_reverts_with_calldata),
            ],
        ),
        storage={slot_create_address: value_canary_to_be_overwritten},
    )
    eof_create_address = compute_eofcreate_address(
        contract_address, salt, code_reverts_with_calldata
    )

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


@pytest.mark.parametrize("index", [1, 255], ids=lambda x: x)
def test_eofcreate_invalid_index(
    eof_test: EOFTestFiller,
    index: int,
):
    """Referring to non-existent container section index"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.EOFCREATE[index](0, 0, 0, 0) + Op.STOP,
                ),
                Section.Container(container=Container(sections=[Section.Code(code=Op.INVALID)])),
            ],
        ),
        expect_exception=EOFException.INVALID_CONTAINER_SECTION_INDEX,
    )
