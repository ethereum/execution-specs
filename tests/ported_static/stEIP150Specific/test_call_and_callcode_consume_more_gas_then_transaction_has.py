"""
test_call_and_callcode_consume_more_gas_then_transaction_has

Ported from:
state_tests/stEIP150Specific/CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json
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
    ["state_tests/stEIP150Specific/CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_and_callcode_consume_more_gas_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_and_callcode_consume_more_gas_then_transaction_has"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0xfd59abae521384b5731ac657616680219fbc423d, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.CALLCODE(gas=0x927c0, address=0xfd59abae521384b5731ac657616680219fbc423d, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x9bdb308c9b567e1dbc906d9d592a8464a05ffd44"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x12) }
    addr_0x1000000000000000000000000000000000000103 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0xfd59abae521384b5731ac657616680219fbc423d"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 18, 8: 0x8d5b6, 9: 1, 10: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
