"""
What is left of a contract that self-destructs in the transaction that
created it.

Tests for [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780).

Such a contract may self-destruct more than once, and may receive more
value afterwards. At the end of the transaction, before EIP-8246 the
account is deleted and any balance it still holds is burned; from EIP-8246
on its nonce, code and storage are cleared but the balance stays, leaving a
balance-only account behind.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BlockAccessListExpectation,
    Bytecode,
    Conditional,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.checklists import EIPChecklist

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "1b6a0e94cc47e859b9866e570391cf37dc55059a"

pytestmark = pytest.mark.valid_from("Cancun")

OTHER_BALANCE = 1
SEND_AMOUNT = 1

SD_SELF = "selfdestruct_to_self"
SD_OTHER = "selfdestruct_to_other"
SEND = "send_value"


def finalized(fork: Fork, balance: int) -> Account | None:
    """
    Expected account for a contract that self-destructed in the transaction
    that created it, holding ``balance`` when the transaction ended. It is
    deleted, or under EIP-8246 kept with only that balance.
    """
    if fork.is_eip_enabled(8246) and balance > 0:
        return Account(balance=balance, nonce=0, code=b"", storage={})
    return Account.NONEXISTENT


def finalized_bal(
    fork: Fork, balance: int, storage_reads: list[int]
) -> BalAccountExpectation:
    """Block access list entry expected for that same contract."""
    kept = balance if fork.is_eip_enabled(8246) else 0
    if kept == 0 and not storage_reads:
        return BalAccountExpectation.empty()
    balance_changes = []
    if kept > 0:
        balance_changes = [
            BalBalanceChange(block_access_index=1, post_balance=kept)
        ]
    return BalAccountExpectation(
        nonce_changes=[],
        code_changes=[],
        storage_changes=[],
        storage_reads=storage_reads,
        balance_changes=balance_changes,
    )


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "initial_balance",
    [pytest.param(0, id="zero_balance"), pytest.param(3, id="funded")],
)
@pytest.mark.parametrize(
    "steps",
    [
        pytest.param((SD_SELF,), id="case01_self"),
        pytest.param((SD_SELF, SD_SELF), id="case02_self_self"),
        pytest.param((SD_SELF, SD_OTHER), id="case03_self_other"),
        pytest.param((SD_OTHER, SD_SELF), id="case04_other_self"),
        pytest.param((SD_OTHER, SEND), id="case05_other_send"),
        pytest.param((SD_OTHER, SEND, SEND), id="case06_other_send_send"),
        pytest.param((SD_OTHER, SEND, SD_OTHER), id="case07_other_send_other"),
        pytest.param((SD_OTHER, SEND, SD_SELF), id="case08_other_send_self"),
        pytest.param((SD_SELF, SEND), id="case09_self_send"),
        pytest.param((SD_SELF, SEND, SEND), id="case10_self_send_send"),
        pytest.param((SD_SELF, SEND, SD_OTHER), id="case11_self_send_other"),
        pytest.param((SD_SELF, SEND, SD_SELF), id="case12_self_send_self"),
    ],
)
@EIPChecklist.Opcode.Test.ExecutionContext.Call(eip=[8246])
@EIPChecklist.Opcode.Test.GasUsage.ExtraGas(eip=[8246])
@EIPChecklist.Opcode.Test.Terminating.Scenarios.SubLevel(eip=[8246])
def test_selfdestruct_sequences(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    steps: tuple[str, ...],
    initial_balance: int,
) -> None:
    """
    Cases 1-12 of the EIP-8246 test list: a contract created in this
    transaction runs a sequence of self-destructs and value sends, and
    whatever it still holds at the end is what it keeps.
    """
    sender = pre.fund_eoa()
    other = pre.fund_eoa(amount=OTHER_BALANCE)

    # The victim self-destructs to the address in calldata, or just takes
    # the value when calldata is zero.
    victim_code = (
        Conditional(
            condition=Op.CALLDATALOAD(0),
            if_true=Op.SELFDESTRUCT(Op.CALLDATALOAD(0)),
        )
        + Op.STOP
    )
    initcode = Initcode(deploy_code=victim_code)

    if create_opcode == Op.CREATE:
        create = Op.CREATE(value=initial_balance, offset=0, size=len(initcode))
    elif create_opcode == Op.CREATE2:
        create = Op.CREATE2(
            value=initial_balance, offset=0, size=len(initcode), salt=0
        )
    else:
        raise ValueError(f"unhandled create opcode {create_opcode}")

    entry_code = Om.MSTORE(initcode, 0) + Op.SSTORE(0, create)
    for slot, step in enumerate(steps, 1):
        if step == SD_SELF:
            calldata: Address | Bytecode | int = Op.SLOAD(0)
            value = 0
        elif step == SD_OTHER:
            calldata = other
            value = 0
        elif step == SEND:
            calldata = 0
            value = SEND_AMOUNT
        else:
            raise ValueError(f"unhandled step {step}")
        entry_code += Op.MSTORE(0, calldata) + Op.SSTORE(
            slot,
            Op.CALL(
                gas=Op.GAS,
                address=Op.SLOAD(0),
                value=value,
                args_offset=0,
                args_size=32,
            ),
        )
    entry = pre.deploy_contract(code=entry_code + Op.STOP)
    victim = compute_create_address(
        address=entry,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx_value = initial_balance + SEND_AMOUNT * steps.count(SEND)
    tx = Transaction(sender=sender, to=entry, value=tx_value)

    victim_balance = initial_balance
    other_balance = OTHER_BALANCE
    logs: list[TransactionLog] = []
    if tx_value > 0:
        logs.append(transfer_log(sender, entry, tx_value))
    if initial_balance > 0:
        logs.append(transfer_log(entry, victim, initial_balance))
    for step in steps:
        if step == SD_SELF:
            # Before EIP-8246 the opcode burns a same-tx contract's balance.
            if not fork.is_eip_enabled(8246):
                victim_balance = 0
        elif step == SD_OTHER:
            if victim_balance > 0:
                logs.append(transfer_log(victim, other, victim_balance))
            other_balance += victim_balance
            victim_balance = 0
        elif step == SEND:
            logs.append(transfer_log(entry, victim, SEND_AMOUNT))
            victim_balance += SEND_AMOUNT
        else:
            raise ValueError(f"unhandled step {step}")
    if fork.is_eip_enabled(7708):
        tx.expected_receipt = TransactionReceipt(logs=logs)

    expected_bal = None
    if fork.is_eip_enabled(7928):
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                victim: finalized_bal(fork, victim_balance, [])
            }
        )

    entry_storage: dict[int, Address | int] = {0: victim}
    for slot in range(1, len(steps) + 1):
        entry_storage[slot] = 1
    state_test(
        pre=pre,
        post={
            entry: Account(balance=0, storage=entry_storage),
            victim: finalized(fork, victim_balance),
            other: Account(balance=other_balance),
        },
        tx=tx,
        expected_block_access_list=expected_bal,
    )


@pytest.mark.parametrize(
    "beneficiary",
    [pytest.param("self", id="self"), pytest.param("other", id="other")],
)
@pytest.mark.parametrize(
    "initial_balance",
    [pytest.param(0, id="zero_balance"), pytest.param(3, id="funded")],
)
@pytest.mark.parametrize(
    "bump_nonce,write_storage",
    [
        pytest.param(True, False, id="nonce"),
        pytest.param(False, True, id="storage"),
        pytest.param(True, True, id="nonce_and_storage"),
    ],
)
def test_selfdestruct_clears_nonce_and_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    beneficiary: str,
    initial_balance: int,
    bump_nonce: bool,
    write_storage: bool,
) -> None:
    """
    Cases 13-16 of the EIP-8246 test list: a contract created in this
    transaction raises its nonce or writes storage before self-destructing.
    It is deleted, or under EIP-8246 has its nonce reset to zero and its
    storage cleared while it keeps its balance.
    """
    sender = pre.fund_eoa()
    other = pre.fund_eoa(amount=OTHER_BALANCE)

    victim_code = Bytecode()
    if bump_nonce:
        victim_code += Op.POP(Op.CREATE(0, 0, 0)) * 2
    if write_storage:
        victim_code += Op.SSTORE(0, 1) + Op.SSTORE(1, 2)
    if beneficiary == "self":
        victim_code += Op.SELFDESTRUCT(Op.ADDRESS)
    elif beneficiary == "other":
        victim_code += Op.SELFDESTRUCT(other)
    else:
        raise ValueError(f"unhandled beneficiary {beneficiary}")
    initcode = Initcode(deploy_code=victim_code)

    entry = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            0, Op.CREATE(value=initial_balance, offset=0, size=len(initcode))
        )
        + Op.SSTORE(1, Op.CALL(gas=Op.GAS, address=Op.SLOAD(0)))
        + Op.STOP
    )
    victim = compute_create_address(address=entry, nonce=1)

    tx = Transaction(sender=sender, to=entry, value=initial_balance)

    if beneficiary == "self":
        victim_balance = initial_balance
        other_balance = OTHER_BALANCE
    elif beneficiary == "other":
        victim_balance = 0
        other_balance = OTHER_BALANCE + initial_balance
    else:
        raise ValueError(f"unhandled beneficiary {beneficiary}")

    logs: list[TransactionLog] = []
    if initial_balance > 0:
        logs.append(transfer_log(sender, entry, initial_balance))
        logs.append(transfer_log(entry, victim, initial_balance))
        if beneficiary == "other":
            logs.append(transfer_log(victim, other, initial_balance))
    if fork.is_eip_enabled(7708):
        tx.expected_receipt = TransactionReceipt(logs=logs)

    expected_bal = None
    if fork.is_eip_enabled(7928):
        storage_reads = [0, 1] if write_storage else []
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                victim: finalized_bal(fork, victim_balance, storage_reads)
            }
        )

    post: dict[Address, Account | None] = {
        entry: Account(storage={0: victim, 1: 1}),
        victim: finalized(fork, victim_balance),
        other: Account(balance=other_balance),
    }
    if bump_nonce:
        for child_nonce in (1, 2):
            child = compute_create_address(address=victim, nonce=child_nonce)
            post[child] = Account(nonce=1, code=b"", balance=0)

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=expected_bal,
    )


@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@pytest.mark.parametrize(
    "beneficiary",
    [pytest.param("self", id="self"), pytest.param("other", id="other")],
)
@pytest.mark.parametrize(
    "initial_balance",
    [pytest.param(0, id="zero_balance"), pytest.param(3, id="funded")],
)
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall(eip=[8246])
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall.Balance(eip=[8246])
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall.Code(eip=[8246])
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall.Storage(eip=[8246])
@EIPChecklist.Opcode.Test.ExecutionContext.Callcode(eip=[8246])
def test_selfdestruct_in_delegate_context(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    beneficiary: str,
    initial_balance: int,
) -> None:
    """
    The account destroyed is the one whose context runs SELFDESTRUCT, not
    the library holding the code.
    """
    sender = pre.fund_eoa()
    other = pre.fund_eoa(amount=OTHER_BALANCE)

    if beneficiary == "self":
        target: Address | Bytecode = Op.ADDRESS
    elif beneficiary == "other":
        target = other
    else:
        raise ValueError(f"unhandled beneficiary {beneficiary}")
    library_code = Op.SSTORE(0, 1) + Op.SELFDESTRUCT(target)
    library = pre.deploy_contract(code=library_code, balance=7)

    victim_code = Op.POP(call_opcode(gas=Op.GAS, address=library)) + Op.STOP
    initcode = Initcode(deploy_code=victim_code)
    entry = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            0, Op.CREATE(value=initial_balance, offset=0, size=len(initcode))
        )
        + Op.SSTORE(1, Op.CALL(gas=Op.GAS, address=Op.SLOAD(0)))
        + Op.STOP
    )
    victim = compute_create_address(address=entry, nonce=1)

    tx = Transaction(sender=sender, to=entry, value=initial_balance)

    if beneficiary == "self":
        victim_balance = initial_balance
        other_balance = OTHER_BALANCE
    elif beneficiary == "other":
        victim_balance = 0
        other_balance = OTHER_BALANCE + initial_balance
    else:
        raise ValueError(f"unhandled beneficiary {beneficiary}")

    logs: list[TransactionLog] = []
    if initial_balance > 0:
        logs.append(transfer_log(sender, entry, initial_balance))
        logs.append(transfer_log(entry, victim, initial_balance))
        if beneficiary == "other":
            logs.append(transfer_log(victim, other, initial_balance))
    if fork.is_eip_enabled(7708):
        tx.expected_receipt = TransactionReceipt(logs=logs)

    expected_bal = None
    if fork.is_eip_enabled(7928):
        # The library's SSTORE runs in the victim's context, so the BAL
        # attributes the (then cleared) slot to the victim, not the library.
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                victim: finalized_bal(fork, victim_balance, [0]),
                library: BalAccountExpectation.empty(),
            }
        )

    state_test(
        pre=pre,
        post={
            entry: Account(storage={0: victim, 1: 1}),
            victim: finalized(fork, victim_balance),
            library: Account(balance=7, code=library_code, storage={}),
            other: Account(balance=other_balance),
        },
        tx=tx,
        expected_block_access_list=expected_bal,
    )


@pytest.mark.parametrize(
    "via_relay",
    [pytest.param(False, id="direct"), pytest.param(True, id="via_relay")],
)
@pytest.mark.parametrize(
    "initial_balance",
    [pytest.param(0, id="zero_balance"), pytest.param(3, id="funded")],
)
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall(eip=[8246])
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.BanCheck(eip=[8246])
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.BanNoModification(
    eip=[8246]
)
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall.SubCalls(eip=[8246])
@EIPChecklist.Opcode.Test.ExceptionalAbort(eip=[8246])
def test_selfdestruct_static_context_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    via_relay: bool,
    initial_balance: int,
) -> None:
    """
    SELFDESTRUCT to self inside a static call aborts the frame, so the
    contract is never registered for deletion and keeps its code.
    """
    sender = pre.fund_eoa()
    victim_code = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode = Initcode(deploy_code=victim_code)

    if via_relay:
        # The relay cannot SSTORE inside the static context, so it returns
        # the inner call result instead. Without that witness a broken
        # relay call would leave the same post-state as a correct abort.
        relay = pre.deploy_contract(
            code=Op.MSTORE(0, Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(0)))
            + Op.RETURN(0, 32)
        )
        static_target: Address | Bytecode = relay
        static_result = 1
    else:
        static_target = Op.SLOAD(0)
        static_result = 0

    entry = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            0, Op.CREATE(value=initial_balance, offset=0, size=len(initcode))
        )
        + Op.MSTORE(0, Op.SLOAD(0))
        + Op.SSTORE(
            1,
            Op.STATICCALL(
                gas=Op.GAS,
                address=static_target,
                args_offset=0,
                args_size=32,
                ret_offset=64,
                ret_size=32,
            ),
        )
        # Store the inner result offset by one so that a failing inner call
        # is still a written slot.
        + Op.SSTORE(2, Op.ADD(Op.MLOAD(64), 1))
        + Op.STOP
    )
    victim = compute_create_address(address=entry, nonce=1)

    tx = Transaction(sender=sender, to=entry, value=initial_balance)

    logs: list[TransactionLog] = []
    if initial_balance > 0:
        logs.append(transfer_log(sender, entry, initial_balance))
        logs.append(transfer_log(entry, victim, initial_balance))
    if fork.is_eip_enabled(7708):
        tx.expected_receipt = TransactionReceipt(logs=logs)

    expected_bal = None
    if fork.is_eip_enabled(7928):
        balance_changes = []
        if initial_balance > 0:
            balance_changes = [
                BalBalanceChange(
                    block_access_index=1, post_balance=initial_balance
                )
            ]
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                victim: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=bytes(victim_code)
                        )
                    ],
                    balance_changes=balance_changes,
                    storage_changes=[],
                    storage_reads=[],
                )
            }
        )

    state_test(
        pre=pre,
        post={
            entry: Account(storage={0: victim, 1: static_result, 2: 1}),
            victim: Account(
                balance=initial_balance, nonce=1, code=victim_code
            ),
        },
        tx=tx,
        expected_block_access_list=expected_bal,
    )
