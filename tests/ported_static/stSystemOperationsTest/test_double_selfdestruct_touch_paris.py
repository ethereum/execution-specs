"""
Verify a contract executing SELFDESTRUCT twice in one transaction: the
second has little effect but touches a new beneficiary address.

Ported from:
state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml

@manually-enhanced: Do not overwrite. The post is a closed form of the
transaction value rather than three pinned result sets, and the caller
records both call results, which is what proves the second SELFDESTRUCT
ran. Extended with a `created_in_tx` arm covering EIP-6780's other
branch, where the account really is deleted.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("tx_value", [0, 1, 2])
@pytest.mark.parametrize(
    "created_in_tx",
    [
        pytest.param(False, id="pre_existing"),
        pytest.param(True, id="created_in_tx"),
    ],
)
def test_double_selfdestruct_touch_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
    created_in_tx: bool,
) -> None:
    """Two SELFDESTRUCTs in one transaction touch two beneficiaries."""
    sender = pre.fund_eoa()

    # Both beneficiaries start non-empty, so a zero-value SELFDESTRUCT
    # leaves one exactly as it was.
    beneficiary_balance = 10
    beneficiary_1 = pre.fund_eoa(amount=beneficiary_balance)
    beneficiary_2 = pre.fund_eoa(amount=beneficiary_balance)

    # Source: yul
    # {
    #   let index := add(sload(0), 1)
    #   sstore(0, index)
    #   selfdestruct(sload(index))
    # }
    # Each call bumps the index, so the first SELFDESTRUCT picks the
    # beneficiary in slot 1 and the second the one in slot 2.
    selfdestructor_code = (
        Op.ADD(Op.SLOAD(key=0x0), 0x1)
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.SELFDESTRUCT(address=Op.SLOAD)
    )

    address_slot = 0x100  # memory word holding the callee's address
    first_result_slot = 1
    second_result_slot = 2
    callee_slot = 3

    tx_data: Bytes | Initcode
    if created_in_tx:
        # Deploy it from the transaction's calldata, so EIP-6780 sees a
        # contract created and destroyed within one transaction.
        tx_data = Initcode(
            deploy_code=selfdestructor_code,
            initcode_prefix=Op.SSTORE(key=0x1, value=beneficiary_1)
            + Op.SSTORE(key=0x2, value=beneficiary_2),
        )
        setup = Op.CALLDATACOPY(
            dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE
        ) + Op.MSTORE(
            address_slot,
            Op.CREATE(value=0x0, offset=0x0, size=Op.CALLDATASIZE),
        )
    else:
        selfdestructor = pre.deploy_contract(
            code=selfdestructor_code,
            storage={0: 0, 1: beneficiary_1, 2: beneficiary_2},
        )
        tx_data = Bytes(b"")
        setup = Op.MSTORE(address_slot, selfdestructor)

    # Split the received value in half and send each half in its own
    # call, recording both results so neither call can go missing.
    first_value = Op.SHR(0x1, Op.CALLVALUE)
    second_value = Op.SUB(Op.CALLVALUE, Op.SHR(0x1, Op.CALLVALUE))
    caller = pre.deploy_contract(
        code=setup
        + Op.SSTORE(key=callee_slot, value=Op.MLOAD(address_slot))
        + Op.SSTORE(
            key=first_result_slot,
            value=Op.CALL(address=Op.MLOAD(address_slot), value=first_value),
        )
        + Op.SSTORE(
            key=second_result_slot,
            value=Op.CALL(address=Op.MLOAD(address_slot), value=second_value),
        )
        + Op.STOP,
    )

    tx = Transaction(sender=sender, to=caller, value=tx_value, data=tx_data)

    # Each SELFDESTRUCT forwards its frame's whole balance onward, so
    # every beneficiary gains exactly the half routed to it.
    first_transfer = tx_value >> 1
    second_transfer = tx_value - first_transfer
    post: dict[Address, Account | None] = {
        sender: Account(nonce=1),
        beneficiary_1: Account(balance=beneficiary_balance + first_transfer),
        beneficiary_2: Account(balance=beneficiary_balance + second_transfer),
    }
    if created_in_tx:
        # EIP-6780 deletes an account created in this same transaction.
        callee = compute_create_address(address=caller, nonce=1)
        post[callee] = Account.NONEXISTENT
    else:
        # EIP-6780 spares a pre-existing account, so the index reaching
        # 2 survives to show both SELFDESTRUCTs executed.
        callee = selfdestructor
        post[selfdestructor] = Account(
            storage={0: 2, 1: beneficiary_1, 2: beneficiary_2},
            balance=0,
        )

    # Recording the callee address proves the CREATE arm really got a
    # contract, rather than a zero address that calls succeed against.
    post[caller] = Account(
        storage={
            first_result_slot: 1,
            second_result_slot: 1,
            callee_slot: callee,
        },
        balance=0,
    )

    state_test(pre=pre, post=post, tx=tx)
