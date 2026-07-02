"""
Test_refund50_1.

Ported from:
state_tests/stRefundTest/refund50_1Filler.json

@manually-enhanced: Do not overwrite. The post-state asserts the sender
balance, which equals its start minus `gas_used * gas_price`. The
contract clears five cold storage slots; EIP-8038 raises each cold
SSTORE-clear charge from 5000 to 13000. The EIP-3529 refund cap
(`gas_used // 5`) binds at both forks (the clear refunds far exceed a
fifth of gas used), so the extra charge raises `gas_used` by exactly
four fifths of itself. Derive the per-clear charge delta from the fork
gas model (0 pre-EIP-8037) and subtract `gas_price * 5 * delta * 4 // 5`
from the Cancun balance; do not hardcode the Amsterdam value.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund50_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund50_1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_refund50_1."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0x989680)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    # EIP-8038 raises each cold SSTORE-clear charge and EIP-2780
    # shifts the tx intrinsic. With the EIP-3529 refund cap binding,
    # gas_used rises by 4/5 of the gross-gas delta.
    cold_clear_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=1, current_value=1, new_value=0
        ).gas_cost(fork)
        - 5000
    )
    intrinsic_delta = fork.transaction_intrinsic_cost_calculator()() - 21_000
    gross_delta = 5 * cold_clear_delta + intrinsic_delta
    extra_gas_used = gross_delta * 4 // 5

    post = {
        target: Account(storage={}),
        coinbase: Account(balance=0),
        sender: Account(balance=0x92F810 - 10 * extra_gas_used, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
