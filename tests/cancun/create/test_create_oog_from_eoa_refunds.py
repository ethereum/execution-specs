"""
Tests for CREATE OOG scenarios from EOA refunds.

Tests that verify refunds are not applied on contract creation
when the creation runs out of gas.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Op,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

pytestmark = pytest.mark.valid_from("Cancun")


class OogScenario(Enum):
    """Different ways a CREATE can run out of gas or succeed."""

    NO_OOG = "no_oog"
    OOG_CODE_DEPOSIT = "oog_code_deposit"  # OOG due to code deposit cost
    OOG_INVALID = "oog_invalid_opcode"  # OOG due to INVALID opcode


class RefundType(Enum):
    """Different refund mechanisms tested."""

    SSTORE_DIRECT = "sstore_in_init_code"
    SSTORE_CALL = "sstore_via_call"
    SSTORE_DELEGATECALL = "sstore_via_delegatecall"
    SSTORE_CALLCODE = "sstore_via_callcode"
    SELFDESTRUCT = "selfdestruct_via_call"
    LOG_OP = "log_operations"
    NESTED_CREATE = "nested_create_in_init_code"
    NESTED_CREATE2 = "nested_create2_in_init_code"


@dataclass
class HelperContracts:
    """Container for deployed helper contract addresses."""

    sstore_refund: Address
    selfdestruct: Address
    log_op: Address
    init_code: Address


def deploy_helper_contracts(pre: Alloc) -> HelperContracts:
    """Deploy all helper contracts needed for the tests."""
    # Simple contract to reset sstore and get refund: sstore(1, 0)
    sstore_refund_code = Op.SSTORE(1, 0) + Op.STOP
    sstore_refund = pre.deploy_contract(
        code=sstore_refund_code,
        storage={1: 1},
    )

    # Simple contract that self-destructs to refund
    selfdestruct_code = Op.SELFDESTRUCT(Op.ORIGIN) + Op.STOP
    selfdestruct = pre.deploy_contract(
        code=selfdestruct_code,
        storage={1: 1},
    )

    # Simple contract that performs log operations
    log_op_code = (
        Op.MSTORE(0, 0xFF)
        + Op.LOG0(0, 32)
        + Op.LOG1(0, 32, 0xFA)
        + Op.LOG2(0, 32, 0xFA, 0xFB)
        + Op.LOG3(0, 32, 0xFA, 0xFB, 0xFC)
        + Op.LOG4(0, 32, 0xFA, 0xFB, 0xFC, 0xFD)
        + Op.STOP
    )
    log_op = pre.deploy_contract(
        code=log_op_code,
        storage={1: 1},
    )

    # Init code that successfully creates contract but contains a refund
    # sstore(0, 1); sstore(0, 0); return(0, 1)
    init_code_with_refund = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.RETURN(0, 1)
    init_code = pre.deploy_contract(
        code=init_code_with_refund,
    )

    return HelperContracts(
        sstore_refund=sstore_refund,
        selfdestruct=selfdestruct,
        log_op=log_op,
        init_code=init_code,
    )


def build_init_code(
    refund_type: RefundType,
    oog_scenario: OogScenario,
    helpers: HelperContracts,
) -> bytes:
    """
    Build init code based on refund type and OOG scenario.

    All init codes:
    - Write to storage slot 0
    - Optionally trigger refund mechanism
    - End with either small return (success) or large return/INVALID (OOG)
    """
    # Common prefix: sstore(0, 1) to mark storage access
    prefix = Op.SSTORE(0, 1)

    # Build the refund-triggering portion based on type
    if refund_type == RefundType.SSTORE_DIRECT:
        # Direct sstore refund: sstore(1, 1); sstore(1, 0)
        refund_code = Op.SSTORE(1, 1) + Op.SSTORE(1, 0)

    elif refund_type == RefundType.SSTORE_CALL:
        # Call to sstore refund helper
        refund_code = Op.POP(
            Op.CALL(Op.GAS, helpers.sstore_refund, 0, 0, 0, 0, 0)
        )

    elif refund_type == RefundType.SSTORE_DELEGATECALL:
        # Delegatecall to sstore refund helper (needs local storage setup)
        refund_code = Op.SSTORE(1, 1) + Op.POP(
            Op.DELEGATECALL(Op.GAS, helpers.sstore_refund, 0, 0, 0, 0)
        )

    elif refund_type == RefundType.SSTORE_CALLCODE:
        refund_code = Op.SSTORE(1, 1) + Op.POP(
            Op.CALLCODE(Op.GAS, helpers.sstore_refund, 0, 0, 0, 0, 0)
        )

    elif refund_type == RefundType.SELFDESTRUCT:
        refund_code = Op.POP(
            Op.CALL(Op.GAS, helpers.selfdestruct, 0, 0, 0, 0, 0)
        )

    elif refund_type == RefundType.LOG_OP:
        # call to log op helper
        refund_code = Op.POP(Op.CALL(Op.GAS, helpers.log_op, 0, 0, 0, 0, 0))

    elif refund_type == RefundType.NESTED_CREATE:
        # Nested CREATE with refund in init code
        # extcodecopy the init code helper and CREATE from it
        refund_code = (
            Op.SSTORE(1, 1)
            + Op.SSTORE(1, 0)
            + Op.EXTCODECOPY(
                helpers.init_code, 0, 0, Op.EXTCODESIZE(helpers.init_code)
            )
            + Op.POP(Op.CREATE(0, 0, Op.EXTCODESIZE(helpers.init_code)))
        )

    elif refund_type == RefundType.NESTED_CREATE2:
        # Nested CREATE2 with refund in init code
        refund_code = (
            Op.SSTORE(1, 1)
            + Op.SSTORE(1, 0)
            + Op.EXTCODECOPY(
                helpers.init_code, 0, 0, Op.EXTCODESIZE(helpers.init_code)
            )
            + Op.POP(Op.CREATE2(0, 0, Op.EXTCODESIZE(helpers.init_code), 0))
        )
    else:
        refund_code = Op.STOP

    # Build the ending based on OOG scenario
    if oog_scenario == OogScenario.NO_OOG:
        # Return 1 byte of code (cheap code deposit)
        if refund_type in (
            RefundType.NESTED_CREATE,
            RefundType.NESTED_CREATE2,
        ):
            # For nested creates, return after init code length
            ending = Op.RETURN(Op.ADD(Op.EXTCODESIZE(helpers.init_code), 1), 1)
        else:
            ending = Op.RETURN(0, 1)

    elif oog_scenario == OogScenario.OOG_CODE_DEPOSIT:
        # Return 5000 bytes of code - code deposit cost exceeds available gas
        if refund_type in (
            RefundType.NESTED_CREATE,
            RefundType.NESTED_CREATE2,
        ):
            ending = Op.RETURN(
                Op.ADD(Op.EXTCODESIZE(helpers.init_code), 1), 5000
            )
        else:
            ending = Op.RETURN(0, 5000)

    elif oog_scenario == OogScenario.OOG_INVALID:
        # INVALID opcode causes OOG (all gas consumed, no refund)
        ending = Op.INVALID

    else:
        ending = Op.STOP

    return bytes(prefix + refund_code + ending)


@pytest.mark.parametrize(
    "oog_scenario",
    [
        pytest.param(OogScenario.NO_OOG, id="no_oog"),
        pytest.param(OogScenario.OOG_CODE_DEPOSIT, id="oog_code_deposit"),
        pytest.param(OogScenario.OOG_INVALID, id="oog_invalid_opcode"),
    ],
)
@pytest.mark.parametrize(
    "refund_type",
    [
        pytest.param(RefundType.SSTORE_DIRECT, id="sstore_direct"),
        pytest.param(RefundType.SSTORE_CALL, id="sstore_call"),
        pytest.param(RefundType.SSTORE_DELEGATECALL, id="sstore_delegatecall"),
        pytest.param(RefundType.SSTORE_CALLCODE, id="sstore_callcode"),
        pytest.param(RefundType.SELFDESTRUCT, id="selfdestruct"),
        pytest.param(RefundType.LOG_OP, id="log_op"),
        pytest.param(RefundType.NESTED_CREATE, id="nested_create"),
        pytest.param(RefundType.NESTED_CREATE2, id="nested_create2"),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CreateOOGFromEOARefundsFiller.yml",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1831"],
)
def test_create_oog_from_eoa_refunds(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    refund_type: RefundType,
    oog_scenario: OogScenario,
    fork: Fork,
) -> None:
    """
    Test CREATE from EOA with various refund mechanisms and OOG scenarios.

    Verifies that:
    1. Refunds are not applied when contract creation runs Out of Gas
    2. When OOG occurs, the sender's balance is fully consumed (no refund)
    3. When OOG occurs, the contract is not created

    For BAL (Block Access List) tracking:
    - NoOoG: Storage writes should be recorded as `storage_changes`
    - OoG: Storage writes should be converted to `storage_reads` since
           the CREATE failed and all state changes were reverted
    """
    helpers = deploy_helper_contracts(pre)
    sender = pre.fund_eoa(amount=4_000_000)
    init_code = build_init_code(refund_type, oog_scenario, helpers)
    created_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=init_code,
        gas_limit=400_000,
    )

    post: Dict[Address, Account | None] = {
        sender: Account(nonce=1),
    }

    if oog_scenario == OogScenario.NO_OOG:
        # contract created with code 0x00 (1 byte from memory)
        if refund_type == RefundType.NESTED_CREATE:
            # Nested CREATE increments the created contract's nonce to 2
            post[created_address] = Account(
                nonce=2,
                code=b"\x00",
                storage={0: 1},  # successful write
            )

            nested_created = compute_create_address(
                address=created_address, nonce=1
            )
            post[nested_created] = Account(
                nonce=1,
                code=b"\x00",
                storage={},
            )
        elif refund_type == RefundType.NESTED_CREATE2:
            # nested create2 increments the created contract's nonce to 2
            post[created_address] = Account(
                nonce=2,
                code=b"\x00",
                storage={0: 1},
            )

            nested_created = compute_create2_address(
                address=created_address,
                salt=0,
                initcode=Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.RETURN(0, 1),
            )
            post[nested_created] = Account(
                nonce=1,
                code=b"\x00",
                storage={},
            )
        else:
            post[created_address] = Account(
                nonce=1,
                code=b"\x00",
                storage={0: 1},
            )
        post[sender] = Account(nonce=1)
    else:
        # OOG case: contract not created, sender balance is fully consumed
        post[created_address] = Account.NONEXISTENT
        post[sender] = Account(
            nonce=1,
            balance=0,
        )

    if refund_type == RefundType.SELFDESTRUCT:
        selfdestruct_code = Op.SELFDESTRUCT(Op.ORIGIN) + Op.STOP
        if oog_scenario == OogScenario.NO_OOG:
            # selfdestruct succeeded, balance is 0
            post[helpers.selfdestruct] = Account(
                balance=0,
                nonce=1,
            )
        else:
            # OOG: selfdestruct reverted, helper unchanged
            post[helpers.selfdestruct] = Account(
                code=bytes(selfdestruct_code),
                nonce=1,
                storage={1: 1},
            )

    bal_expectation = None
    if fork.header_bal_hash_required():
        if oog_scenario == OogScenario.NO_OOG:
            # Success: storage write to slot 0 persists
            expected_nonce = (
                2
                if refund_type
                in (RefundType.NESTED_CREATE, RefundType.NESTED_CREATE2)
                else 1
            )
            created_bal = BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(
                        block_access_index=1, post_nonce=expected_nonce
                    )
                ],
                storage_changes=[
                    BalStorageSlot(
                        slot=0,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=1
                            )
                        ],
                    ),
                ],
                storage_reads=(
                    # noop write 0 -> 1 -> 0
                    [1]
                    if refund_type
                    in (
                        RefundType.SSTORE_DIRECT,
                        RefundType.SSTORE_DELEGATECALL,
                        RefundType.SSTORE_CALLCODE,
                        RefundType.NESTED_CREATE,
                        RefundType.NESTED_CREATE2,
                    )
                    else []
                ),
            )
        else:
            # OOG case: storage writes converted to reads
            # All refund types write to slot 0, most also write to slot 1
            if refund_type in (
                RefundType.SSTORE_DIRECT,
                RefundType.SSTORE_DELEGATECALL,
                RefundType.SSTORE_CALLCODE,
                RefundType.NESTED_CREATE,
                RefundType.NESTED_CREATE2,
            ):
                # write to both slot 0 and slot 1 (noop write 0 -> 1 -> 0)
                created_bal = BalAccountExpectation(
                    storage_changes=[],
                    storage_reads=[0, 1],
                )
            else:
                # SSTORE_CALL, SELFDESTRUCT, LOG_OP only write to slot 0
                created_bal = BalAccountExpectation(
                    storage_changes=[],
                    storage_reads=[0],
                )
        bal_expectation = BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                created_address: created_bal,
            }
        )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=bal_expectation)],
        post=post,
    )
