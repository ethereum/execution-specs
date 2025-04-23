"""Test related to making calls to accounts having a delegation set on them."""

import itertools
from enum import Enum, auto, unique

import pytest

from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

pytestmark = pytest.mark.valid_from("Prague")
REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7702.md"
REFERENCE_SPEC_VERSION = "37ce65b354756ac51c6a6f114e15de4a523a7f2e"

LEGACY_CALL_FAILURE = 0
LEGACY_CALL_SUCCESS = 1

"""Storage addresses for common testing fields"""
_slot = itertools.count(1)
slot_code_worked = next(_slot)
slot_call_result = next(_slot)
slot_returndata = next(_slot)
slot_last_slot = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015


identity = Address(0x04)


@unique
class TargetAccountType(Enum):
    """Kinds of target accounts for calls."""

    EMPTY = auto()
    EOA = auto()
    LEGACY_CONTRACT = auto()
    LEGACY_CONTRACT_INVALID = auto()
    LEGACY_CONTRACT_REVERT = auto()
    IDENTITY_PRECOMPILE = auto()

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return f"{self.name}"


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Sender of the transaction."""
    return pre.fund_eoa()


@pytest.fixture
def target_address(pre: Alloc, target_account_type: TargetAccountType) -> Address:
    """Target address of the call depending on required type of account."""
    match target_account_type:
        case TargetAccountType.EMPTY:
            return pre.fund_eoa(amount=0)
        case TargetAccountType.EOA:
            return pre.fund_eoa()
        case TargetAccountType.LEGACY_CONTRACT:
            return pre.deploy_contract(
                code=Op.STOP,
            )
        case TargetAccountType.LEGACY_CONTRACT_INVALID:
            return pre.deploy_contract(
                code=Op.INVALID,
            )
        case TargetAccountType.LEGACY_CONTRACT_REVERT:
            return pre.deploy_contract(
                code=Op.REVERT(0, 0),
            )
        case TargetAccountType.IDENTITY_PRECOMPILE:
            return identity


@pytest.mark.parametrize("target_account_type", TargetAccountType)
@pytest.mark.parametrize("delegate", [True, False])
@pytest.mark.parametrize("call_from_initcode", [True, False])
def test_delegate_call_targets(
    state_test: StateTestFiller,
    pre: Alloc,
    target_account_type: TargetAccountType,
    target_address: Address,
    delegate: bool,
    call_from_initcode: bool,
):
    """
    Test contracts doing delegatecall to various targets resolved via 7702
    delegation.
    """
    env = Environment()

    if delegate:
        target_address = pre.fund_eoa(0, delegation=target_address)

    delegate_call_code = Op.SSTORE(
        slot_call_result, Op.DELEGATECALL(address=target_address)
    ) + Op.SSTORE(slot_code_worked, value_code_worked)

    if call_from_initcode:
        # Call from initcode
        caller_contract = delegate_call_code + Op.RETURN(0, 0)
        tx = Transaction(
            sender=pre.fund_eoa(),
            to=None,
            data=caller_contract,
            gas_limit=4_000_000,
        )
        calling_contract_address = tx.created_contract
    else:
        # Normal call from existing contract
        caller_contract = delegate_call_code + Op.STOP
        calling_contract_address = pre.deploy_contract(caller_contract)

        tx = Transaction(
            sender=pre.fund_eoa(),
            to=calling_contract_address,
            gas_limit=4_000_000,
        )

    calling_storage = {
        slot_code_worked: value_code_worked,
        slot_call_result: LEGACY_CALL_FAILURE
        if target_account_type
        in [TargetAccountType.LEGACY_CONTRACT_INVALID, TargetAccountType.LEGACY_CONTRACT_REVERT]
        else LEGACY_CALL_SUCCESS,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
