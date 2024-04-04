"""
Suicide scenario requested test
https://github.com/ethereum/tests/issues/1325
"""

import pytest

from ethereum_test_forks import Cancun, Fork
from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    TestAddress2,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "2f8299df31bb8173618901a03a8366a3183479b0"


@pytest.fixture
def env():  # noqa: D103
    return Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x020000,
        gas_limit=71794957647893862,
        number=1,
        timestamp=1000,
    )


@pytest.mark.valid_from("Paris")
@pytest.mark.parametrize("first_suicide", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL])
@pytest.mark.parametrize("second_suicide", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL])
def test_reentrancy_selfdestruct_revert(
    env: Environment,
    fork: Fork,
    first_suicide: Op,
    second_suicide: Op,
    state_test: StateTestFiller,
):
    """
    Suicide reentrancy scenario:

    Call|Callcode|Delegatecall the contract S.
    S self destructs.
    Call the revert proxy contract R.
    R Calls|Callcode|Delegatecall S.
    S self destructs (for the second time).
    R reverts (including the effects of the second selfdestruct).
    It is expected the S is self destructed after the transaction.
    """
    address_to = TestAddress2
    address_s = Address(0x1000000000000000000000000000000000000001)
    address_r = Address(0x1000000000000000000000000000000000000002)
    suicide_d = Address(0x03E8)

    def construct_call_s(call_type: Op, money: int):
        if call_type in [Op.CALLCODE, Op.CALL]:
            return call_type(Op.GAS, address_s, money, 0, 0, 0, 0)
        else:
            return call_type(Op.GAS, address_s, money, 0, 0, 0)

    pre = {
        address_to: Account(
            balance=1000000000000000000,
            nonce=0,
            code=Op.SSTORE(1, construct_call_s(first_suicide, 0))
            + Op.SSTORE(2, Op.CALL(Op.GAS, address_r, 0, 0, 0, 0, 0))
            + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE())
            + Op.SSTORE(3, Op.MLOAD(0)),
            storage={0x01: 0x0100, 0x02: 0x0100, 0x03: 0x0100},
        ),
        address_s: Account(
            balance=3000000000000000000,
            nonce=0,
            code=Op.SELFDESTRUCT(1000),
            storage={},
        ),
        address_r: Account(
            balance=5000000000000000000,
            nonce=0,
            # Send money when calling it suicide second time to make sure the funds not transferred
            code=Op.MSTORE(0, Op.ADD(15, construct_call_s(second_suicide, 100)))
            + Op.REVERT(0, 32),
            storage={},
        ),
        TestAddress: Account(
            balance=7000000000000000000,
            nonce=0,
            code="0x",
            storage={},
        ),
    }

    post = {
        # Second caller unchanged as call gets reverted
        address_r: Account(balance=5000000000000000000, storage={}),
    }

    if first_suicide in [Op.CALLCODE, Op.DELEGATECALL]:
        if fork >= Cancun:
            # On Cancun even callcode/delegatecall does not remove the account, so the value remain
            post[address_to] = Account(
                storage={
                    0x01: 0x01,  # First call to contract S->suicide success
                    0x02: 0x00,  # Second call to contract S->suicide reverted
                    0x03: 16,  # Reverted value to check that revert really worked
                },
            )
        else:
            # Callcode executed first suicide from sender. sender is deleted
            post[address_to] = Account.NONEXISTENT  # type: ignore

        # Original suicide account remains in state
        post[address_s] = Account(balance=3000000000000000000, storage={})
        # Suicide destination
        post[suicide_d] = Account(
            balance=1000000000000000000,
        )

    # On Cancun suicide no longer destroys the account from state, just cleans the balance
    if first_suicide in [Op.CALL]:
        post[address_to] = Account(
            storage={
                0x01: 0x01,  # First call to contract S->suicide success
                0x02: 0x00,  # Second call to contract S->suicide reverted
                0x03: 16,  # Reverted value to check that revert really worked
            },
        )
        if fork >= Cancun:
            # On Cancun suicide does not remove the account, just sends the balance
            post[address_s] = Account(balance=0, code="0x6103e8ff", storage={})
        else:
            post[address_s] = Account.NONEXISTENT  # type: ignore

        # Suicide destination
        post[suicide_d] = Account(
            balance=3000000000000000000,
        )

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to=address_to,
        gas_price=10,
        protected=False,
        data="",
        gas_limit=500000,
        value=0,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
