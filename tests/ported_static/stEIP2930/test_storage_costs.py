"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP2930/storageCostsFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/storageCostsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_access_list, expected_post",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001002"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={1: 2903}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001005"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001005"): Account(
                    storage={1: 103}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001004"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743, 1: 103}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001001"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    storage={1: 100}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001021"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001021"): Account(
                    storage={1: 97}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000011",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001011"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001011"): Account(
                    storage={0: 24743, 1: 100}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001003"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 48879, 1: 2903}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x00000000000000000000000000000000000060a7"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000fffffad"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000000ad"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000123214342ad"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000deadbeef"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000fffff"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000123214342"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000deadbeef"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000010000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000fffffbc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000000bc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000123214342bc"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000deadbeefbc"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0xffffffffffffffffffffffffffffffffffffffff"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000fffffbc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000000bc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000123214342bc"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000deadbeefbc"  # noqa: E501
                        ),
                        Hash(
                            "0xdeadbeef12345678deadbeef12345678deadbeef12345678deadbeef12345678"  # noqa: E501
                        ),
                        Hash(
                            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # noqa: E501
                        ),
                    ],
                ),
            ],
            {
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={0: 2, 1: 20003}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={0: 2, 1: 20003}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001020"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001020"): Account(
                    storage={0: 2, 1: 20000}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001010"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001010"): Account(
                    storage={0: 2, 1: 103}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000fff",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xcccccccccccccccccccccccccccccccccccccccc"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 100, 2: 20000, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={1: 5003}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            None,
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={1: 5003}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001002"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={1: 5003}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743, 1: 2203}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            None,
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743, 1: 2203}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001005"): Account(
                    storage={1: 2203}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            None,
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001005"): Account(
                    storage={1: 2203}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001005"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001005"): Account(
                    storage={1: 2203}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001004"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743, 1: 2203}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    storage={1: 2100}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            None,
            {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    storage={1: 2100}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001001"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    storage={1: 2100}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001021"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001021"): Account(
                    storage={1: 97}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000011",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001011"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001011"): Account(
                    storage={0: 24743, 1: 100}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 48879, 1: 5003}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            None,
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 48879, 1: 5003}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001003"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 48879, 1: 5003}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={0: 2, 1: 22103}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            None,
            {
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={0: 2, 1: 22103}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={0: 2, 1: 22103}
                ),
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001020"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001020"): Account(
                    storage={0: 2, 1: 20000}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001010"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001010"): Account(
                    storage={0: 2, 1: 103}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000fff",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xcccccccccccccccccccccccccccccccccccccccc"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f000"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f001"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f002"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f0a7"  # noqa: E501
                        ),
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000fff",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xcccccccccccccccccccccccccccccccccc000000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
            {
                Address("0x0000000000000000000000000000000000001002"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={0: 24743}
                ),
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        ),
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
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
        "case24",
        "case25",
        "case26",
        "case27",
        "case28",
        "case29",
        "case30",
        "case31",
        "case32",
        "case33",
        "case34",
        "case35",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_storage_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_access_list: list | None,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
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
        gas_limit=71794957647893862,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xBEEF)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x0},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001010"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001011"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001020"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001021"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { ; TO_ADDR_VALID   TO_ADDR_INVALID_ADDR    TO_ADDR_INVALID_CELL
    #   ; Call a different contract
    #   (call (gas) (+ 0x1000 $4) 0 0 0 0 0)
    #
    #   ; Read @@0, and see how much gas that cost.
    #     [0]   (gas)
    #     @@0x60A7
    #     [0]   (- @0 (gas) 19)
    #    [[1]] @0
    #
    #
    #   ; Write to @@0, and see how much gas that cost. It should
    #   ; cost more when it is not declared storage
    #     [0]   (gas)
    #    [[0]]  0x02
    #     [0]   (- @0 (gas) 17)
    #    [[2]] @0
    #
    #   ; The 17 is the cost of the extra opcodes:
    #   ; PUSH1 0x00, MSTORE
    #   ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #   ; GAS
    #
    #
    # }
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x60A7))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x60A7: 0xDEAD},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=400000,
        value=100000,
        access_list=tx_access_list,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
