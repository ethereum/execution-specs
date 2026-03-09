"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP2930/coinbaseT01Filler.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
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
    ["tests/static/state_tests/stEIP2930/coinbaseT01Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_access_list, expected_post",
    [
        (
            None,
            {
                Address("0x30873f83c35401e315e6e5994c012f1ee8119585"): Account(
                    storage={0: 6800}
                )
            },
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3"
                    ),
                    storage_keys=[],
                )
            ],
            {
                Address("0x30873f83c35401e315e6e5994c012f1ee8119585"): Account(
                    storage={0: 6800}
                )
            },
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000ba5a"
                    ),
                    storage_keys=[],
                )
            ],
            {
                Address("0x30873f83c35401e315e6e5994c012f1ee8119585"): Account(
                    storage={0: 6800}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_t01(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_access_list: list | None,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    sender = EOA(
        key=0xDE0C95357363DA5C1C5A73BD7C2781CA5C9FECC1014103B5E1D1E990AE8208EC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=100,
        gas_limit=71794957647893862,
    )

    # Source: Yul
    # {
    #   mstore(0, gas())
    #   pop(call(gas(), <eoa:0x000000000000000000000000000000000000ba5e>, 1000000, 0, 0, 0, 0))  # noqa: E501
    #   mstore(0x20, gas())
    #
    #   // The 24 is the cost of twi gas(), seven pushes(), a pop(), and an mstore()  # noqa: E501
    #   sstore(0, sub(sub(mload(0), mload(0x20)),33))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x7704D8A022A1BA8F3539FC82C7D7FB065ABC0DF3,
                    value=0xF4240,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x21,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x30873f83c35401e315e6e5994c012f1ee8119585"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "693c61390000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
        gas_limit=16777216,
        gas_price=1000,
        nonce=1,
        access_list=tx_access_list,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
