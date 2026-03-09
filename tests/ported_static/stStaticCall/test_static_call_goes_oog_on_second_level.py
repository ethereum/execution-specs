"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_CallGoesOOGOnSecondLevelFiller.json
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
        "tests/static/state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_goes_oog_on_second_level(
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

    pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0x2FFFFF) + Op.STOP,
        nonce=0,
        address=Address("0x44969261d9660fcc1a2e03db83ba372ebf5f652d"),  # noqa: E501
    )
    # Source: LLL
    # { (SSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000110> 0 0 0 0)) [[ 10 ]] (GAS) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x9,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=0xA1202B00F0CB8ACDD112E4FC87899F33572541C6,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0xA, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x6a2a170a903e470c3dd8bfd7974c77020c5fd8f9"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x8, value=Op.GAS)
            + Op.MSTORE(
                offset=0x9,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=0x44969261D9660FCC1A2E03DB83BA372EBF5F652D,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa1202b00f0cb8acdd112e4fc87899f33572541c6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=220000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
