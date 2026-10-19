"""
Verify gas refunds earned inside a CREATE2's init code (storage clears,
via direct stores and CALL/CALLCODE/DELEGATECALL helpers, selfdestructs,
and nested creations) against out-of-gas boundaries: each scenario runs
once completing normally and twice dying, on an oversized code deposit
and on an INVALID that pins the refund bookkeeping.

Ported from:
state_tests/stCreate2/Create2OOGFromCallRefundsFiller.yml

@manually-enhanced: Do not overwrite. The SSTORE pairs solc had folded
out of five init codes are restored, so the refunds the OoG arms must
discard are actually earned. The transaction budget and the sender's
funding derive from the fork: the ported 400k regular budget plus the
restored sets and the deepest arm's outstanding EIP-8037 state gas,
guarded to stay below the 5000-byte deposit charge that starves the OoG
arms.
"""

from enum import Enum, auto

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_PRICE = 10
# The ported budget, proven to cover every NoOoG arm's regular gas.
PORTED_GAS_LIMIT = 400_000
# The OoG arms return this much memory as code. The deposit charge is
# what must exceed the transaction budget so they starve.
OOG_DEPOSIT_SIZE = 0x1388
# Init codes return from here, past anything any of them writes to
# memory, so the byte a completing arm deposits is always zero.
DEPOSIT_OFFSET = 0x20


class Refund(Enum):
    """How an init code earns the refund the arm is about."""

    DIRECT = auto()
    """Clears a slot it set itself."""
    CALL = auto()
    """Has a callee clear the callee's own slot."""
    DELEGATECALL = auto()
    """Runs the callee's clear in its own storage."""
    CALLCODE = auto()
    """As DELEGATECALL, with its own address as the caller."""
    SELFDESTRUCT = auto()
    """Calls a contract that destroys itself."""
    LOGS = auto()
    """Calls a contract that only emits logs, earning nothing."""
    CREATE = auto()
    """Nests a CREATE that clears a slot."""
    CREATE2 = auto()
    """Nests a CREATE2 that clears a slot."""


class Outcome(Enum):
    """How the init code ends, which decides whether refunds survive."""

    COMPLETES = auto()
    """Deposits one byte and returns normally."""
    OOG_DEPOSIT = auto()
    """Requests a deposit the budget cannot pay for."""
    OOG_INVALID = auto()
    """Ends on INVALID, burning whatever gas is left."""


NESTED = (Refund.CREATE, Refund.CREATE2)
"""Arms whose init code creates a further contract."""


