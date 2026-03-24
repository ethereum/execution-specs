"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refundSuicide50procentCapFiller.json
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
        "tests/static/state_tests/stRefundTest/refundSuicide50procentCapFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "00000000000000000000000000000000000000000000000000000000000001f4",
            {
                Address("0xa6cc2ca5611255d50118601aa8ece6f124fc4c45"): Account(
                    storage={10: 1, 23: 0x107A7}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000010000",
            {
                Address("0xa6cc2ca5611255d50118601aa8ece6f124fc4c45"): Account(
                    storage={10: 1, 11: 1, 23: 0x166FA}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_refund_suicide50procent_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
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
            Op.SELFDESTRUCT(address=0xA6CC2CA5611255D50118601AA8ECE6F124FC4C45)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x4ff65047ce9c85f968689e4369c10003026a41a9"),  # noqa: E501
    )
    # Source: LLL
    # { [22] (GAS) [[ 10 ]] 1 [[ 11 ]] (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 ) [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 [[ 6 ]] 0 [[ 7 ]] 0 [[ 8 ]] 0 [[ 23 ]] (SUB @22 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x16, value=Op.GAS)
            + Op.SSTORE(key=0xA, value=0x1)
            + Op.SSTORE(
                key=0xB,
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
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.SSTORE(key=0x6, value=0x0)
            + Op.SSTORE(key=0x7, value=0x0)
            + Op.SSTORE(key=0x8, value=0x0)
            + Op.SSTORE(key=0x17, value=Op.SUB(Op.MLOAD(offset=0x16), Op.GAS))
            + Op.STOP
        ),
        storage={
            0x1: 0x1,
            0x2: 0x1,
            0x3: 0x1,
            0x4: 0x1,
            0x5: 0x1,
            0x6: 0x1,
            0x7: 0x1,
            0x8: 0x1,
        },
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa6cc2ca5611255d50118601aa8ece6f124fc4c45"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)
    pre[coinbase] = Account(balance=0, nonce=1)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=10000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
