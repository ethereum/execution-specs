"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP2930/transactionCostsFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "00",
    "00",
    "00",
    "00",
    "00",
    "00",
    "00",
    "00",
    "00",
    "00",
    "00",
]

TX_GAS = [400000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/transactionCostsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v, tx_access_list",
    [
        pytest.param(0, 0, 0, [], id="case0"),
        pytest.param(
            1,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000103"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000104"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000105"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000001111"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000002222"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000003333"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000106"
                    ),
                    storage_keys=[],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000107"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000108"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000109"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        ),
                    ],
                ),
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
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[],
                )
            ],
            id="case2",
        ),
        pytest.param(
            3,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0xff00000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case3",
        ),
        pytest.param(
            4,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0xff00000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000fffffffffffffffffffffffff"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case4",
        ),
        pytest.param(
            5,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case5",
        ),
        pytest.param(
            6,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case6",
        ),
        pytest.param(
            7,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case7",
        ),
        pytest.param(
            8,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        )
                    ],
                ),
            ],
            id="case8",
        ),
        pytest.param(
            9,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                ),
            ],
            id="case9",
        ),
        pytest.param(
            10,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        )
                    ],
                ),
            ],
            id="case10",
        ),
        pytest.param(0, 0, 0, None, id="case11"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
    tx_access_list: list | None,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x7778A3B885EA30938725C6E00831943A454477163CDBC252DEBEB9612B4FA5F7
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex("00"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x1bf4bd50bbda0f09948556f87d37f86f2e19e84a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5FA9C18)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("00"))},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        access_list=tx_access_list,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
