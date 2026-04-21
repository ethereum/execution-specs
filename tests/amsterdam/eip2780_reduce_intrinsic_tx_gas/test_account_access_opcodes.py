"""
Tests for EIP-2780 Reduce Transaction Intrinsic Cost.

Tests that account access opcodes (BALANCE, EXTCODESIZE, EXTCODECOPY,
EXTCODEHASH) charge cold access gas correctly based on whether the
target account has code.
"""

import enum
from typing import Optional

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    keccak256,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")

# Contract code with a distinctive byte pattern: EXTCODESIZE returns 2,
# EXTCODECOPY copies 0x60FF followed by zeros (non-zero uint256).
_CONTRACT_CODE = Op.PUSH1(0xFF)


class AccountAccessOpcode(enum.Enum):
    """Account state access opcodes affected by EIP-2780."""

    BALANCE = "balance"
    EXTCODESIZE = "extcodesize"
    EXTCODEHASH = "extcodehash"
    EXTCODECOPY = "extcodecopy"


class AccessScenario(enum.Enum):
    """Whether the opcode access attempt succeeds or runs out of gas."""

    OOG = "oog"
    SUCCESS = "success"


@pytest.mark.parametrize(
    "accessed_opcode",
    list(AccountAccessOpcode),
    ids=lambda o: o.value,
)
@pytest.mark.parametrize(
    "accessed_account_type",
    [
        pytest.param(RecipientType.EOA, id="eoa"),
        pytest.param(RecipientType.CONTRACT, id="contract"),
        pytest.param(RecipientType.EMPTY_ACCOUNT, id="empty_account"),
        pytest.param(RecipientType.DELEGATION_7702, id="delegation_7702"),
    ],
)
@pytest.mark.parametrize(
    "accessed_address_warm",
    [
        pytest.param(False, id="cold"),
        pytest.param(True, id="warm"),
    ],
)
@pytest.mark.parametrize(
    "access_scenario",
    list(AccessScenario),
    ids=lambda s: s.value,
)
def test_account_access_opcode(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    accessed_opcode: AccountAccessOpcode,
    accessed_account_type: RecipientType,
    accessed_address_warm: bool,
    access_scenario: AccessScenario,
) -> None:
    """
    Test account access opcode gas under EIP-2780.

    EIP-2780 splits cold access cost by whether the target has code:
    - G_COLD_ACCOUNT_COST_CODE (2600) for accounts with code.
    - G_COLD_ACCOUNT_COST_NO_CODE (500) for accounts without.

    The checker stores the opcode result in slot 0, and a success
    marker (1) in slot 1. If the access opcode OOGs, neither SSTORE
    executes and both slots remain at their initial value (0). The
    success marker always distinguishes OOG from SUCCESS, even when
    the result in slot 0 is zero.
    """
    target: Address
    target_balance: int
    target_code_bytes: bytes
    address_has_code: bool

    match accessed_account_type:
        case RecipientType.EOA:
            target = pre.fund_eoa(amount=10**18)
            target_balance = 10**18
            target_code_bytes = b""
            address_has_code = False
        case RecipientType.CONTRACT:
            target = pre.deploy_contract(code=_CONTRACT_CODE, balance=100)
            target_balance = 100
            target_code_bytes = bytes(_CONTRACT_CODE)
            address_has_code = True
        case RecipientType.EMPTY_ACCOUNT:
            target = pre.fund_eoa(amount=0)
            target_balance = 0
            target_code_bytes = b""
            address_has_code = False
        case RecipientType.DELEGATION_7702:
            delegated_to = pre.deploy_contract(code=Op.STOP)
            deleg_code = Spec7702.delegation_designation(delegated_to)
            target = pre.deploy_contract(code=deleg_code, balance=100)
            target_balance = 100
            target_code_bytes = bytes(deleg_code)
            address_has_code = True
        case _:
            raise ValueError(
                f"Unsupported account type: {accessed_account_type}"
            )

    access_list: Optional[list[AccessList]] = (
        [AccessList(address=target, storage_keys=[])]
        if accessed_address_warm
        else None
    )

    # Compute the expected opcode result stored in slot 0 on SUCCESS.
    expected_slot0: int
    match accessed_opcode:
        case AccountAccessOpcode.BALANCE:
            expected_slot0 = target_balance
        case AccountAccessOpcode.EXTCODESIZE:
            expected_slot0 = len(target_code_bytes)
        case AccountAccessOpcode.EXTCODEHASH:
            if accessed_account_type == RecipientType.EMPTY_ACCOUNT:
                # Empty (non-existent) account: EXTCODEHASH returns 0.
                expected_slot0 = 0
            else:
                expected_slot0 = int.from_bytes(
                    keccak256(target_code_bytes), "big"
                )
        case AccountAccessOpcode.EXTCODECOPY:
            # First 32 bytes of code, zero-padded to 32 bytes, as uint256.
            expected_slot0 = int.from_bytes(
                (target_code_bytes + b"\x00" * 32)[:32], "big"
            )

    # Build the bytecode that evaluates the opcode and leaves the result on
    # the stack.  For EXTCODECOPY there is no stack result: we copy to
    # memory[0:32] and then load it back with MLOAD.
    result_bytecode: Bytecode
    match accessed_opcode:
        case AccountAccessOpcode.BALANCE:
            result_bytecode = Op.BALANCE(
                address=target,
                address_warm=accessed_address_warm,
                address_has_code=address_has_code,
            )
        case AccountAccessOpcode.EXTCODESIZE:
            result_bytecode = Op.EXTCODESIZE(
                address=target,
                address_warm=accessed_address_warm,
                address_has_code=address_has_code,
            )
        case AccountAccessOpcode.EXTCODEHASH:
            result_bytecode = Op.EXTCODEHASH(
                address=target,
                address_warm=accessed_address_warm,
                address_has_code=address_has_code,
            )
        case AccountAccessOpcode.EXTCODECOPY:
            # Copy 32 bytes into memory then load them back onto the stack.
            result_bytecode = Op.EXTCODECOPY(
                address=target,
                dest_offset=0,
                offset=0,
                size=32,
                address_warm=accessed_address_warm,
                address_has_code=address_has_code,
                data_size=32,
                new_memory_size=32,
                old_memory_size=0,
            ) + Op.MLOAD(
                offset=0,
                # Memory is already at 32 bytes from EXTCODECOPY; no expansion.
                new_memory_size=32,
                old_memory_size=32,
            )

    # Slot 0: the opcode result.
    # Slot 1: success marker (1 iff both SSTOREs ran).
    checker_code = (
        Op.SSTORE(
            key=0,
            value=result_bytecode,
            key_warm=False,
            original_value=0,
            new_value=expected_slot0,
        )
        + Op.SSTORE(
            key=1, value=1, key_warm=False, original_value=0, new_value=1
        )
        + Op.STOP
    )
    checker = pre.deploy_contract(code=checker_code)
    sender = pre.fund_eoa(amount=10**18)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        recipient_type=RecipientType.CONTRACT,
        return_cost_deducted_prior_execution=True,
    )

    gsc = fork.gas_costs()
    cold_access = (
        gsc.WARM_ACCESS
        if accessed_address_warm
        else gsc.COLD_ACCOUNT_COST_CODE
        if address_has_code
        else gsc.COLD_ACCOUNT_COST_NO_CODE
    )
    # EXTCODECOPY pushes 4 args (address, dest_offset, offset, size);
    # all other opcodes push 1 arg (address).
    n_push_args = (
        4 if accessed_opcode == AccountAccessOpcode.EXTCODECOPY else 1
    )

    if access_scenario == AccessScenario.OOG:
        # Push all opcode arguments onto the stack, then give one less gas
        # than the access cost — the opcode itself OOGs immediately.
        gas_limit = (
            intrinsic_cost + gsc.VERY_LOW * n_push_args + cold_access - 1
        )
        expected_storage = {0: 0, 1: 0}
    else:  # SUCCESS
        gas_limit = intrinsic_cost + checker_code.gas_cost(fork)
        expected_storage = {0: expected_slot0, 1: 1}

    tx = Transaction(
        sender=sender,
        to=checker,
        gas_limit=gas_limit,
        access_list=access_list,
    )

    post = {checker: Account(storage=expected_storage)}

    state_test(pre=pre, tx=tx, post=post)
