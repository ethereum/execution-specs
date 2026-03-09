"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json
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
        "tests/static/state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000002f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd",
            {
                Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd"): Account(
                    storage={0: 1}
                ),
                Address("0xe4552fdc3736d39144e64ad1a1e8253017b0c974"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
            {
                Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"): Account(
                    storage={0: 1}
                ),
                Address("0xe4552fdc3736d39144e64ad1a1e8253017b0c974"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcallcode_001_2(
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
        gas_limit=30000000,
    )

    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALLCODE(
                    gas=0x3D090,
                    address=0x2881A083EA775F78057A93F73110241FDB7398A9,
                    value=0x3,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0ffffaeb931552e5f094ca96a70be612da56b887"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x11223344) + Op.STOP,
        nonce=0,
        address=Address("0x2881a083ea775f78057a93f73110241fdb7398a9"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0x52BC8086D7F6AC48937CF1B98DFC6F4BE0F75112,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x493E0,
                    address=0xFFFFAEB931552E5F094CA96A70BE612DA56B887,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x52bc8086d7f6ac48937cf1b98dfc6f4be0f75112"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x4, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x3D090,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x6, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x5517c40699ceb16c4eb71f2b0d841078c198560e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x493E0,
                    address=0x5517C40699CEB16C4EB71F2B0D841078C198560E,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb4631a307a08abc5d5a582549b23cb98a7c5beb2"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0xB4631A307A08ABC5D5A582549B23CB98A7C5BEB2,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1}
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe4552fdc3736d39144e64ad1a1e8253017b0c974"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=3000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
