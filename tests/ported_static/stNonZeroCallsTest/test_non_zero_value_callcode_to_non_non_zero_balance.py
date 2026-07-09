"""
Test_non_zero_value_callcode_to_non_non_zero_balance.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToNonNonZeroBalanceFiller.json

@manually-enhanced: Do not overwrite. The measured slot captures the
regular gas of a value-1 CALLCODE to a cold, alive EOA plus the SSTORE
storing the (success) result. EIP-8038 reprices the CALLCODE's cold
account access and value transfer, and reprices the cold
value-unchanged SSTORE. The delta is therefore
`(COLD_ACCOUNT_ACCESS - 2600) + (CALL_VALUE - 9000)` plus the cold
SSTORE reprice, each derived from the fork and exactly 0 before
EIP-8038.
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
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToNonNonZeroBalanceFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_callcode_to_non_non_zero_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_non_zero_value_callcode_to_non_non_zero_balance."""
    # EIP-8038 deltas, each 0 before EIP-8038. The CALLCODE pays the
    # cold account reprice and the value-transfer reprice; the cold
    # value-unchanged SSTORE gains its own reprice.
    gas_costs = fork.gas_costs()
    cold_account_delta = gas_costs.COLD_ACCOUNT_ACCESS - 2600
    call_value_delta = gas_costs.CALL_VALUE - 9000
    cold_noop_sstore_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=0, current_value=0, new_value=0
        ).gas_cost(fork)
        - 2200
    )
    call_measure_delta = (
        cold_account_delta + call_value_delta + cold_noop_sstore_delta
    )
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=100)  # noqa: F841
    # Source: lll
    # { [0](GAS) [[1]] (CALLCODE 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0xEA60,
                address=addr,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(balance=100),
        target: Account(storage={100: 11535 + call_measure_delta}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
