"""
Measure a value CALL to the coinbase with and without an access list.

Ported from:
state_tests/stEIP2930/coinbaseT01Filler.yml
state_tests/stEIP2930/coinbaseT2Filler.yml

@manually-enhanced: Do not overwrite. The target contract measures, via
`Op.GAS`, the regular gas of a `CALL` that transfers value to the warm,
already-existing coinbase. EIP-8038 raises the value-transfer
component `CALL_VALUE`, so the measurement grows by the `CALL_VALUE`
delta versus Cancun. That delta is derived from the fork's own gas
model, so it is exactly 0 before EIP-8038 and tracks future parameter
changes; do not hardcode the Amsterdam number.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_VALUE = 1_000_000
WARM_VALUE_CALL_GAS = 6800
MEASUREMENT_OVERHEAD = 0x21


@pytest.mark.ported_from(
    [
        "state_tests/stEIP2930/coinbaseT01Filler.yml",
        "state_tests/stEIP2930/coinbaseT2Filler.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_type, access_list",
    [
        pytest.param(0, None, id="T0"),
        pytest.param(1, "coinbase", id="T1baseInList"),
        pytest.param(1, "other", id="T1baseNotInList"),
        pytest.param(2, "coinbase", id="T2baseInList"),
        pytest.param(2, "other", id="T2baseNotInList"),
    ],
)
def test_coinbase_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    access_list: str | None,
) -> None:
    """Check the coinbase is warm whether or not the access list has it."""
    sender = pre.fund_eoa()
    coinbase = pre.fund_eoa(amount=1)
    target = pre.deploy_contract(
        code=Op.MSTORE(0, Op.GAS)
        + Op.POP(Op.CALL(address=coinbase, value=CALL_VALUE))
        + Op.MSTORE(0x20, Op.GAS)
        + Op.SSTORE(
            0,
            Op.SUB(Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)), MEASUREMENT_OVERHEAD),
        ),
        balance=CALL_VALUE,
    )

    access_lists = {
        None: None,
        "coinbase": [AccessList(address=coinbase, storage_keys=[])],
        "other": [
            AccessList(address=pre.nonexistent_account(), storage_keys=[])
        ],
    }
    call_value_delta = (
        fork.gas_costs().CALL_VALUE - Cancun.gas_costs().CALL_VALUE
    )
    post = {
        target: Account(storage={0: WARM_VALUE_CALL_GAS + call_value_delta})
    }

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=target,
        access_list=access_lists[access_list],
    )
    state_test(
        env=Environment(fee_recipient=coinbase), pre=pre, post=post, tx=tx
    )
