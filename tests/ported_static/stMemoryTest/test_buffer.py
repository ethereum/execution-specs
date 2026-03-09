"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stMemoryTest/bufferFiller.yml
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
    ["tests/static/state_tests/stMemoryTest/bufferFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f1000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f1000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f1000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f1000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f2000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f2000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f2000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f2000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000000d",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={256: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000019",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000001b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000039000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000013e000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a10000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a1000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a20000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a2000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a30000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a3000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a40000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000a4000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f10000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f1000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f1000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000d",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f20000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f2000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f2000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f40000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001f4000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000370000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000001fa000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000000000000000000000000000000000000000000037000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000f30c0de"): Account(
                    storage={0: 24743}
                )
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
        "case36",
        "case37",
        "case38",
        "case39",
        "case40",
        "case41",
        "case42",
        "case43",
        "case44",
        "case45",
        "case46",
        "case47",
        "case48",
        "case49",
        "case50",
        "case51",
        "case52",
        "case53",
        "case54",
        "case55",
        "case56",
        "case57",
        "case58",
        "case59",
        "case60",
        "case61",
        "case62",
        "case63",
        "case64",
        "case65",
        "case66",
        "case67",
        "case68",
        "case69",
        "case70",
        "case71",
        "case72",
        "case73",
        "case74",
        "case75",
        "case76",
        "case77",
        "case78",
        "case79",
        "case80",
        "case81",
        "case82",
        "case83",
        "case84",
        "case85",
        "case86",
        "case87",
        "case88",
        "case89",
        "case90",
        "case91",
        "case92",
        "case93",
        "case94",
        "case95",
        "case96",
        "case97",
        "case98",
        "case99",
        "case100",
        "case101",
        "case102",
        "case103",
        "case104",
        "case105",
        "case106",
        "case107",
        "case108",
        "case109",
        "case110",
        "case111",
        "case112",
        "case113",
        "case114",
        "case115",
        "case116",
        "case117",
        "case118",
        "case119",
        "case120",
        "case121",
        "case122",
        "case123",
        "case124",
        "case125",
        "case126",
        "case127",
        "case128",
        "case129",
        "case130",
        "case131",
        "case132",
        "case133",
        "case134",
        "case135",
        "case136",
        "case137",
        "case138",
        "case139",
        "case140",
        "case141",
        "case142",
        "case143",
        "case144",
        "case145",
        "case146",
        "case147",
        "case148",
        "case149",
        "case150",
        "case151",
        "case152",
        "case153",
        "case154",
        "case155",
        "case156",
        "case157",
        "case158",
        "case159",
        "case160",
        "case161",
        "case162",
        "case163",
        "case164",
        "case165",
        "case166",
        "case167",
        "case168",
        "case169",
        "case170",
        "case171",
        "case172",
        "case173",
        "case174",
        "case175",
        "case176",
        "case177",
        "case178",
        "case179",
        "case180",
        "case181",
        "case182",
        "case183",
        "case184",
        "case185",
        "case186",
        "case187",
        "case188",
        "case189",
        "case190",
        "case191",
        "case192",
        "case193",
        "case194",
        "case195",
        "case196",
        "case197",
        "case198",
        "case199",
        "case200",
        "case201",
        "case202",
        "case203",
        "case204",
        "case205",
        "case206",
        "case207",
        "case208",
        "case209",
        "case210",
        "case211",
        "case212",
        "case213",
        "case214",
        "case215",
        "case216",
        "case217",
        "case218",
        "case219",
        "case220",
        "case221",
        "case222",
        "case223",
        "case224",
        "case225",
        "case226",
        "case227",
        "case228",
        "case229",
        "case230",
        "case231",
        "case232",
        "case233",
        "case234",
        "case235",
        "case236",
        "case237",
        "case238",
        "case239",
        "case240",
        "case241",
        "case242",
        "case243",
        "case244",
        "case245",
        "case246",
        "case247",
        "case248",
        "case249",
        "case250",
        "case251",
        "case252",
        "case253",
        "case254",
        "case255",
        "case256",
        "case257",
        "case258",
        "case259",
        "case260",
        "case261",
        "case262",
        "case263",
        "case264",
        "case265",
        "case266",
        "case267",
        "case268",
        "case269",
        "case270",
        "case271",
        "case272",
        "case273",
        "case274",
        "case275",
        "case276",
        "case277",
        "case278",
        "case279",
        "case280",
        "case281",
        "case282",
        "case283",
        "case284",
        "case285",
        "case286",
        "case287",
        "case288",
        "case289",
        "case290",
        "case291",
        "case292",
        "case293",
        "case294",
        "case295",
        "case296",
        "case297",
        "case298",
        "case299",
        "case300",
        "case301",
        "case302",
        "case303",
        "case304",
        "case305",
        "case306",
        "case307",
        "case308",
        "case309",
        "case310",
        "case311",
        "case312",
        "case313",
        "case314",
        "case315",
        "case316",
        "case317",
        "case318",
        "case319",
        "case320",
        "case321",
        "case322",
        "case323",
        "case324",
        "case325",
        "case326",
        "case327",
        "case328",
        "case329",
        "case330",
        "case331",
        "case332",
        "case333",
        "case334",
        "case335",
        "case336",
        "case337",
        "case338",
        "case339",
        "case340",
        "case341",
        "case342",
        "case343",
        "case344",
        "case345",
        "case346",
        "case347",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_buffer(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
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
        gas_limit=100000000,
    )

    # Source: LLL
    # {
    #       (return 0 0x120)
    # }
    pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0x120) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    # Source: LLL
    # {
    #        ; We get length from the caller
    #        (def 'length $0)
    #        (def 'offset $0x20)
    #
    #        [[0]] 0    ; capricide
    #        (return offset length)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x0)
            + Op.RETURN(
                offset=Op.CALLDATALOAD(offset=0x20),
                size=Op.CALLDATALOAD(offset=0x0),
            )
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000f30c0de"),  # noqa: E501
    )
    # Source: LLL
    # {
    #        ; We get length from the caller
    #        (def 'length $0)
    #        (def 'offset $0x20)
    #
    #        (revert offset length)
    # }
    pre.deploy_contract(
        code=(
            Op.REVERT(
                offset=Op.CALLDATALOAD(offset=0x20),
                size=Op.CALLDATALOAD(offset=0x0),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000ff0c0de"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #    (def 'opcode $4)
    #    (def 'bufferType $36)
    #    (def 'NOP 0)
    #
    #    ; Variables
    #    (def 'length     0x2020)
    #    (def 'offset     0x2040)
    #
    #    ; bufferTypes  0 is normal, 1 is length zero, 2 is negative length
    #    ; bufferType 3 is excessively long, for opcodes with bounds checking
    #    ; Add 0 for offset 0x100, 10 for offset 0x0
    #
    #    ; High offsets:
    #    ; 20 for 2^256-10
    #    ; 21 for 2^31-1
    #    ; 22 for 2^31
    #    ; 23 for 2^32-1
    #    ; 24 for 2^32
    #    ; 25 for 2^63-1
    #    ; 26 for 2^63
    #    ; 27 for 2^64-1
    #    ; 28 for 2^64
    #    (if (= bufferType 0) {
    #            [length] 10
    #            [offset] 0x100
    #      } NOP)
    #    (if (= bufferType 1) {
    #            [length] 0
    #            [offset] 0x100
    # ... (113 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=Op.PUSH2[0x11],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x1F])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0xA)
            + Op.MSTORE(offset=0x2040, value=0x100)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x31],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x3F])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x0)
            + Op.MSTORE(offset=0x2040, value=0x100)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x51],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x2),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x62])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=Op.SUB(0x0, 0xA))
            + Op.MSTORE(offset=0x2040, value=0x100)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x74],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x3),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x83])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x1000)
            + Op.MSTORE(offset=0x2040, value=0x100)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x95],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xA),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xA2])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0xA)
            + Op.MSTORE(offset=0x2040, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xB4],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xB),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xC1])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x0)
            + Op.MSTORE(offset=0x2040, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xD3],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xC),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0xE3])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=Op.SUB(0x0, 0xA))
            + Op.MSTORE(offset=0x2040, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xF5],
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xD),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x103)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x1000)
            + Op.MSTORE(offset=0x2040, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x115,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x14),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x125)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=Op.SUB(0x0, 0xA))
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x137,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x15),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x147)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0x7FFFFFFF)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x159,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x16),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x169)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0x80000000)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x17B,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x17),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x18B)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0xFFFFFFFF)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x19D,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x18),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1AE)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0x100000000)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C0,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x19),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1D4)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0x7FFFFFFFFFFFFFFF)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1E6,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1A),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1FA)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0x8000000000000000)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x20C,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1B),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x220)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0xFFFFFFFFFFFFFFFF)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x232,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1C),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x247)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2020, value=0x5)
            + Op.MSTORE(offset=0x2040, value=0x10000000000000000)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x258,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x20),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x262)
            + Op.JUMPDEST
            + Op.SHA3(
                offset=Op.MLOAD(offset=0x2040), size=Op.MLOAD(offset=0x2020)
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x275,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x37),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x281)
            + Op.JUMPDEST
            + Op.CALLDATACOPY(
                dest_offset=Op.MLOAD(offset=0x2040),
                offset=0x0,
                size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x293,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x39),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x29F)
            + Op.JUMPDEST
            + Op.CODECOPY(
                dest_offset=Op.MLOAD(offset=0x2040),
                offset=0x0,
                size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2B1,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3C),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x2C0)
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xC0DE,
                dest_offset=Op.MLOAD(offset=0x2040),
                offset=0x0,
                size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2D2,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3E),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x2DE)
            + Op.JUMPDEST
            + Op.RETURNDATACOPY(
                dest_offset=Op.MLOAD(offset=0x2040),
                offset=0x0,
                size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2F0,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA0),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x2FA)
            + Op.JUMPDEST
            + Op.LOG0(
                offset=Op.MLOAD(offset=0x2040), size=Op.MLOAD(offset=0x2020)
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x30C,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA1),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x318)
            + Op.JUMPDEST
            + Op.LOG1(
                offset=Op.MLOAD(offset=0x2040),
                size=Op.MLOAD(offset=0x2020),
                topic_1=0x1,
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x32A,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA2),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x338)
            + Op.JUMPDEST
            + Op.LOG2(
                offset=Op.MLOAD(offset=0x2040),
                size=Op.MLOAD(offset=0x2020),
                topic_1=0x1,
                topic_2=0x2,
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x34A,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA3),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x35A)
            + Op.JUMPDEST
            + Op.LOG3(
                offset=Op.MLOAD(offset=0x2040),
                size=Op.MLOAD(offset=0x2020),
                topic_1=0x1,
                topic_2=0x2,
                topic_3=0x3,
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x36C,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA4),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x37E)
            + Op.JUMPDEST
            + Op.LOG4(
                offset=Op.MLOAD(offset=0x2040),
                size=Op.MLOAD(offset=0x2020),
                topic_1=0x1,
                topic_2=0x2,
                topic_3=0x3,
                topic_4=0x4,
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x38F,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF0),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x39B)
            + Op.JUMPDEST
            + Op.CREATE(
                value=0x0,
                offset=Op.MLOAD(offset=0x2040),
                size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x3AD,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x3C3)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xC0DE,
                value=0x0,
                args_offset=Op.MLOAD(offset=0x2040),
                args_size=Op.MLOAD(offset=0x2020),
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x3D6,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1F1),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x3EC)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xC0DE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=Op.MLOAD(offset=0x2040),
                ret_size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x3FE,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x414)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xC0DE,
                value=0x0,
                args_offset=Op.MLOAD(offset=0x2040),
                args_size=Op.MLOAD(offset=0x2020),
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x427,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1F2),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x43D)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xC0DE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=Op.MLOAD(offset=0x2040),
                ret_size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x44F,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x464)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x100000,
                address=0xC0DE,
                args_offset=Op.MLOAD(offset=0x2040),
                args_size=Op.MLOAD(offset=0x2020),
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x477,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1F4),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x48C)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x100000,
                address=0xC0DE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=Op.MLOAD(offset=0x2040),
                ret_size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x49E,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF5),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4AD)
            + Op.JUMPDEST
            + Op.CREATE2(
                value=0x0,
                offset=Op.MLOAD(offset=0x2040),
                size=Op.MLOAD(offset=0x2020),
                salt=0x5A17,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x4BF,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4D4)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x100000,
                address=0xC0DE,
                args_offset=Op.MLOAD(offset=0x2040),
                args_size=Op.MLOAD(offset=0x2020),
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x4E7,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1FA),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4FC)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x100000,
                address=0xC0DE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=Op.MLOAD(offset=0x2040),
                ret_size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x510,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x13E),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x530)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=0x1000,
                    address=0xC0DE,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x100,
                    ret_size=0x100,
                ),
            )
            + Op.RETURNDATACOPY(
                dest_offset=Op.MLOAD(offset=0x2040),
                offset=0x0,
                size=Op.MLOAD(offset=0x2020),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x541,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF3),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x557)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x100000,
                address=0xF30C0DE,
                value=0x0,
                args_offset=0x2020,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=0x56A,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFF),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x585)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALL(
                    gas=0x100000,
                    address=0xFF0C0DE,
                    value=0x0,
                    args_offset=0x2020,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x0)
            + Op.STOP
        ),
        storage={0x100: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
