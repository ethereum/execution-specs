"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_RawCallGasAskFiller.json
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
    ["tests/static/state_tests/stStaticCall/static_RawCallGasAskFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000001000000000000000000000000000000000000001",
            {
                Address("0x1000000000000000000000000000000000000001"): Account(
                    storage={1: 0xE9F83}
                )
            },
        ),
        (
            "0000000000000000000000002000000000000000000000000000000000000001",
            {
                Address("0x2000000000000000000000000000000000000001"): Account(
                    storage={1: 0xE9F83}
                )
            },
        ),
        (
            "0000000000000000000000003000000000000000000000000000000000000001",
            {
                Address("0x3000000000000000000000000000000000000001"): Account(
                    storage={1: 0xE9C1B}
                )
            },
        ),
        (
            "0000000000000000000000004000000000000000000000000000000000000001",
            {
                Address("0x4000000000000000000000000000000000000001"): Account(
                    storage={1: 0xE9C1B}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_raw_call_gas_ask(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
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
        gas_limit=10000000,
    )

    # Source: LLL
    # { (MSTORE 0 (GAS)) }
    pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x094f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xE8D4A51000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {  (STATICCALL 3000000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0) [[1]] (GAS) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x2DC6C0,
                    address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL 130000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0) [[1]] (GAS) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x1FBD0,
                    address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL 3000000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 8000 0 8000) [[1]] (GAS) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x2DC6C0,
                    address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    args_offset=0x0,
                    args_size=0x1F40,
                    ret_offset=0x0,
                    ret_size=0x1F40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL 130000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 8000 0 8000) [[1]] (GAS) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x1FBD0,
                    address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    args_offset=0x0,
                    args_size=0x1F40,
                    ret_offset=0x0,
                    ret_size=0x1F40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000001"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=1000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
