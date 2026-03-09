"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertSubCallStorageOOG2Filler.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertSubCallStorageOOG2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_value, expected_post",
    [
        (61500, 0, {}),
        (61500, 1, {}),
        (
            181000,
            0,
            {
                Address("0x48bc00be37fe77bd0f7b7b8009f908fc534a028b"): Account(
                    storage={0: 13, 1: 14}
                )
            },
        ),
        (181000, 1, {}),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_revert_sub_call_storage_oog2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_value: int,
    expected_post: dict,
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex(
            "60606040526000357c010000000000000000000000000000000000000000000000000000"  # noqa: E501
            "0000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b34"  # noqa: E501
            "60005760506076565b005b34600057605c6081565b604051808215151515815260200191"  # noqa: E501
            "505060405180910390f35b600c6000819055505b565b600060896076565b600d60008190"  # noqa: E501
            "5550600e6001819055505b905600a165627a7a72305820b7c6987c21e63fed8a74d89955"  # noqa: E501
            "7744a3be8d3fda191ce0f56cf261d6b860f6b40029"
        ),
        balance=1,
        nonce=0,
        address=Address("0x48bc00be37fe77bd0f7b7b8009f908fc534a028b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
