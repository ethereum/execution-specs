"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json
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
        "tests/static/state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000000000000000000000000000000000000000000",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000001",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000002",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={
                        0: 0x8209944E898F69A7BD10A23C839D341E935FD5CA,
                        2: 1,
                    }
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000003",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={
                        0: 0x4300A157335CB7C9FC9423E011D7DD51090D093F,
                        2: 1,
                    }
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000004",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000005",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000006",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000007",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000008",
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
        "case8",
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_ecrecover0_0input(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
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
    # { [[ 2 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0)),
            )
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=3652240,
        value=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000000000000000000000000000000000000000000",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000001",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000002",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={
                        0: 0x8209944E898F69A7BD10A23C839D341E935FD5CA,
                        2: 1,
                    }
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000003",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={
                        0: 0x4300A157335CB7C9FC9423E011D7DD51090D093F,
                        2: 1,
                    }
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000004",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000005",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000006",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000007",
            {
                Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"): Account(
                    storage={2: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000008",
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
        "case8",
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_ecrecover0_0input_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
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
    # { [[ 2 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0)),
            )
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=3652240,
        value=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
