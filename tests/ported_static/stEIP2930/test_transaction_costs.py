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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/transactionCostsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.parametrize(
    "tx_access_list, expected_post",
    [
        ([], {}),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000103"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000104"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000105"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000001111"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000002222"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000003333"
                            # noqa: E501
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
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000108"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000109"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0xff00000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0xff00000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000fffffffffffffffffffffffff"
                            # noqa: E501
                        )
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                            # noqa: E501
                        ),
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                            # noqa: E501
                        )
                    ],
                ),
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                            # noqa: E501
                        )
                    ],
                ),
            ],
            {},
        ),
        (None, {}),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_access_list: list | None,
    expected_post: dict,
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
        address=Address("0x1bf4bd50bbda0f09948556f87d37f86f2e19e84a"),
        # noqa: E501
    )
    pre[sender] = Account(balance=0x5FA9C18)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=400000,
        value=100000,
        access_list=tx_access_list,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/transactionCostsFiller.yml"],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "tx_access_list, expected_post",
    [
        ([], {}),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000103"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000104"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000105"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000001111"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000002222"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000003333"
                            # noqa: E501
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
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000108"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000fffffffffffffff"
                            # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000109"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"
                            # noqa: E501
                        ),
                    ],
                ),
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0xff00000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0xff00000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000fffffffffffffffffffffffff"
                            # noqa: E501
                        )
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                            # noqa: E501
                        ),
                    ],
                )
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                            # noqa: E501
                        )
                    ],
                ),
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
            ],
            {},
        ),
        (
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"
                            # noqa: E501
                        )
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000102"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                            # noqa: E501
                        )
                    ],
                ),
            ],
            {},
        ),
        (None, {}),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_costs_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_access_list: list | None,
    expected_post: dict,
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
        address=Address("0x1bf4bd50bbda0f09948556f87d37f86f2e19e84a"),
        # noqa: E501
    )
    pre[sender] = Account(balance=0x5FA9C18)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=400000,
        value=100000,
        access_list=tx_access_list,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
