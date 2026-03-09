"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json
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
        "tests/static/state_tests/stCallCreateCallCodeTest/contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (
            96000,
            {
                Address("0x1000000000000000000000000000000000000001"): Account(
                    storage={1: 1}
                )
            },
        ),
        (60000, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
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
        gas_limit=10000000,
    )

    # Source: LLL
    # {(SSTORE 1 1)}
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10C8E0)
    # Source: LLL
    # {(CALL 50000 0x1000000000000000000000000000000000000001 0 0 64 0 64)}
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xC350,
                address=0x1000000000000000000000000000000000000001,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "6040600060406000600073100000000000000000000000000000000000000161c350f1"  # noqa: E501
        ),
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
