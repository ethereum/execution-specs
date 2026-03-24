"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json
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
        "tests/static/state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level(
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

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x493E0,
                    address=0xCCC0159BD2EF7118B5E7B8D958E72237F02493FE,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0xC, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x066f77b181e0e662e17d427c7320267adf2fd624"),  # noqa: E501
    )
    # Source: LLL
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000110> 0 0 0 0 0)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0x66F77B181E0E662E17D427C7320267ADF2FD624,
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
        address=Address("0x3c6dca5471c6305d0642c6210d39d4613b5ea30b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
            + Op.SSTORE(key=0x9, value=Op.GAS)
            + Op.SSTORE(key=0xA, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xccc0159bd2ef7118b5e7b8d958e72237f02493fe"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=2200000,
    )

    post = {
        callee: Account(storage={8: 0x927BE, 12: 1}),
        contract: Account(storage={8: 0x213FB6, 9: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
