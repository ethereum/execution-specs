"""
test_test_random_test

Ported from:
state_tests/stSystemOperationsTest/testRandomTestFiller.json
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
    ["state_tests/stSystemOperationsTest/testRandomTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_random_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_test_random_test"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw
    # 0x424443444243434383f0155af055
    contract_0 = pre.deploy_contract(
        code=Op.TIMESTAMP + Op.PREVRANDAO + Op.NUMBER + Op.PREVRANDAO
        + Op.SSTORE(key=Op.CREATE(value=Op.GAS, offset=Op.ISZERO(Op.CREATE(value=Op.DUP4, offset=Op.NUMBER, size=Op.NUMBER)), size=Op.NUMBER), value=Op.TIMESTAMP),  # noqa: E501
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=300000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={0xebcce5f60530275ee9318ce1eff9e4bfee810172: 1000},
                nonce=2,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