@pytest.mark.ported_from(
    ["state_tests/stCreate2/Create2OOGFromCallRefundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "outcome", list(Outcome), ids=lambda o: o.name.lower()
)
@pytest.mark.parametrize("refund", list(Refund), ids=lambda r: r.name.lower())
def test_create2_oog_from_call_refunds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    refund: Refund,
    outcome: Outcome,
) -> None:
    """Init-code refunds survive only a completing CREATE2."""
    # The entry point takes the init code straight from the
    # transaction's calldata. The ported filler instead passed the
    # address of a contract holding those bytes and EXTCODECOPYed them,
    # which needed a carrier contract deployed per arm.
    #
    # A failed CREATE2 falls through to INVALID, which burns whatever
    # gas is left; that is what makes the refund bookkeeping in the OoG
    # arms deterministic.
    entry_code = (
        Op.CALLDATACOPY(size=Op.CALLDATASIZE)
        + Conditional(
            condition=Op.ISZERO(
                Op.CREATE2(
                    value=0x0, offset=0x0, size=Op.CALLDATASIZE, salt=0x0
                )
            ),
            if_true=Op.INVALID,
        )
        + Op.STOP
    )
    entry = pre.deploy_contract(code=entry_code)

    nested_initcode = (
        Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x0, value=0x0)
        + Op.RETURN(offset=0x0, size=0x1)
    )

    body: Bytecode
    post: dict[Address, Account | None] = {}
    match refund:
        case Refund.DIRECT:
            # Sets a second slot and clears it itself.
            body = (
                Op.SSTORE(key=0x0, value=0x1)
                + Op.SSTORE(key=0x1, value=0x1)
                + Op.SSTORE(key=0x1, value=0x0)
            )
        case Refund.CALL | Refund.DELEGATECALL | Refund.CALLCODE:
            # The callee clears a slot of its own.
            clear_target_code = Op.SSTORE(key=0x1, value=0x0) + Op.STOP
            clear_target = pre.deploy_contract(
                code=clear_target_code,
                storage={1: 1},
            )
            sstore_code = Op.SSTORE(key=0x0, value=0x1)
            if refund == Refund.CALL:
                call_opcode = Op.CALL
            elif refund == Refund.DELEGATECALL:
                sstore_code += Op.SSTORE(key=0x1, value=0x1)
                call_opcode = Op.DELEGATECALL
            else:
                sstore_code += Op.SSTORE(key=0x1, value=0x1)
                call_opcode = Op.CALLCODE
            body = sstore_code + call_opcode(address=clear_target)
            post[clear_target] = Account(
                storage={
                    1: int(
                        refund != Refund.CALL or outcome != Outcome.COMPLETES
                    )
                }
            )
        case Refund.SELFDESTRUCT:
            # The callee destroys itself.
            selfdestruct_target_code = Op.SELFDESTRUCT(address=Op.ORIGIN)
            selfdestruct_target = pre.deploy_contract(
                code=selfdestruct_target_code,
                storage={1: 1},
            )
            body = Op.SSTORE(key=0x0, value=0x1) + Op.CALL(
                gas=Op.GAS, address=selfdestruct_target
            )
            if outcome is Outcome.COMPLETES:
                post[selfdestruct_target] = Account(balance=0, nonce=1)
            else:
                post[selfdestruct_target] = Account(
                    storage={1: 1}, code=selfdestruct_target_code, nonce=1
                )
        case Refund.LOGS:
            # The callee only emits logs, so nothing is refunded.
            log_target_code = (
                Op.MSTORE(offset=0x0, value=0xFF)
                + Op.LOG0(offset=0x0, size=0x20)
                + Op.LOG1(offset=0x0, size=0x20, topic_1=0xFA)
                + Op.LOG2(offset=0x0, size=0x20, topic_1=0xFA, topic_2=0xFB)
                + Op.LOG3(
                    offset=0x0,
                    size=0x20,
                    topic_1=0xFA,
                    topic_2=0xFB,
                    topic_3=0xFC,
                )
                + Op.LOG4(
                    offset=0x0,
                    size=0x20,
                    topic_1=0xFA,
                    topic_2=0xFB,
                    topic_3=0xFC,
                    topic_4=0xFD,
                )
                + Op.STOP
            )
            body = Op.SSTORE(key=0x0, value=0x1) + Op.CALL(
                gas=Op.GAS,
                address=pre.deploy_contract(
                    code=log_target_code, storage={1: 1}
                ),
            )
        case Refund.CREATE | Refund.CREATE2:
            nested_carrier = pre.deploy_contract(code=nested_initcode)
            nested_size = Op.EXTCODESIZE(address=nested_carrier)

            assert DEPOSIT_OFFSET >= len(nested_initcode), (
                "the deposit offset must clear the copied init code"
            )
            body = (
                Op.SSTORE(key=0x0, value=0x1)
                + Op.SSTORE(key=0x1, value=0x1)
                + Op.SSTORE(key=0x1, value=0x0)
                + Op.EXTCODECOPY(
                    address=nested_carrier,
                    dest_offset=0x0,
                    offset=0x0,
                    size=nested_size,
                )
            )
            if refund == Refund.CREATE:
                body += Op.CREATE(offset=0x0, size=nested_size)
            else:
                body += Op.CREATE2(offset=0x0, size=nested_size)

    match outcome:
        case Outcome.COMPLETES:
            # Deposit a single zero byte and return normally.
            ends = Op.RETURN(offset=DEPOSIT_OFFSET, size=0x1)
        case Outcome.OOG_DEPOSIT:
            # Ask for more code than the budget can pay to deposit.
            ends = Op.RETURN(
                offset=DEPOSIT_OFFSET,
                size=OOG_DEPOSIT_SIZE,
                code_deposit_size=OOG_DEPOSIT_SIZE,
            )
        case Outcome.OOG_INVALID:
            # Burn whatever gas is left.
            ends = Op.INVALID

    initcode = body + ends

    # The ported budget was sized for the compiled programs, in which
    # solc had folded a fresh set out of the deepest arm's two init codes
    # (restored here). On top of it, EIP-8037 charges state gas: the
    # deepest arm (create inside create2) makes three fresh sets and two
    # new accounts and deposits one byte at each depth. All state terms
    # are zero before Amsterdam.
    fresh_set = Op.SSTORE(
        key=0x0, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    new_account_state = Op.CREATE2(
        value=0x0, offset=0x0, size=0x0, salt=0x0
    ).state_cost(fork)
    # Passing the init code as calldata adds intrinsic gas to the old
    # carrier-address setup; derive that allowance from its actual bytes.
    intrinsic = fork.transaction_intrinsic_cost_calculator()
    calldata_gas = intrinsic(calldata=initcode) - intrinsic()
    tx_gas_limit = (
        PORTED_GAS_LIMIT
        + 2 * fresh_set.execution_cost(fork)
        + 3 * fresh_set.state_cost(fork)
        + 2 * new_account_state
        + 2 * fork.code_deposit_state_gas(code_size=1)
        + calldata_gas
    )
    # The budget must stay below the oversized deposit charge so the
    # OoG arms keep starving on it on every fork.
    if outcome == Outcome.OOG_DEPOSIT:
        assert tx_gas_limit < ends.gas_cost(fork), (
            "the OoG arms must stay starved"
        )

    # The exact funding makes the OoG arms' post-state balance zero.
    sender = pre.fund_eoa(amount=tx_gas_limit * GAS_PRICE)

    created = compute_create2_address(entry, 0, initcode)
    nested_created_address: Address | None = None
    if refund in NESTED:
        nested_created_address = compute_create_address(
            address=created,
            nonce=1,
            salt=0,
            initcode=nested_initcode,
            opcode=Op.CREATE if refund == Refund.CREATE else Op.CREATE2,
        )

    if outcome is Outcome.COMPLETES:
        # The CREATE2 finished, so the refunds it earned stand and the
        # one deposited byte survives.
        post[sender] = Account(nonce=1)
        post[created] = Account(
            storage={0: 1}, code=Op.STOP, nonce=2 if refund in NESTED else 1
        )
        if nested_created_address:
            post[nested_created_address] = Account(
                storage={}, code=Op.STOP, nonce=1
            )
    else:
        # The frame died, so nothing it did survives and the sender is
        # charged for the whole budget.
        post[sender] = Account(balance=0, nonce=1)
        post[created] = Account.NONEXISTENT
        if nested_created_address:
            post[nested_created_address] = Account.NONEXISTENT

    tx = Transaction(
        sender=sender,
        to=entry,
        data=initcode,
        gas_limit=tx_gas_limit,
        gas_price=GAS_PRICE,
    )

    state_test(pre=pre, post=post, tx=tx)
