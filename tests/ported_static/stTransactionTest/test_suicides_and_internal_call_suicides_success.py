"""
Verify SELFDESTRUCT inside an internal call: the callee self-destructs to
a previously nonexistent beneficiary, which materializes only when the
forwarded gas covers the new-account charge.

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesSuccessFiller.json

@manually-enhanced: Do not overwrite. The two forwarded-gas calldata words
derive from the fork's SELFDESTRUCT new-account cost (state-priced
under EIP-8037), and the two arms sit one gas either side of it, so the
boundary is exact on every fork rather than approximate. The floor is
Berlin: the cold-access metadata the budget derives from has no meaning
before EIP-2929.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_VALUE = 1
SD_VALUE = 999


@pytest.mark.ported_from(
    [
        "state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesSuccessFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "sufficient_selfdestruct_gas",
    [
        pytest.param(False, id="insufficient_selfdestruct_gas"),
        pytest.param(True, id="sufficient_selfdestruct_gas"),
    ],
)
def test_suicides_and_internal_call_suicides_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficient_selfdestruct_gas: bool,
) -> None:
    """A funded SELFDESTRUCT materializes its beneficiary."""
    self_destructing_contract_recipient = pre.nonexistent_account()
    # Source: lll
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    self_destruct_code = Op.SELFDESTRUCT(
        address=self_destructing_contract_recipient,
        # The beneficiary has never been touched, so the access is cold,
        # and it does not exist, so it has to be created.
        address_warm=False,
        account_new=True,
    )
    self_destructing_contract = pre.deploy_contract(code=self_destruct_code)

    # What the callee needs: the beneficiary push plus the SELFDESTRUCT,
    # including its EIP-8037 state charge. A value-bearing CALL hands it
    # a stipend on top of the ask, so the ask that exactly suffices is
    # that much smaller; the two arms sit one gas either side of it.
    required_gas = self_destruct_code.gas_cost(fork)
    exact_ask = required_gas - fork.gas_costs().CALL_STIPEND
    assert exact_ask > 0, "the stipend alone would fund the SELFDESTRUCT"
    call_gas = exact_ask if sufficient_selfdestruct_gas else exact_ask - 1

    # Source: lll
    # {(CALL (CALLDATALOAD 0) 0x0000000000000000000000000000000000000000 1 0 0 0 0) (SELFDESTRUCT 0)}  # noqa: E501
    caller_self_destructing_contract = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=call_gas,
                address=self_destructing_contract,
                value=CALL_VALUE,
            )
        )
        + Op.SELFDESTRUCT(address=self_destructing_contract)
        + Op.STOP,
        balance=CALL_VALUE + SD_VALUE,
    )

    # The beneficiary is created only when the forwarded gas covers the
    # new-account charge; otherwise the callee runs out and never pays.
    post: dict[Address, Account | None] = {
        self_destructing_contract_recipient: (
            Account(storage={}, balance=CALL_VALUE)
            if sufficient_selfdestruct_gas
            else Account.NONEXISTENT
        ),
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller_self_destructing_contract,
        # Charge state gas to the frames, so the callee's new-account
        # charge is paid out of `call_gas` and the boundary is real.
        state_gas_reservoir=0,
    )

    state_test(pre=pre, post=post, tx=tx)
