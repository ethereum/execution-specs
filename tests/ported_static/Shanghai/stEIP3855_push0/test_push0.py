"""
Test ported from static filler.

Ported from:
tests/static/state_tests/Shanghai/stEIP3855_push0/push0Filler.yml
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
    ["tests/static/state_tests/Shanghai/stEIP3855_push0/push0Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000000000000000200",
            {
                Address("0x0000000000000000000000000000000000000200"): Account(
                    storage={0: 1}
                ),
                Address("0x0000000000000000000000000000000000000400"): Account(
                    storage={0: 10, 1: 10}
                ),
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000000000000000000300",
            {
                Address("0x0000000000000000000000000000000000000400"): Account(
                    storage={0: 10, 1: 10}
                ),
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000000000000000000700",
            {
                Address("0x0000000000000000000000000000000000000400"): Account(
                    storage={0: 10, 1: 10}
                ),
                Address("0x0000000000000000000000000000000000000700"): Account(
                    storage={0: 1}
                ),
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000000000000000000400",
            {
                Address("0x0000000000000000000000000000000000000400"): Account(
                    storage={0: 2}
                ),
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000000000000000000500",
            {
                Address("0x0000000000000000000000000000000000000400"): Account(
                    storage={0: 10, 1: 10}
                ),
                Address("0x0000000000000000000000000000000000000500"): Account(
                    storage={0: 1, 1: 1, 2: 255}
                ),
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000000000000000001000",
            {
                Address("0x0000000000000000000000000000000000000400"): Account(
                    storage={0: 10, 1: 10}
                ),
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={0: 1}
                ),
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_push0(
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
        gas_limit=89128960,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"  # noqa: E501
            "5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f1717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "171717171717171717171717171717171717171717171717171717171717171717171717"  # noqa: E501
            "1717171717171717171717171717171717171717171717171717171717171760019055"  # noqa: E501
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000300"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=Op.PUSH0, value=0x2) + Op.SSTORE(key=0x1, value=0x0)
        ),
        storage={0x0: 0xA, 0x1: 0xA},
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000400"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0x600,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.RETURNDATACOPY(dest_offset=0x1F, offset=0x0, size=0x1)
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000500"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=Op.PUSH0, value=0xFF)
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000600"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMP(pc=0x4)
            + Op.PUSH0
            + Op.JUMPDEST
            + Op.SSTORE(key=Op.PUSH0, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000700"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SSTORE(key=Op.PUSH0, value=0x1),
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: Yul
    # {
    #     sstore(0, call(100000, shr(96, calldataload(0)), 0, 0, 0, 0, 0))
    #     sstore(1, 1)
    #   }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=Op.SHR(0x60, Op.CALLDATALOAD(offset=Op.DUP1)),
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=700000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
