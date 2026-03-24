"""
Test ported from static filler.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml
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
        "tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ac",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000bc",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000cc",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000dc",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ec",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fc",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000010c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000011c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000012c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000013c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000014c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000015c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000016c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000017c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000018c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000019c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000020c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000002c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000003c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000002c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000004c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000005c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000006c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000007c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000008c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000009c",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ac",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000bc",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000cc",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000dc",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000003c",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ec",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fc",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000010c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000011c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000012c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000013c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000014c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000015c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000016c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000017c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000004c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000018c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000019c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000020c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000005c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000006c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000007c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000008c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000009c",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000001c",  # noqa: E501
            {},
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000aa",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ba",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ca",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000da",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ea",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fa",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000010a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000011a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000012a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000013a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000014a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000015a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000016a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000017a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000018a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000019a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000020a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000002a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000003a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000004a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000005a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000006a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000007a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000008a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000009a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000001a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jump_to_push(
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
        gas_limit=100000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xA)
            + Op.PUSH1[0x5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH1[0x5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xB)
            + Op.PUSH2[0x5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH2[0x5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xA)
            + Op.PUSH2[0x5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xC)
            + Op.PUSH3[0x5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH3[0x5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xB)
            + Op.PUSH3[0x5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xD)
            + Op.PUSH4[0x5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH4[0x5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xC)
            + Op.PUSH4[0x5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xE)
            + Op.PUSH5[0x5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH5[0x5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xD)
            + Op.PUSH5[0x5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xF)
            + Op.PUSH6[0x5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH6[0x5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xE)
            + Op.PUSH6[0x5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x10)
            + Op.PUSH7[0x5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH7[0x5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0xF)
            + Op.PUSH7[0x5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x11)
            + Op.PUSH8[0x5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH8[0x5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x10)
            + Op.PUSH8[0x5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x12)
            + Op.PUSH9[0x5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000009a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH9[0x5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000009b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x11)
            + Op.PUSH9[0x5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000009c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x13)
            + Op.PUSH10[0x5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000aa"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH10[0x5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000ab"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x12)
            + Op.PUSH10[0x5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000ac"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x14)
            + Op.PUSH11[0x5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000ba"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH11[0x5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000bb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x13)
            + Op.PUSH11[0x5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000bc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x15)
            + Op.PUSH12[0x5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000ca"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH12[0x5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000cb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x14)
            + Op.PUSH12[0x5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000cc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x16)
            + Op.PUSH13[0x5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000da"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH13[0x5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000db"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x15)
            + Op.PUSH13[0x5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000dc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x17)
            + Op.PUSH14[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000ea"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH14[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000eb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x16)
            + Op.PUSH14[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000ec"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x18)
            + Op.PUSH15[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000fa"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH15[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000fb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x17)
            + Op.PUSH15[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000000fc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x19)
            + Op.PUSH16[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000010a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH16[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000010b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x18)
            + Op.PUSH16[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000010c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1A)
            + Op.PUSH17[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000011a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH17[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000011b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x19)
            + Op.PUSH17[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000011c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1B)
            + Op.PUSH18[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000012a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH18[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000012b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1A)
            + Op.PUSH18[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000012c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1C)
            + Op.PUSH19[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000013a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH19[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000013b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1B)
            + Op.PUSH19[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000013c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1D)
            + Op.PUSH20[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000014a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH20[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000014b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1C)
            + Op.PUSH20[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000014c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1E)
            + Op.PUSH21[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000015a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH21[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000015b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1D)
            + Op.PUSH21[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000015c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1F)
            + Op.PUSH22[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000016a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH22[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000016b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1E)
            + Op.PUSH22[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000016c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x20)
            + Op.PUSH23[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000017a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH23[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000017b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x1F)
            + Op.PUSH23[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000017c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x21)
            + Op.PUSH24[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000018a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH24[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000018b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x20)
            + Op.PUSH24[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000018c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x22)
            + Op.PUSH25[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000019a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH25[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000019b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x21)
            + Op.PUSH25[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000019c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x23)
            + Op.PUSH26[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001aa"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH26[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001ab"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x22)
            + Op.PUSH26[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001ac"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x24)
            + Op.PUSH27[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001ba"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH27[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001bb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x23)
            + Op.PUSH27[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001bc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x25)
            + Op.PUSH28[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001ca"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH28[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001cb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x24)
            + Op.PUSH28[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001cc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x26)
            + Op.PUSH29[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001da"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH29[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001db"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x25)
            + Op.PUSH29[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001dc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x27)
            + Op.PUSH30[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001ea"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH30[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001eb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x26)
            + Op.PUSH30[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001ec"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x28)
            + Op.PUSH31[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001fa"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH31[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001fb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x27)
            + Op.PUSH31[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000001fc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x29)
            + Op.PUSH32[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x9)
            + Op.PUSH32[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x28)
            + Op.PUSH32[
                0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
            ]
            + Op.JUMPDEST
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: Yul
    # {
    #   let addr := calldataload(4)
    #   pop(delegatecall(sub(gas(), 5000), addr, 0, 0, 0, 0))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x1388),
                address=Op.CALLDATALOAD(offset=0x4),
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x0: 0x0},
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
