"""
Test cases for the memory expansion cost in the MCOPY instruction.

Ported from:
tests/static/state_tests/Cancun/stEIP5656_MCOPY
MCOPY_memory_expansion_costFiller.yml
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
        "tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_expansion_costFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mcopy_memory_expansion_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test cases for the memory expansion cost in the MCOPY instruction."""
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
    #   // Take most of the SSTORE cost before MCOPY.
    #   sstore(0, 1)
    #
    #   // MCOPY using parameters from CALLDATA.
    #   mcopy(calldataload(0), calldataload(32), calldataload(64))
    #
    #   // Put MSIZE in storage.
    #   sstore(0, msize())
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=Op.PUSH0, value=0x1)
            + Op.MCOPY(
                dest_offset=Op.CALLDATALOAD(offset=Op.PUSH0),
                offset=Op.CALLDATALOAD(offset=0x20),
                size=Op.CALLDATALOAD(offset=0x40),
            )
            + Op.SSTORE(key=Op.PUSH0, value=Op.MSIZE)
            + Op.STOP
        ),
        storage={0x0: 0xFA11ED},
        address=Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_expansion_costFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 768}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 1408}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
                )
            },
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # noqa: E501
            {
                Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"): Account(
                    storage={0: 0xFA11ED}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mcopy_memory_expansion_cost_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test cases for the memory expansion cost in the MCOPY instruction."""
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
    #   // Take most of the SSTORE cost before MCOPY.
    #   sstore(0, 1)
    #
    #   // MCOPY using parameters from CALLDATA.
    #   mcopy(calldataload(0), calldataload(32), calldataload(64))
    #
    #   // Put MSIZE in storage.
    #   sstore(0, msize())
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=Op.PUSH0, value=0x1)
            + Op.MCOPY(
                dest_offset=Op.CALLDATALOAD(offset=Op.PUSH0),
                offset=Op.CALLDATALOAD(offset=0x20),
                size=Op.CALLDATALOAD(offset=0x40),
            )
            + Op.SSTORE(key=Op.PUSH0, value=Op.MSIZE)
            + Op.STOP
        ),
        storage={0x0: 0xFA11ED},
        address=Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
