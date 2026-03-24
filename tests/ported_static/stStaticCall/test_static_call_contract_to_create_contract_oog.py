"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_CallContractToCreateContractOOGFiller.json
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
        "tests/static/state_tests/stStaticCall/static_CallContractToCreateContractOOGFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value, expected_post",
    [
        (0, {}),
        (
            1,
            {
                Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"): Account(
                    storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6}
                ),
                Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account(
                    storage={0: 12}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_contract_to_create_contract_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
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
        gas_limit=100000000,
    )

    # Source: LLL
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3) [[0]](CREATE 1 11 21) (STATICCALL 0 (SLOAD 0) 0 0 0 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x600C60005566602060406000F060205260076039F3,
            )
            + Op.SSTORE(
                key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15)
            )
            + Op.STATICCALL(
                gas=0x0,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540BE400)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
