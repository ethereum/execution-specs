"""
Test cases for the cost of memory copy in the MCOPY instruction.

Ported from:
tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_copy_costFiller.yml
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
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000aedf",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000aee0",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000aee1",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000aedf",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000aee0",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000aee1",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000aedf",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000aee0",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000aee1",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000aedf",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000aee0",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000aee1",  # noqa: E501
]

TX_GAS = [100000, 55697]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_copy_costFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 1, 0, id="case1"),
        pytest.param(1, 0, 0, id="case2"),
        pytest.param(1, 1, 0, id="case3"),
        pytest.param(2, 0, 0, id="case4"),
        pytest.param(2, 1, 0, id="case5"),
        pytest.param(3, 0, 0, id="case6"),
        pytest.param(3, 1, 0, id="case7"),
        pytest.param(4, 0, 0, id="case8"),
        pytest.param(4, 1, 0, id="case9"),
        pytest.param(5, 0, 0, id="case10"),
        pytest.param(5, 1, 0, id="case11"),
        pytest.param(6, 0, 0, id="case12"),
        pytest.param(6, 1, 0, id="case13"),
        pytest.param(7, 0, 0, id="case14"),
        pytest.param(7, 1, 0, id="case15"),
        pytest.param(8, 0, 0, id="case16"),
        pytest.param(8, 1, 0, id="case17"),
        pytest.param(9, 0, 0, id="case18"),
        pytest.param(9, 1, 0, id="case19"),
        pytest.param(10, 0, 0, id="case20"),
        pytest.param(10, 1, 0, id="case21"),
        pytest.param(11, 0, 0, id="case22"),
        pytest.param(11, 1, 0, id="case23"),
        pytest.param(12, 0, 0, id="case24"),
        pytest.param(12, 1, 0, id="case25"),
        pytest.param(13, 0, 0, id="case26"),
        pytest.param(13, 1, 0, id="case27"),
        pytest.param(14, 0, 0, id="case28"),
        pytest.param(14, 1, 0, id="case29"),
        pytest.param(15, 0, 0, id="case30"),
        pytest.param(15, 1, 0, id="case31"),
        pytest.param(16, 0, 0, id="case32"),
        pytest.param(16, 1, 0, id="case33"),
        pytest.param(17, 0, 0, id="case34"),
        pytest.param(17, 1, 0, id="case35"),
        pytest.param(18, 0, 0, id="case36"),
        pytest.param(18, 1, 0, id="case37"),
        pytest.param(19, 0, 0, id="case38"),
        pytest.param(19, 1, 0, id="case39"),
        pytest.param(20, 0, 0, id="case40"),
        pytest.param(20, 1, 0, id="case41"),
        pytest.param(21, 0, 0, id="case42"),
        pytest.param(21, 1, 0, id="case43"),
        pytest.param(22, 0, 0, id="case44"),
        pytest.param(22, 1, 0, id="case45"),
        pytest.param(23, 0, 0, id="case46"),
        pytest.param(23, 1, 0, id="case47"),
        pytest.param(24, 0, 0, id="case48"),
        pytest.param(24, 1, 0, id="case49"),
        pytest.param(25, 0, 0, id="case50"),
        pytest.param(25, 1, 0, id="case51"),
        pytest.param(26, 0, 0, id="case52"),
        pytest.param(26, 1, 0, id="case53"),
        pytest.param(27, 0, 0, id="case54"),
        pytest.param(27, 1, 0, id="case55"),
        pytest.param(28, 0, 0, id="case56"),
        pytest.param(28, 1, 0, id="case57"),
        pytest.param(29, 0, 0, id="case58"),
        pytest.param(29, 1, 0, id="case59"),
        pytest.param(30, 0, 0, id="case60"),
        pytest.param(30, 1, 0, id="case61"),
        pytest.param(31, 0, 0, id="case62"),
        pytest.param(31, 1, 0, id="case63"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mcopy_copy_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test cases for the cost of memory copy in the MCOPY instruction."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1687174231,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: Yul
    # {
    #   function mcopy(dst, src, size) { verbatim_3i_0o(hex"5e", dst, src, size) }  # noqa: E501
    #
    #   // Put a flag in storage indicating successful execution (will be reverted in case of OOG).  # noqa: E501
    #   sstore(0, 1)
    #
    #   // Expand memory to cover memory expansion cost before MCOPY.
    #   // The test uses up to 1400 memory words.
    #   mstore(44800, 1)
    #
    #   // MCOPY using src and size from CALLDATA to 0 destination.
    #   mcopy(0, calldataload(0), calldataload(32))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.JUMP(pc=0xC)
            + Op.JUMPDEST
            + Op.MCOPY(dest_offset=Op.DUP3, offset=Op.DUP3, size=Op.DUP3)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.SSTORE(key=Op.PUSH0, value=0x1)
            + Op.MSTORE(offset=0xAF00, value=0x1)
            + Op.PUSH1[0x22]
            + Op.CALLDATALOAD(offset=0x20)
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.PUSH0
            + Op.JUMP(pc=0x3)
            + Op.JUMPDEST
        ),
        address=Address("0x9f1a7b52bb2d016223285964cb0876dff8c9c9f8"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 22, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 23, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 24, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 25, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 26, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 27, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 28, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 29, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 30, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 31, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600c565b8282825e505050565b60015f55600161af005260226020355f355f6003565b"  # noqa: E501
                    )
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
