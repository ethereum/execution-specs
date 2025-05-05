"""
Return data management around create2
Port call_outsize_then_create2_successful_then_returndatasizeFiller.json test
Port call_then_create2_successful_then_returndatasizeFiller.json test.
"""

import pytest

from ethereum_test_tools import Account, Alloc, StateTestFiller, Transaction, keccak256
from ethereum_test_tools import Opcodes as Op

from .spec import ref_spec_1014

REFERENCE_SPEC_GIT_PATH = ref_spec_1014.git_path
REFERENCE_SPEC_VERSION = ref_spec_1014.version


@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("call_return_size", [35, 32, 0])
@pytest.mark.parametrize("create_type", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("return_type", [Op.RETURN, Op.REVERT])
@pytest.mark.parametrize("return_type_in_create", [Op.RETURN, Op.REVERT])
def test_create2_return_data(
    call_return_size: int,
    create_type: Op,
    return_type: Op,
    return_type_in_create: Op,
    pre: Alloc,
    state_test: StateTestFiller,
):
    """Validate that create2 return data does not interfere with previously existing memory."""
    # Storage vars
    slot_returndatasize_before_create = 0
    slot_returndatasize_after_create = 1
    slot_return_data_hash_before_create = 2
    slot_return_data_hash_after_create = 3
    slot_code_worked = 4
    slot_returndatacopy_before_create = 5
    slot_returndatacopy_before_create_2 = 6
    slot_returndatacopy_after_create = 7
    slot_begin_memory_after_create = 8

    # CREATE2 Initcode
    create2_salt = 1
    return_data_in_create = 0xFFFAFB
    initcode = Op.MSTORE(0, return_data_in_create) + return_type_in_create(0, 32)
    call_return_data_value = 0x1122334455667788991011121314151617181920212223242526272829303132
    expected_call_return_data = int.to_bytes(call_return_data_value, 32, byteorder="big").ljust(
        call_return_size, b"\0"
    )[0:call_return_size]
    expected_returndatacopy = expected_call_return_data[0:32]
    empty_data = b""

    address_call = pre.deploy_contract(
        code=Op.MSTORE(0, call_return_data_value)
        + Op.MSTORE(32, 0xFFFFFFFF)
        + return_type(0, call_return_size),
        storage={},
    )
    address_to = pre.deploy_contract(
        balance=100_000_000,
        code=Op.JUMPDEST()
        + Op.MSTORE(0x100, Op.CALLDATALOAD(0))
        + Op.CALL(0x0900000000, address_call, 0, 0, 0, 0, call_return_size)
        #
        #
        + Op.SSTORE(slot_returndatasize_before_create, Op.RETURNDATASIZE())
        + Op.RETURNDATACOPY(0x200, 0, call_return_size)
        + Op.SSTORE(slot_returndatacopy_before_create, Op.MLOAD(0x200))
        + Op.SSTORE(slot_returndatacopy_before_create_2, Op.MLOAD(0x220))
        + Op.SSTORE(slot_return_data_hash_before_create, Op.SHA3(0, call_return_size))
        #
        #
        + create_type(offset=0x100, size=Op.CALLDATASIZE(), salt=create2_salt)
        + Op.SSTORE(slot_returndatasize_after_create, Op.RETURNDATASIZE())
        + Op.RETURNDATACOPY(0x300, 0, Op.RETURNDATASIZE())
        + Op.SSTORE(slot_returndatacopy_after_create, Op.MLOAD(0x300))
        + Op.SSTORE(slot_return_data_hash_after_create, Op.SHA3(0x300, Op.RETURNDATASIZE()))
        + Op.SSTORE(slot_begin_memory_after_create, Op.MLOAD(0))
        + Op.SSTORE(slot_code_worked, 1)
        + Op.STOP(),
        storage={
            slot_returndatasize_before_create: 0xFF,
            slot_returndatasize_after_create: 0xFF,
            slot_return_data_hash_before_create: 0xFF,
            slot_return_data_hash_after_create: 0xFF,
            slot_returndatacopy_before_create: 0xFF,
            slot_returndatacopy_before_create_2: 0xFF,
            slot_begin_memory_after_create: 0xFF,
        },
    )

    post = {
        address_to: Account(
            storage={
                slot_code_worked: 1,
                slot_returndatacopy_before_create: expected_returndatacopy,
                slot_returndatacopy_before_create_2: 0,
                #
                # the actual bytes returned by returndatacopy opcode after create
                slot_returndatacopy_after_create: (
                    return_data_in_create if return_type_in_create == Op.REVERT else 0
                ),
                slot_returndatasize_before_create: call_return_size,
                #
                # return datasize value after create
                slot_returndatasize_after_create: (
                    0x20 if return_type_in_create == Op.REVERT else 0
                ),
                #
                slot_return_data_hash_before_create: keccak256(expected_call_return_data),
                slot_return_data_hash_after_create: (
                    keccak256(empty_data)
                    if return_type_in_create == Op.RETURN
                    else keccak256(int.to_bytes(return_data_in_create, 32, byteorder="big"))
                ),
                #
                # check that create 2 didn't mess up with initial memory space declared for return
                slot_begin_memory_after_create: expected_returndatacopy,
            }  # type: ignore
        )
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=address_to,
        protected=False,
        data=initcode,
        gas_limit=500_000,
        value=0,
    )  # type: ignore

    state_test(pre=pre, post=post, tx=tx)
