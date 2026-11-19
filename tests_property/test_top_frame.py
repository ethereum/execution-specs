"""
Properties of the gas a transaction pays as its top frame is set up.

From [EIP-2780] the costs that depend on state leave the intrinsic cost
and are charged before the first instruction runs: the account a transfer
or a creation brings into being, and the access to the code a delegated
recipient points at. The framework prices both, and the spec must spend
exactly that much gas and run out with one less.

[EIP-2780]: https://eips.ethereum.org/EIPS/eip-2780
"""

from functools import partial
from typing import Any, Tuple

import pytest
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint
from execution_testing import RecipientType
from execution_testing.forks import Fork
from hypothesis import assume, given
from hypothesis import strategies as st

from ethereum.state import Address
from ethereum.state_mpt import State
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import add_account, zeroed
from .strategies import CONTRACT_CODE, DELEGATION_PREFIX, ints

pytestmark = requires(lambda fork: fork.is_eip_enabled(2780))

SENDER = Address(b"\x01" * 20)
RECIPIENT = Address(b"\x02" * 20)
DELEGATE = Address(b"\x03" * 20)
# What the recipient is before the transaction, as the framework names it.
# A creation's target is `EMPTY_ACCOUNT` when fresh and `EOA` when funded.
RECIPIENTS = {
    RecipientType.EMPTY_ACCOUNT: None,
    RecipientType.EOA: b"",
    RecipientType.CONTRACT: CONTRACT_CODE,
    RecipientType.DELEGATION_7702: DELEGATION_PREFIX + DELEGATE,
}


def top_frame(
    spec: Hardfork,
    recipient_type: RecipientType,
    *,
    creates: bool,
    value: int,
    delegate_warm: bool,
    gas_left: int,
    reservoir: int,
) -> Tuple[Any, Any]:
    """Set up a transaction's top frame, and return it with its meter."""
    vm = spec.module("vm")
    tracker = spec.module("state_tracker")
    gas = spec.module("vm.gas")

    block_state = tracker.BlockState(pre_state=State())
    add_account(block_state, SENDER, nonce=1, balance=value)
    code = RECIPIENTS[recipient_type]
    if code is not None:
        # EIP-7523: an account that exists is never empty.
        add_account(block_state, RECIPIENT, nonce=0, balance=1, code=code)
    tx_env = zeroed(
        vm.TransactionEnvironment,
        origin=SENDER,
        recipient=RECIPIENT,
        is_create=creates,
        value=U256(value),
        data=Bytes(b""),
        access_list_addresses={DELEGATE} if delegate_warm else set(),
        state=tracker.TransactionState(parent=block_state),
    )
    block_env = zeroed(vm.BlockEnvironment, state=block_state)
    meter = gas.GasMeter(
        gas_left=Uint(gas_left),
        state_gas_left=Uint(reservoir),
        state_gas_baseline=Uint(reservoir),
    )
    create_evm = spec.module("vm.interpreter").create_evm
    return create_evm(block_env, tx_env, meter), meter


@pytest.mark.parametrize("gas_side", ["exact", "one_short"])
@given(data=st.data())
def test_top_frame_charges_match_the_framework(
    fork: Fork, spec: Hardfork, gas_side: str, data: st.DataObject
) -> None:
    """
    Setting up the top frame spends exactly the execution and state gas
    the framework prices for the recipient the transaction finds, and
    runs out with one gas less.
    """
    creates = data.draw(st.booleans())
    recipient_type = data.draw(st.sampled_from(sorted(RECIPIENTS, key=str)))
    value = data.draw(st.sampled_from([0, 1]))
    delegate_warm = data.draw(st.booleans())
    # EIP-684: a creation needs a target without code.
    assume(not creates or not RECIPIENTS[recipient_type])

    execution_gas = fork.transaction_top_frame_execution_gas(
        contract_creation=creates,
        recipient_type=recipient_type,
        delegation_warm=delegate_warm,
    )
    state_gas = fork.transaction_top_frame_state_gas(
        # The framework prices a creation for a fresh target.
        contract_creation=creates
        and recipient_type == RecipientType.EMPTY_ACCOUNT,
        sends_value=value > 0,
        recipient_type=recipient_type,
    )
    if creates and recipient_type == RecipientType.EOA:
        # A target that already exists is not a new account.
        state_gas = 0
    reservoir = data.draw(ints(2 * state_gas))
    needed = execution_gas + max(0, state_gas - reservoir)
    assume(gas_side == "exact" or needed > 0)

    set_up = partial(
        top_frame,
        spec,
        recipient_type,
        creates=creates,
        value=value,
        delegate_warm=delegate_warm,
        reservoir=reservoir,
    )
    if gas_side == "one_short":
        with pytest.raises(spec.module("vm.exceptions").OutOfGasError):
            set_up(gas_left=needed - 1)
        return

    evm, meter = set_up(gas_left=needed)
    assert int(meter.gas_left) == 0
    assert int(meter.state_gas_left) == max(0, reservoir - state_gas)
    if recipient_type == RecipientType.DELEGATION_7702 and not creates:
        assert evm.code_address == DELEGATE
        assert DELEGATE in evm.accessed_addresses
    assert {SENDER, RECIPIENT} <= evm.accessed_addresses


@given(
    recipient_type=st.sampled_from(
        [RecipientType.CONTRACT, RecipientType.DELEGATION_7702]
    ),
    value=st.sampled_from([0, 1]),
    gas=ints(1 << 24),
)
def test_creation_onto_code_collides(
    spec: Hardfork, recipient_type: RecipientType, value: int, gas: int
) -> None:
    """A creation whose target holds code fails, whatever gas it has."""
    with pytest.raises(spec.module("vm.exceptions").AddressCollision):
        top_frame(
            spec,
            recipient_type,
            creates=True,
            value=value,
            delegate_warm=False,
            gas_left=gas,
            reservoir=gas,
        )
