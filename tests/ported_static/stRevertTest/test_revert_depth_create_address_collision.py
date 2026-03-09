"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest
RevertDepthCreateAddressCollisionFiller.json
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
        "tests/static/state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, expected_post",
    [
        (
            "000000000000000000000000000000000000000000000000000000000000ea60",
            110000,
            1,
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000ea60",
            110000,
            0,
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000ea60",
            160000,
            1,
            {
                Address("0x97e33a176b7c8d61b356d1c170ac2119d28867df"): Account(
                    storage={0: 1, 4: 12}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000ea60",
            160000,
            0,
            {
                Address("0x97e33a176b7c8d61b356d1c170ac2119d28867df"): Account(
                    storage={0: 1, 4: 12}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000001ea60",
            110000,
            1,
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000001ea60",
            110000,
            0,
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000001ea60",
            160000,
            1,
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000001ea60",
            160000,
            0,
            {},
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
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

    # Source: LLL
    # { [[0]] 1 [[1]] (CALL (CALLDATALOAD 0) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[4]] 12 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=Op.CALLDATALOAD(offset=0x0),
                    address=0xB1B49241A4ECF7860872E686090781C906B1B437,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.STOP
        ),
        balance=5,
        nonce=54,
        address=Address("0x97e33a176b7c8d61b356d1c170ac2119d28867df"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0x8)
            + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0))
            + Op.SSTORE(key=0x3, value=0xC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb1b49241a4ecf7860872e686090781c906b1b437"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
