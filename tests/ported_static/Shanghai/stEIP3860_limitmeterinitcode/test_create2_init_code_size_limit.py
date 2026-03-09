"""
Test ported from static filler.

Ported from:
tests/static/state_tests/Shanghai/stEIP3860_limitmeterinitcode
create2InitCodeSizeLimitFiller.yml
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
        "tests/static/state_tests/Shanghai/stEIP3860_limitmeterinitcode/create2InitCodeSizeLimitFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000000000000000000000000000000000000000c001",
            {
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000c000",
            {
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={
                        0: 0x9E7A3337D18C31FE4C1FE51AB2DA6CFD3629923D,
                        10: 55539,
                    }
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_create2_init_code_size_limit(
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

    pre[sender] = Account(balance=0xBEBC200)
    # Source: Yul
    # {
    #   mstore(0, calldataload(0))
    #   let call_result := call(10000000, 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b, 0, 0, calldatasize(), 0, 0)  # noqa: E501
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
                    address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
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
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   // :yul { codecopy(0x00, 0x00, 0x0a) return(0x00, 0x0a) }
    #   mstore(0, 0x600a80600080396000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   // get initcode size from calldata
    #   let initcode_size := calldataload(0)
    #   let gas_before := gas()
    #   let create_result := create2(0, 0, initcode_size, 0xdeadbeef)
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
            + Op.PUSH4[0xDEADBEEF]
            + Op.GAS
            + Op.SWAP2
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.CREATE2
            + Op.SWAP1
            + Op.GAS
            + Op.SWAP1
            + Op.SSTORE(key=0xA, value=Op.SUB)
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=15000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
