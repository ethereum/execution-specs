"""
abstract: Tests for [EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)
    Test cases for `TSTORE` and `TLOAD` opcode calls in reentrancy after self-destruct, taking into
    account the changes in EIP-6780.
"""  # noqa: E501

from enum import unique
from typing import Dict

import pytest

from ethereum_test_tools import Account, Alloc, Bytecode, CalldataCase, Environment, Hash, Initcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Switch, Transaction, compute_create_address

from . import PytestParameterEnum
from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

CREATE_CODE = Op.CALLDATACOPY(size=Op.CALLDATASIZE) + Op.CREATE(size=Op.CALLDATASIZE)


def call_option(option_number: int) -> Bytecode:
    """
    Return the bytecode for a call to the callee contract with the given option number.
    """
    return Op.MSTORE(value=option_number) + Op.CALL(
        address=Op.SLOAD(0),
        args_offset=0,
        args_size=32,
        ret_offset=0,
        ret_size=32,
    )


@unique
class SelfDestructCases(PytestParameterEnum):
    """
    Transient storage test cases for different reentrancy calls which involve the contract
    self-destructing.
    """

    TLOAD_AFTER_SELFDESTRUCT_PRE_EXISTING_CONTRACT = {
        "description": (
            "Use TSTORE to store a transient value and self-destruct in a contract that was"
            "deployed in a transaction prior to the one currently executing."
            "Then re-enter the contract and attempt to TLOAD the transient value.",
        ),
        "pre_existing_contract": True,
        "caller_bytecode": Op.SSTORE(0, Op.CALLDATALOAD(0))
        + Op.SSTORE(1, call_option(1))
        + Op.SSTORE(2, call_option(2))
        + Op.SSTORE(3, Op.MLOAD(0)),
        "callee_bytecode": Switch(
            cases=[
                CalldataCase(value=1, action=Op.TSTORE(0xFF, 0x100) + Op.SELFDESTRUCT(0)),
                CalldataCase(value=2, action=Op.MSTORE(0, Op.TLOAD(0xFF)) + Op.RETURN(0, 32)),
            ],
        ),
        "expected_storage": {
            1: 0x01,
            2: 0x01,
            3: 0x100,
        },
    }

    TLOAD_AFTER_SELFDESTRUCT_NEW_CONTRACT = {
        "description": (
            "Use TSTORE to store a transient value and self-destruct in a contract that was"
            "deployed in the current transaction."
            "Then re-enter the contract and attempt to TLOAD the transient value.",
        ),
        "pre_existing_contract": False,
        "caller_bytecode": Op.SSTORE(0, CREATE_CODE)
        + Op.SSTORE(1, call_option(1))
        + Op.SSTORE(2, call_option(2))
        + Op.SSTORE(3, Op.MLOAD(0)),
        "callee_bytecode": Switch(
            cases=[
                CalldataCase(value=1, action=Op.TSTORE(0xFF, 0x100) + Op.SELFDESTRUCT(0)),
                CalldataCase(value=2, action=Op.MSTORE(0, Op.TLOAD(0xFF)) + Op.RETURN(0, 32)),
            ],
        ),
        "expected_storage": {
            1: 0x01,
            2: 0x01,
            3: 0x100,
        },
    }

    TLOAD_AFTER_INNER_SELFDESTRUCT_PRE_EXISTING_CONTRACT = {
        "description": (
            "Use TSTORE to store a transient value and then call for re-entry and self-destruct,"
            "and use TLOAD upon return from the inner self-destructing call.",
        ),
        "pre_existing_contract": True,
        "caller_bytecode": Op.SSTORE(0, Op.CALLDATALOAD(0))
        + Op.SSTORE(1, call_option(1))
        + Op.SSTORE(2, Op.MLOAD(0)),
        "callee_bytecode": Switch(
            cases=[
                CalldataCase(
                    value=1,
                    action=Op.TSTORE(0xFF, 0x100)
                    + call_option(2)
                    + Op.MSTORE(0, Op.TLOAD(0xFF))
                    + Op.RETURN(0, 32),
                ),
                CalldataCase(value=2, action=Op.SELFDESTRUCT(0)),
            ],
        ),
        "expected_storage": {
            1: 0x01,
            2: 0x100,
        },
    }

    TLOAD_AFTER_INNER_SELFDESTRUCT_NEW_CONTRACT = {
        "description": (
            "In a newly created contract, use TSTORE to store a transient value and then call "
            "for re-entry and self-destruct, and use TLOAD upon return from the inner "
            "self-destructing call.",
        ),
        "pre_existing_contract": False,
        "caller_bytecode": (
            Op.SSTORE(0, CREATE_CODE) + Op.SSTORE(1, call_option(1)) + Op.SSTORE(2, Op.MLOAD(0))
        ),
        "callee_bytecode": Switch(
            cases=[
                CalldataCase(
                    value=1,
                    action=Op.TSTORE(0xFF, 0x100)
                    + Op.MSTORE(value=2)
                    + Op.CALL(
                        address=Op.ADDRESS,
                        args_offset=0,
                        args_size=32,
                        ret_offset=0,
                        ret_size=32,
                    )
                    + Op.MSTORE(0, Op.TLOAD(0xFF))
                    + Op.RETURN(0, 32),
                ),
                CalldataCase(value=2, action=Op.SELFDESTRUCT(0)),
            ],
        ),
        "expected_storage": {
            1: 0x01,
            2: 0x100,
        },
    }

    TSTORE_AFTER_SELFDESTRUCT_PRE_EXISTING_CONTRACT = {
        "description": (
            "Use self-destruct in a pre-existing contract and then use TSTORE upon a re-entry."
            "Lastly use TLOAD on another re-entry",
        ),
        "pre_existing_contract": True,
        "caller_bytecode": Op.SSTORE(0, Op.CALLDATALOAD(0))
        + Op.SSTORE(1, call_option(1))
        + Op.SSTORE(2, call_option(2))
        + Op.SSTORE(3, call_option(3))
        + Op.SSTORE(4, Op.MLOAD(0)),
        "callee_bytecode": Switch(
            cases=[
                CalldataCase(value=1, action=Op.SELFDESTRUCT(0)),
                CalldataCase(value=2, action=Op.TSTORE(0xFF, 0x100)),
                CalldataCase(value=3, action=Op.MSTORE(0, Op.TLOAD(0xFF)) + Op.RETURN(0, 32)),
            ],
        ),
        "expected_storage": {
            1: 0x01,
            2: 0x01,
            3: 0x01,
            4: 0x100,
        },
    }

    TSTORE_AFTER_SELFDESTRUCT_NEW_CONTRACT = {
        "description": (
            "Use self-destruct in a newly created contract and then use TSTORE upon a re-entry."
            "Lastly use TLOAD on another re-entry",
        ),
        "pre_existing_contract": False,
        "caller_bytecode": Op.SSTORE(0, CREATE_CODE)
        + Op.SSTORE(1, call_option(1))
        + Op.SSTORE(2, call_option(2))
        + Op.SSTORE(3, call_option(3))
        + Op.SSTORE(4, Op.MLOAD(0)),
        "callee_bytecode": Switch(
            cases=[
                CalldataCase(value=1, action=Op.SELFDESTRUCT(0)),
                CalldataCase(value=2, action=Op.TSTORE(0xFF, 0x100)),
                CalldataCase(value=3, action=Op.MSTORE(0, Op.TLOAD(0xFF)) + Op.RETURN(0, 32)),
            ],
        ),
        "expected_storage": {
            1: 0x01,
            2: 0x01,
            3: 0x01,
            4: 0x100,
        },
    }


@SelfDestructCases.parametrize()
def test_reentrant_selfdestructing_call(
    state_test: StateTestFiller,
    pre: Alloc,
    pre_existing_contract: bool,
    caller_bytecode: Bytecode,
    callee_bytecode: Bytecode,
    expected_storage: Dict,
):
    """
    Test transient storage in different reentrancy contexts after selfdestructing.
    """
    env = Environment()

    caller_address = pre.deploy_contract(code=caller_bytecode)

    data: Hash | Bytecode
    if pre_existing_contract:
        callee_address = pre.deploy_contract(code=callee_bytecode)
        data = Hash(callee_address)
    else:
        callee_address = compute_create_address(address=caller_address, nonce=1)
        data = Initcode(deploy_code=callee_bytecode)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
        gas_limit=1_000_000,
        data=data,
    )

    expected_storage[0] = callee_address

    post: Dict = {caller_address: Account(storage=expected_storage)}

    if pre_existing_contract:
        post[callee_address] = Account(code=callee_bytecode)
    else:
        post[callee_address] = Account.NONEXISTENT

    state_test(env=env, pre=pre, post=post, tx=tx)
