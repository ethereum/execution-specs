"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific
CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP150Specific/CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_and_callcode_consume_more_gas_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xA,
                value=Op.CALLCODE(
                    gas=0x927C0,
                    address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x9bdb308c9b567e1dbc906d9d592a8464a05ffd44"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0xfd59abae521384b5731ac657616680219fbc423d"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(storage={0: 18, 8: 0x8D5B6, 9: 1, 10: 1}),
        callee: Account(storage={0: 18}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
