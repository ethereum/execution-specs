"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest/testRandomTestFiller.json
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
        "tests/static/state_tests/stSystemOperationsTest/testRandomTestFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_random_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.TIMESTAMP
            + Op.PREVRANDAO
            + Op.NUMBER
            + Op.PREVRANDAO
            + Op.SSTORE(
                key=Op.CREATE(
                    value=Op.GAS,
                    offset=Op.ISZERO(
                        Op.CREATE(
                            value=Op.DUP4, offset=Op.NUMBER, size=Op.NUMBER
                        ),
                    ),
                    size=Op.NUMBER,
                ),
                value=Op.TIMESTAMP,
            )
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=300000,
        value=100000,
    )

    post = {
        contract: Account(
            storage={0xEBCCE5F60530275EE9318CE1EFF9E4BFEE810172: 1000},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
