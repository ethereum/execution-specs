"""
Test ported from static filler.

Ported from:
tests/static/state_tests/Shanghai/stEIP3860_limitmeterinitcode
createInitCodeSizeLimitFiller.yml
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
        "tests/static/state_tests/Shanghai/stEIP3860_limitmeterinitcode/createInitCodeSizeLimitFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000000000000000000000000000000000000000c001",
            {
                Address("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000c000",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0x5F6BAAEB5B7C97725F84D1569C4ABC85135F4716,
                        10: 46323,
                    }
                ),
                Address("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_create_init_code_size_limit(
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
        gas_limit=20000000,
    )

    # Source: Yul
    # {
    #   // :yul { codecopy(0x00, 0x00, 0x0a) return(0x00, 0x0a) }
    #   mstore(0, 0x600a80600080396000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   // get initcode size from calldata
    #   let initcode_size := calldataload(0)
    #   let gas_before := gas()
    #   let create_result := create(0, 0, initcode_size)
    #   sstore(10, sub(gas_before, gas()))
    #   sstore(0, create_result)
    # }
    pre.deploy_contract(
        code=(
            Op.SHL(0xB0, 0x600A80600080396000F3)
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.CALLDATALOAD
            + Op.GAS
            + Op.SWAP1
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.CREATE
            + Op.SWAP1
            + Op.GAS
            + Op.SWAP1
            + Op.SSTORE(key=0xA, value=Op.SUB)
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.STOP
        ),
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBEBC200, nonce=1)
    # Source: Yul
    # {
    #   mstore(0, calldataload(0))
    #   let call_result := call(10000000, 0xc0de, 0, 0, calldatasize(), 0, 0)
    #   sstore(0, call_result)
    #   sstore(1, 1)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x989680,
                    address=0xC0DE,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.STOP
        ),
        address=Address("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=15000000,
        nonce=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
