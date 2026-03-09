"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refund_CallToSuicideNoStorageFiller.json
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
        "tests/static/state_tests/stRefundTest/refund_CallToSuicideNoStorageFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "00000000000000000000000000000000000000000000000000000000000001f4",
            {
                Address("0x5be4b33890f720eff72be0019b122e0ff75cb937"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000010000",
            {
                Address("0x5be4b33890f720eff72be0019b122e0ff75cb937"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_refund_call_to_suicide_no_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6F0117D3E9C684C7D6E1E6B79DC3880DA2BEBE77C765B171C062FDFFD38A673F
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x5BE4B33890F720EFF72BE0019B122E0FF75CB937)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x4ff65047ce9c85f968689e4369c10003026a41a9"),  # noqa: E501
    )
    # Source: LLL
    # { [[ 0 ]] (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.CALLDATALOAD(offset=0x0),
                    address=0x4FF65047CE9C85F968689E4369C10003026A41A9,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        storage={0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x5be4b33890f720eff72be0019b122e0ff75cb937"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540BE400)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=10000000,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
