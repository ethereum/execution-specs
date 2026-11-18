"""
Verify calls into a contract that self-destructs to its caller, with a
sub-call grant that may or may not cover SELFDESTRUCT.

Ported from:
state_tests/stRefundTest/refund_CallToSuicideNoStorageFiller.json
state_tests/stRefundTest/refund_CallToSuicideStorageFiller.json
state_tests/stRefundTest/refund_CallToSuicideTwiceFiller.json

@manually-enhanced: Do not overwrite. Three fillers merged into one test.
The outcome is derived from the fork: the calls succeed when the grant
covers the callee's code, and the self-destructed contract is deleted
only before EIP-6780. Calling it a second time re-runs SELFDESTRUCT with
nothing left to send.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Hash,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 0xDE0B6B3A7640000


@pytest.mark.ported_from(
    [
        "state_tests/stRefundTest/refund_CallToSuicideNoStorageFiller.json",
        "state_tests/stRefundTest/refund_CallToSuicideStorageFiller.json",
        "state_tests/stRefundTest/refund_CallToSuicideTwiceFiller.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "call_gas",
    [
        pytest.param(0x1F4, id="call_gas_500"),
        pytest.param(0x10000, id="call_gas_65536"),
    ],
)
@pytest.mark.parametrize(
    "callee_has_storage, call_twice",
    [
        pytest.param(False, False, id="no_storage"),
        pytest.param(True, False, id="storage"),
        pytest.param(True, True, id="storage_twice"),
    ],
)
def test_refund_call_to_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    callee_has_storage: bool,
    call_twice: bool,
    call_gas: int,
) -> None:
    """Call a self-destructing contract once or twice in a transaction."""
    sender = pre.fund_eoa(amount=0x2540BE400)

    callee_storage: Storage.StorageDictType = (
        {1: 1} if callee_has_storage else {}
    )

    # The beneficiary is the caller, which is warm as the transaction's
    # destination.
    callee_code = Op.SELFDESTRUCT(address=Op.CALLER, address_warm=True)
    callee = pre.deploy_contract(
        code=callee_code + Op.STOP,
        storage=callee_storage,
        balance=CONTRACT_BALANCE,
    )

    # The sub-call grant is read from the calldata.
    call = Op.CALL(gas=Op.CALLDATALOAD(offset=0x0), address=callee)
    caller_code = Op.SSTORE(key=0x0, value=call)
    if call_twice:
        caller_code += call
    caller = pre.deploy_contract(
        code=caller_code + Op.STOP,
        storage={1: 1},
        balance=CONTRACT_BALANCE,
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        data=Hash(call_gas),
        gas_limit=10_000_000,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    callee_succeeds = callee_code.gas_cost(fork) <= call_gas
    callee_post: Account | None
    if not callee_succeeds:
        callee_post = Account(storage=callee_storage, balance=CONTRACT_BALANCE)
    elif fork.is_eip_enabled(6780):
        callee_post = Account(storage=callee_storage, balance=0, nonce=1)
    else:
        callee_post = Account.NONEXISTENT

    post = {
        caller: Account(
            storage={0: int(callee_succeeds), 1: 1},
            balance=CONTRACT_BALANCE
            + tx.value
            + (CONTRACT_BALANCE if callee_succeeds else 0),
        ),
        sender: Account(nonce=1),
        callee: callee_post,
    }

    state_test(pre=pre, post=post, tx=tx)
