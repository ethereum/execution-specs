"""
create2SmartInitCode. create2 works different each time you call it.

Ported from:
tests/static/state_tests/stCreate2/create2SmartInitCodeFiller.json
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
    ["tests/static/state_tests/stCreate2/create2SmartInitCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
            {
                Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"): Account(
                    storage={1: 0xF6510583D425CFCF94B99F8B073B44F60D1912B}
                )
            },
        ),
        (
            "0000000000000000000000001f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
            {
                Address("0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"): Account(
                    storage={1: 0xD27E800C69122409AC5609FE4DF903745F3988A0}
                ),
                Address("0xd27e800c69122409ac5609fe4df903745f3988a0"): Account(
                    storage={1: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_create2_smart_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Create2SmartInitCode. create2 works different each time you call it."""
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
        gas_limit=47244640256,
    )

    # Source: LLL
    # { (MSTORE 0 0x600060015414601157600a6000f3601a565b60016001556001ff5b) [[1]](CREATE2 1 5 27 0) [[2]](CREATE2 1 5 27 0) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x600060015414601157600A6000F3601A565B60016001556001FF5B,
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.CREATE2(value=0x1, offset=0x5, size=0x1B, salt=0x0),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CREATE2(value=0x1, offset=0x5, size=0x1B, salt=0x0),
            )
            + Op.STOP
        ),
        balance=100,
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0x600060015414601157600a6000f3601c565b6001600155600a6000f35b) [[1]](CREATE2 1 3 29 0) [[2]](CREATE2 1 5 27 0) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x600060015414601157600A6000F3601C565B6001600155600A6000F35B,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.CREATE2(value=0x1, offset=0x3, size=0x1D, salt=0x0),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CREATE2(value=0x1, offset=0x5, size=0x1B, salt=0x0),
            )
            + Op.STOP
        ),
        balance=100,
        nonce=0,
        address=Address("0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)
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
        balance=0x6400000000,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=400000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
