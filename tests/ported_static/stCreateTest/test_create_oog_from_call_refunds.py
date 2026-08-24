"""
Verify that gas refunds earned inside a CREATE frame are discarded when the
deployment fails.

Ported from:
state_tests/stCreateTest/CreateOOGFromCallRefundsFiller.yml

@manually-enhanced: Do not overwrite. Restored SSTORE pairs solc had
optimized away, and parametrized on refund source x deployment outcome.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateOOGFromCallRefundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "deploy_outcome",
    [
        pytest.param(
            "created",
            marks=pytest.mark.valid_before("EIP8368"),
        ),
        "code_deposit_oog",
        "invalid_opcode",
    ],
)
@pytest.mark.parametrize(
    "refund_source",
    [
        "sstore",
        "call",
        "delegatecall",
        "callcode",
        "selfdestruct",
        "log",
        "create",
        "create2",
    ],
)
def test_create_oog_from_call_refunds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_source: str,
    deploy_outcome: str,
) -> None:
    """
    Verify that a gas refund earned inside a CREATE frame only survives if
    the deployment does.

    `refund_source` picks how the init code earns the refund; `deploy_outcome`
    picks whether that frame commits (`created`) or is discarded, by failing
    the code deposit (`code_deposit_oog`) or hitting `INVALID`
    (`invalid_opcode`). Both failures burn the whole gas allowance, so the
    receipt must charge the full limit -- a refund that wrongly survived
    would show up as a discount.
    """
    # More code than the budget can afford to deposit.
    oversized_code_size = 5000
    tx_gas_limit = 800_000
    # High enough for the successful cases (EIP-8037 charges heavy state gas
    # per zero -> non-zero SSTORE and per created account), low enough that
    # the oversized deposit still cannot be paid for.
    assert (
        tx_gas_limit
        < oversized_code_size * fork.gas_costs().CODE_DEPOSIT_PER_BYTE
    ), "budget covers the oversized code deposit; OOG cases would succeed"

    sender = pre.fund_eoa()

    # Deploys the calldata as init code, burning all remaining gas on a
    # trailing INVALID if that fails, which pins the gas charged on failure
    # to the whole limit and makes any surviving refund observable.
    factory_contract = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
            + Op.JUMPI(
                19,
                Op.EQ(0, Op.CREATE(value=0, offset=0, size=Op.CALLDATASIZE)),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.INVALID
        )
    )
    created_contract = compute_create_address(
        address=factory_contract, nonce=1
    )

    # Every init code returns this one byte, read from untouched memory.
    deployed_code = Op.STOP
    deploy_succeeds = deploy_outcome == "created"

    # Clears an already-set slot to earn a refund; which account's slot it
    # hits depends on the call opcode used below.
    storage_clearing_code = Op.SSTORE(key=0x1, value=0x0) + Op.STOP

    # Where the returned zero byte comes from; only nested creates use memory.
    return_offset = 0
    # Post-state entries specific to the refund source.
    extra_post: dict = {}
    refund_code: Bytecode

    if refund_source == "sstore":
        # Both slot 1 writes matter: alone, the clear is a no-op on a fresh
        # account and earns nothing. solc folded the pair away when ported.
        refund_code = (
            Op.SSTORE(key=0, value=1)
            + Op.SSTORE(key=1, value=1)
            + Op.SSTORE(key=1, value=0)
        )
    elif refund_source == "call":
        # Refund earned one frame below, in the callee's own storage.
        storage_clearing_contract = pre.deploy_contract(
            code=storage_clearing_code, storage={1: 1}
        )
        refund_code = Op.SSTORE(key=0, value=1) + Op.POP(
            Op.CALL(address=storage_clearing_contract)
        )
    elif refund_source in ("delegatecall", "callcode"):
        # Both run the callee against this frame's storage, so slot 1 must be
        # set here for the callee's clear to earn anything.
        storage_clearing_contract = pre.deploy_contract(
            code=storage_clearing_code, storage={1: 1}
        )
        subcall = (
            Op.DELEGATECALL if refund_source == "delegatecall" else Op.CALLCODE
        )
        refund_code = (
            Op.SSTORE(key=0, value=1)
            + Op.SSTORE(key=1, value=1)
            + Op.POP(subcall(address=storage_clearing_contract))
        )
    elif refund_source == "selfdestruct":
        self_destructing_code = Op.SELFDESTRUCT(address=Op.ORIGIN)
        self_destructing_contract = pre.deploy_contract(
            code=self_destructing_code, storage={1: 1}
        )
        refund_code = Op.SSTORE(key=0, value=1) + Op.POP(
            Op.CALL(address=self_destructing_contract)
        )
        extra_post[self_destructing_contract] = (
            Account(balance=0, nonce=1)
            if deploy_succeeds
            else Account(storage={1: 1}, code=self_destructing_code, nonce=1)
        )
    elif refund_source == "log":
        # Control case: logs only, no refund earned.
        logging_contract = pre.deploy_contract(
            code=Op.MSTORE(offset=0x0, value=0xFF)
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
            + Op.STOP,
            storage={1: 1},
        )
        refund_code = Op.SSTORE(key=0, value=1) + Op.POP(
            Op.CALL(address=logging_contract)
        )
    else:
        # Grandchild earns a refund of its own, so a failure has to discard
        # two nested frames' worth at once.
        child_init_code = (
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=0x0, value=0x0)
            + Op.RETURN(offset=0x0, size=0x1)
        )
        create_op = Op.CREATE if refund_source == "create" else Op.CREATE2
        refund_code = (
            Op.SSTORE(key=0, value=1)
            + Op.SSTORE(key=1, value=1)
            + Op.SSTORE(key=1, value=0)
            + Op.MSTORE(
                offset=0, value=Hash(child_init_code, right_padding=True)
            )
            + Op.POP(create_op(value=0, offset=0, size=len(child_init_code)))
        )
        # Init code fills the first memory word; read past its end.
        return_offset = len(child_init_code)
        child_contract = compute_create_address(
            address=created_contract,
            nonce=1,
            salt=0,
            initcode=child_init_code,
            opcode=create_op,
        )
        extra_post[child_contract] = (
            Account(storage={}, code=deployed_code, nonce=1)
            if deploy_succeeds
            else Account.NONEXISTENT
        )

    deploy_code: Bytecode
    if deploy_outcome == "created":
        deploy_code = Op.RETURN(offset=return_offset, size=len(deployed_code))
    elif deploy_outcome == "code_deposit_oog":
        # More code than the deposit charge can be paid for.
        deploy_code = Op.RETURN(offset=return_offset, size=oversized_code_size)
    else:
        deploy_code = Op.INVALID

    post = {
        sender: Account(nonce=1),
        created_contract: (
            Account(
                storage={0: 1},
                code=deployed_code,
                # The nested creates bump this nonce again.
                nonce=2 if refund_source in ("create", "create2") else 1,
            )
            if deploy_succeeds
            else Account.NONEXISTENT
        ),
        **extra_post,
    }

    tx = Transaction(
        sender=sender,
        to=factory_contract,
        data=refund_code + deploy_code,
        gas_limit=tx_gas_limit,
        # The factory's INVALID burns the frame, so the entire limit must be
        # charged: any refund that survived the failure would show up as a
        # discount here. Only `cumulative_gas_used` is actually verified, and
        # it equals this transaction's gas used since it is alone in its block.
        expected_receipt=(
            None
            if deploy_succeeds
            else TransactionReceipt(cumulative_gas_used=tx_gas_limit)
        ),
    )

    state_test(pre=pre, post=post, tx=tx)
