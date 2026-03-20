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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/coinbaseT01Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v, tx_access_list",
    [
        pytest.param(0, 0, 0, None, id="case0"),
        pytest.param(
            1,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3"
                    ),
                    storage_keys=[],
                )
            ],
            id="case1",
        ),
        pytest.param(
            2,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000ba5a"
                    ),
                    storage_keys=[],
                )
            ],
            id="case2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_t01(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
    tx_access_list: list | None,
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

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 6800},
                    code=bytes.fromhex(
                        "5a6000526000808080620f4240737704d8a022a1ba8f3539fc82c7d7fb065abc0df35af1505a6020526021602051600051030360005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 6800},
                    code=bytes.fromhex(
                        "5a6000526000808080620f4240737704d8a022a1ba8f3539fc82c7d7fb065abc0df35af1505a6020526021602051600051030360005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 6800},
                    code=bytes.fromhex(
                        "5a6000526000808080620f4240737704d8a022a1ba8f3539fc82c7d7fb065abc0df35af1505a6020526021602051600051030360005500"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=1000,
        nonce=1,
        value=TX_VALUE[v],
        access_list=tx_access_list,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
