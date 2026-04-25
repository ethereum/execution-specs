"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/transactionCostsFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam, Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP2930/transactionCostsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="type0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="addrs_0_keys_0",
        ),
        pytest.param(
            2,
            0,
            0,
            id="addrs_1_keys_0",
        ),
        pytest.param(
            3,
            0,
            0,
            id="addrs_1_keys_1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="addrs_1_keys_1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="addrs_1_keys_1",
        ),
        pytest.param(
            6,
            0,
            0,
            id="addrs_1_keys_2",
        ),
        pytest.param(
            7,
            0,
            0,
            id="addrs_2_keys_2",
        ),
        pytest.param(
            8,
            0,
            0,
            id="addrs_2_keys_2",
        ),
        pytest.param(
            9,
            0,
            0,
            id="addrs_2_keys_2",
        ),
        pytest.param(
            10,
            0,
            0,
            id="addrs_1_keys_2",
        ),
        pytest.param(
            11,
            0,
            0,
            id="addrs_10_keys_25",
        ),
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
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x5FA9C18)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: raw
    # 0x00
    target = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
    )

    expect_entries: list[dict] = [
        # EIP-7981 changes access list costs in Amsterdam+. Balance is a
        # placeholder; the expected value is computed dynamically below.
        # Ordered first so Amsterdam+ forks match here instead of the
        # entries below.
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Amsterdam"],
            "result": {sender: Account(balance=0)},
        },
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": ["Cancun"],
            "result": {sender: Account(balance=0x5F5E100)},
        },
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Prague"],
            "result": {sender: Account(balance=0x5F5E0C4)},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(balance=0x5F58340)},
        },
        {
            "indexes": {"data": [3, 4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(balance=0x5F53908)},
        },
        {
            "indexes": {"data": [6, 10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(balance=0x5F4EED0)},
        },
        {
            "indexes": {"data": [7, 8, 9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(balance=0x5F49110)},
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(balance=0x5EAF808)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries, d, g, v, fork)

    tx_data = [
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
    ]
    tx_gas = [400000]
    tx_value = [100000]
    tx_access_lists: dict[int, list] = {
        1: [],
        2: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000102),
                storage_keys=[],
            ),
        ],
        3: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        4: [
            AccessList(
                address=Address(0xFF00000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        5: [
            AccessList(
                address=Address(0xFF00000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000fffffffffffffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        6: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        7: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000102),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        8: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        9: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        10: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        11: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000100),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000102),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000103),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000104),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000105),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000001111"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000002222"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000003333"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000106),
                storage_keys=[],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000107),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000108),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000fffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000000000000000109),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    # EIP-7981 (access list repricing) activates in Amsterdam. Compute the
    # expected balance dynamically from the fork's intrinsic cost calculator
    # rather than hardcoding values that change as EIP-7981 evolves. Past
    # forks keep their original hardcoded values above.
    if _exc is None and fork >= Amsterdam:
        sender_pre = pre[sender]
        assert sender_pre is not None
        gas_price = int(tx.gas_price or tx.max_fee_per_gas or 0)
        intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
            calldata=tx.data,
            contract_creation=tx.to is None,
            access_list=tx.access_list,
        )
        post[sender] = Account(
            balance=(
                int(sender_pre.balance)
                - int(tx.value)
                - intrinsic_gas * gas_price
            ),
        )

    state_test(env=env, pre=pre, post=post, tx=tx)
