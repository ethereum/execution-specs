"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callCreateFiller.json
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
    ["tests/static/state_tests/stStaticCall/static_callCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000f5c27325e6c5769b6569971cd81e01570fd30ef1",
            {
                Address("0xe49f04b30026f23e9e04493c44ece7cfec9224ca"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "00000000000000000000000029d4d72a31d1b141b2067d1d4193bdf12fcddc41",
            {},
        ),
        (
            "000000000000000000000000b4aa7cc91d100eddc01f22ca32f643bb0f1c91cc",
            {
                Address("0xe49f04b30026f23e9e04493c44ece7cfec9224ca"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "000000000000000000000000f9ecfe0635fefb5ad44418f97d7fcaf210ebd5aa",
            {
                Address("0xe49f04b30026f23e9e04493c44ece7cfec9224ca"): Account(
                    storage={0: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_create(
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

    pre.deploy_contract(
        code=Op.CREATE(value=0x0, offset=0x1, size=0x1) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=0x249F0,
                address=0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb4aa7cc91d100eddc01f22ca32f643bb0f1c91cc"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xe49f04b30026f23e9e04493c44ece7cfec9224ca"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x249F0,
                address=0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xf5c27325e6c5769b6569971cd81e01570fd30ef1"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x249F0,
                address=0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xf9ecfe0635fefb5ad44418f97d7fcaf210ebd5aa"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=1000000,
        value=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
