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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c6139000000000000000000000000000000000000000000000000000000000000001a",
    "693c6139000000000000000000000000000000000000000000000000000000000000002a",
    "693c6139000000000000000000000000000000000000000000000000000000000000003a",
    "693c6139000000000000000000000000000000000000000000000000000000000000004a",
    "693c6139000000000000000000000000000000000000000000000000000000000000005a",
    "693c6139000000000000000000000000000000000000000000000000000000000000006a",
    "693c6139000000000000000000000000000000000000000000000000000000000000007a",
    "693c6139000000000000000000000000000000000000000000000000000000000000008a",
    "693c6139000000000000000000000000000000000000000000000000000000000000009a",
    "693c613900000000000000000000000000000000000000000000000000000000000000aa",
    "693c613900000000000000000000000000000000000000000000000000000000000000ba",
    "693c613900000000000000000000000000000000000000000000000000000000000000ca",
    "693c613900000000000000000000000000000000000000000000000000000000000000da",
    "693c613900000000000000000000000000000000000000000000000000000000000000ea",
    "693c613900000000000000000000000000000000000000000000000000000000000000fa",
    "693c6139000000000000000000000000000000000000000000000000000000000000010a",
    "693c6139000000000000000000000000000000000000000000000000000000000000011a",
    "693c6139000000000000000000000000000000000000000000000000000000000000012a",
    "693c6139000000000000000000000000000000000000000000000000000000000000013a",
    "693c6139000000000000000000000000000000000000000000000000000000000000014a",
    "693c6139000000000000000000000000000000000000000000000000000000000000015a",
    "693c6139000000000000000000000000000000000000000000000000000000000000016a",
    "693c6139000000000000000000000000000000000000000000000000000000000000017a",
    "693c6139000000000000000000000000000000000000000000000000000000000000018a",
    "693c6139000000000000000000000000000000000000000000000000000000000000019a",
    "693c6139000000000000000000000000000000000000000000000000000000000000020a",
    "693c6139000000000000000000000000000000000000000000000000000000000000001c",
    "693c6139000000000000000000000000000000000000000000000000000000000000002c",
    "693c6139000000000000000000000000000000000000000000000000000000000000003c",
    "693c6139000000000000000000000000000000000000000000000000000000000000004c",
    "693c6139000000000000000000000000000000000000000000000000000000000000005c",
    "693c6139000000000000000000000000000000000000000000000000000000000000006c",
    "693c6139000000000000000000000000000000000000000000000000000000000000007c",
    "693c6139000000000000000000000000000000000000000000000000000000000000008c",
    "693c6139000000000000000000000000000000000000000000000000000000000000009c",
    "693c613900000000000000000000000000000000000000000000000000000000000000ac",
    "693c613900000000000000000000000000000000000000000000000000000000000000bc",
    "693c613900000000000000000000000000000000000000000000000000000000000000cc",
    "693c613900000000000000000000000000000000000000000000000000000000000000dc",
    "693c613900000000000000000000000000000000000000000000000000000000000000ec",
    "693c613900000000000000000000000000000000000000000000000000000000000000fc",
    "693c6139000000000000000000000000000000000000000000000000000000000000010c",
    "693c6139000000000000000000000000000000000000000000000000000000000000011c",
    "693c6139000000000000000000000000000000000000000000000000000000000000012c",
    "693c6139000000000000000000000000000000000000000000000000000000000000013c",
    "693c6139000000000000000000000000000000000000000000000000000000000000014c",
    "693c6139000000000000000000000000000000000000000000000000000000000000015c",
    "693c6139000000000000000000000000000000000000000000000000000000000000016c",
    "693c6139000000000000000000000000000000000000000000000000000000000000017c",
    "693c6139000000000000000000000000000000000000000000000000000000000000018c",
    "693c6139000000000000000000000000000000000000000000000000000000000000019c",
    "693c6139000000000000000000000000000000000000000000000000000000000000020c",
    "693c6139000000000000000000000000000000000000000000000000000000000000001c",
    "693c6139000000000000000000000000000000000000000000000000000000000000002c",
    "693c6139000000000000000000000000000000000000000000000000000000000000003c",
    "693c6139000000000000000000000000000000000000000000000000000000000000004c",
    "693c6139000000000000000000000000000000000000000000000000000000000000005c",
    "693c6139000000000000000000000000000000000000000000000000000000000000006c",
    "693c6139000000000000000000000000000000000000000000000000000000000000007c",
    "693c6139000000000000000000000000000000000000000000000000000000000000008c",
    "693c6139000000000000000000000000000000000000000000000000000000000000009c",
    "693c613900000000000000000000000000000000000000000000000000000000000000ac",
    "693c613900000000000000000000000000000000000000000000000000000000000000bc",
    "693c613900000000000000000000000000000000000000000000000000000000000000cc",
    "693c613900000000000000000000000000000000000000000000000000000000000000dc",
    "693c613900000000000000000000000000000000000000000000000000000000000000ec",
    "693c613900000000000000000000000000000000000000000000000000000000000000fc",
    "693c6139000000000000000000000000000000000000000000000000000000000000010c",
    "693c6139000000000000000000000000000000000000000000000000000000000000011c",
    "693c6139000000000000000000000000000000000000000000000000000000000000012c",
    "693c6139000000000000000000000000000000000000000000000000000000000000013c",
    "693c6139000000000000000000000000000000000000000000000000000000000000014c",
    "693c6139000000000000000000000000000000000000000000000000000000000000015c",
    "693c6139000000000000000000000000000000000000000000000000000000000000016c",
    "693c6139000000000000000000000000000000000000000000000000000000000000017c",
    "693c6139000000000000000000000000000000000000000000000000000000000000018c",
    "693c6139000000000000000000000000000000000000000000000000000000000000019c",
    "693c6139000000000000000000000000000000000000000000000000000000000000020c",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(35, 0, 0, id="case0"),
        pytest.param(36, 0, 0, id="case1"),
        pytest.param(37, 0, 0, id="case2"),
        pytest.param(38, 0, 0, id="case3"),
        pytest.param(39, 0, 0, id="case4"),
        pytest.param(40, 0, 0, id="case5"),
        pytest.param(41, 0, 0, id="case6"),
        pytest.param(42, 0, 0, id="case7"),
        pytest.param(43, 0, 0, id="case8"),
        pytest.param(44, 0, 0, id="case9"),
        pytest.param(45, 0, 0, id="case10"),
        pytest.param(46, 0, 0, id="case11"),
        pytest.param(47, 0, 0, id="case12"),
        pytest.param(48, 0, 0, id="case13"),
        pytest.param(49, 0, 0, id="case14"),
        pytest.param(50, 0, 0, id="case15"),
        pytest.param(51, 0, 0, id="case16"),
        pytest.param(52, 0, 0, id="case17"),
        pytest.param(53, 0, 0, id="case18"),
        pytest.param(54, 0, 0, id="case19"),
        pytest.param(27, 0, 0, id="case20"),
        pytest.param(55, 0, 0, id="case21"),
        pytest.param(56, 0, 0, id="case22"),
        pytest.param(57, 0, 0, id="case23"),
        pytest.param(58, 0, 0, id="case24"),
        pytest.param(59, 0, 0, id="case25"),
        pytest.param(60, 0, 0, id="case26"),
        pytest.param(61, 0, 0, id="case27"),
        pytest.param(62, 0, 0, id="case28"),
        pytest.param(63, 0, 0, id="case29"),
        pytest.param(64, 0, 0, id="case30"),
        pytest.param(28, 0, 0, id="case31"),
        pytest.param(65, 0, 0, id="case32"),
        pytest.param(66, 0, 0, id="case33"),
        pytest.param(67, 0, 0, id="case34"),
        pytest.param(68, 0, 0, id="case35"),
        pytest.param(69, 0, 0, id="case36"),
        pytest.param(70, 0, 0, id="case37"),
        pytest.param(71, 0, 0, id="case38"),
        pytest.param(72, 0, 0, id="case39"),
        pytest.param(73, 0, 0, id="case40"),
        pytest.param(74, 0, 0, id="case41"),
        pytest.param(29, 0, 0, id="case42"),
        pytest.param(75, 0, 0, id="case43"),
        pytest.param(76, 0, 0, id="case44"),
        pytest.param(77, 0, 0, id="case45"),
        pytest.param(30, 0, 0, id="case46"),
        pytest.param(31, 0, 0, id="case47"),
        pytest.param(32, 0, 0, id="case48"),
        pytest.param(33, 0, 0, id="case49"),
        pytest.param(34, 0, 0, id="case50"),
        pytest.param(26, 0, 0, id="case51"),
        pytest.param(9, 0, 0, id="case52"),
        pytest.param(10, 0, 0, id="case53"),
        pytest.param(11, 0, 0, id="case54"),
        pytest.param(12, 0, 0, id="case55"),
        pytest.param(13, 0, 0, id="case56"),
        pytest.param(14, 0, 0, id="case57"),
        pytest.param(15, 0, 0, id="case58"),
        pytest.param(16, 0, 0, id="case59"),
        pytest.param(17, 0, 0, id="case60"),
        pytest.param(18, 0, 0, id="case61"),
        pytest.param(19, 0, 0, id="case62"),
        pytest.param(20, 0, 0, id="case63"),
        pytest.param(21, 0, 0, id="case64"),
        pytest.param(22, 0, 0, id="case65"),
        pytest.param(23, 0, 0, id="case66"),
        pytest.param(24, 0, 0, id="case67"),
        pytest.param(25, 0, 0, id="case68"),
        pytest.param(1, 0, 0, id="case69"),
        pytest.param(2, 0, 0, id="case70"),
        pytest.param(3, 0, 0, id="case71"),
        pytest.param(4, 0, 0, id="case72"),
        pytest.param(5, 0, 0, id="case73"),
        pytest.param(6, 0, 0, id="case74"),
        pytest.param(7, 0, 0, id="case75"),
        pytest.param(8, 0, 0, id="case76"),
        pytest.param(0, 0, 0, id="case77"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jump_to_push(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
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

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                    34,
                    35,
                    36,
                    37,
                    38,
                    39,
                    40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                    48,
                    49,
                    50,
                    51,
                    52,
                    53,
                    54,
                    55,
                    56,
                    57,
                    58,
                    59,
                    60,
                    61,
                    62,
                    63,
                    64,
                    65,
                    66,
                    67,
                    68,
                    69,
                    70,
                    71,
                    72,
                    73,
                    74,
                    75,
                    76,
                    77,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 0})},
        },
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
