"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml
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
    ["tests/static/state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f2f2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f4f2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000faf2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f1f4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f2f4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f4f4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000faf4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f1fa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f2fa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f4fa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000fafa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fd",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fe",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000ff",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f0",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f5",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f0f1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f5f1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f0f2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f5f2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f0f4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f5f4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f0fa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f5fa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000060baccfa57",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f4",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fa",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f1f1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f2f1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f4f1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000faf1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000f1f2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f1",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f2",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
                ),
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000060006"): Account(
                    storage={0: 24743}
                ),
                Address("0x000000000000000000000000000000000060bacc"): Account(
                    storage={0: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 10}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_base_fee_diff_places(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
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
        gas_limit=4503599627370496,
    )

    # Source: Yul
    # {
    #    // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #
    #    // Here the result is is mload(0). We want to run it, but
    #    // prefix it with a zero so we'll be safe from being considered
    #    // an invalid program.
    #    //
    #    // If we use this as a constructor the result will be
    #    // the code of the created contract, but we can live
    #    // with that. We won't call it.
    #    mstore(0x40, mload(0x00))
    #    return(0x3F, 0x21)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.MSTORE(offset=0x40, value=Op.MLOAD(offset=0x0))
            + Op.RETURN(offset=0x3F, size=0x21)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   // basefee is still not supported in Yul 0.8.5
    #
    #
    #   mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.INVALID
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0x0000000000000000000000000000000000060006"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #
    #    // Here the result is is mload(0).
    #    return(0x00, 0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000020c0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #    sstore(0,mload(0))
    #    revert(0,0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000060bacc"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let addr := 0x20C0DE
    #    let length := extcodesize(addr)
    #
    #    // Read the code from 0x20C0DE
    #    extcodecopy(addr, 0, 0, length)
    #
    #    // Return this memory as the code for the contract
    #    return(0, length)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH3[0x20C0DE]
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.RETURN
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000c0dec0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(call(gas(), 0xca11, 0, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x15,
                condition=Op.ISZERO(
                    Op.CALL(
                        gas=Op.GAS,
                        address=0xCA11,
                        value=Op.DUP1,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100f1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(callcode(gas(), 0xca11, 0, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x15,
                condition=Op.ISZERO(
                    Op.CALLCODE(
                        gas=Op.GAS,
                        address=0xCA11,
                        value=Op.DUP1,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100f2"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(delegatecall(gas(), 0xca11, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x14,
                condition=Op.ISZERO(
                    Op.DELEGATECALL(
                        gas=Op.GAS,
                        address=0xCA11,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100f4"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(staticcall(gas(), 0xca11, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x14,
                condition=Op.ISZERO(
                    Op.STATICCALL(
                        gas=Op.GAS,
                        address=0xCA11,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100fa"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    selfdestruct(0)
    # }
    pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x0),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000deaddead"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let depth := calldataload(0)
    #
    #    if eq(depth,0) {
    #        // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #        return(0, 0x20)
    #    }
    #
    #    // Dig deeper
    #    mstore(0, sub(depth,1))
    #
    #    // Call yourself with depth-1
    #    if iszero(call(gas(), 0x60BACCFA57, 0, 0, 0x20, 0, 0x20)) {
    #       // Propagate failure if we failed
    #       revert(0, 0x20)
    #    }
    #
    #    // Propagate success
    #    return (0, 0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.JUMPI(pc=0x2D, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.MSTORE(offset=0x0, value=Op.SUB)
            + Op.JUMPI(
                pc=0x27,
                condition=Op.ISZERO(
                    Op.CALL(
                        gas=Op.GAS,
                        address=0x60BACCFA57,
                        value=Op.DUP1,
                        args_offset=Op.DUP2,
                        args_size=Op.DUP2,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000060baccfa57"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000, nonce=1)
    # Source: Yul
    # {
    #    let action := calldataload(4)
    #    let res := 1   // If the result of a call is revert, revert here too
    #    let addr := 1  // If the result of CREATE[2] is zero, it reverted
    #
    #    // For when we need code in our memory
    #    let codeBuffer := 0x20
    #    // When running the template in the constructor
    #    let codeLength := extcodesize(0xC0DE)
    #    // When running the template in the created code
    #    let codeLength2 := extcodesize(0xC0DEC0DE)
    #
    #    // Goat should be overwritten
    #    mstore(0, 0x60A7)
    #
    #    switch action
    #    case 0 {  // run the code snippet as normal code
    #       // basefee is still not supported in Yul 0.8.5
    #
    #
    #   mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #    }
    #
    #    // One level of call stack
    #    case 0xF1 {  // call a contract to run this code
    #       res := call(gas(), 0xca11, 0, 0, 0, 0, 0x20) // call template code
    #    }
    #    case 0xF2 {  // callcode a contract to run this code
    # ... (290 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x60A7)
            + Op.PUSH1[0x1]
            + Op.DUP1
            + Op.CALLDATALOAD(offset=0x4)
            + Op.EXTCODESIZE(address=0xC0DEC0DE)
            + Op.PUSH1[0x20]
            + Op.EXTCODESIZE(address=0xC0DE)
            + Op.JUMPI(pc=0x58A, condition=Op.ISZERO(Op.DUP4))
            + Op.JUMPI(pc=0x574, condition=Op.EQ(0xF1, Op.DUP4))
            + Op.JUMPI(pc=0x55E, condition=Op.EQ(0xF2, Op.DUP4))
            + Op.JUMPI(pc=0x549, condition=Op.EQ(0xF4, Op.DUP4))
            + Op.JUMPI(pc=0x534, condition=Op.EQ(0xFA, Op.DUP4))
            + Op.JUMPI(pc=0x51C, condition=Op.EQ(0xF1F1, Op.DUP4))
            + Op.JUMPI(pc=0x504, condition=Op.EQ(0xF2F1, Op.DUP4))
            + Op.JUMPI(pc=0x4ED, condition=Op.EQ(0xF4F1, Op.DUP4))
            + Op.JUMPI(pc=0x4D6, condition=Op.EQ(0xFAF1, Op.DUP4))
            + Op.JUMPI(pc=0x4BE, condition=Op.EQ(0xF1F2, Op.DUP4))
            + Op.JUMPI(pc=0x4A6, condition=Op.EQ(0xF2F2, Op.DUP4))
            + Op.JUMPI(pc=0x48F, condition=Op.EQ(0xF4F2, Op.DUP4))
            + Op.JUMPI(pc=0x478, condition=Op.EQ(0xFAF2, Op.DUP4))
            + Op.JUMPI(pc=0x460, condition=Op.EQ(0xF1F4, Op.DUP4))
            + Op.JUMPI(pc=0x448, condition=Op.EQ(0xF2F4, Op.DUP4))
            + Op.JUMPI(pc=0x431, condition=Op.EQ(0xF4F4, Op.DUP4))
            + Op.JUMPI(pc=0x41A, condition=Op.EQ(0xFAF4, Op.DUP4))
            + Op.JUMPI(pc=0x402, condition=Op.EQ(0xF1FA, Op.DUP4))
            + Op.JUMPI(pc=0x3EA, condition=Op.EQ(0xF2FA, Op.DUP4))
            + Op.JUMPI(pc=0x3D3, condition=Op.EQ(0xF4FA, Op.DUP4))
            + Op.JUMPI(pc=0x3BC, condition=Op.EQ(0xFAFA, Op.DUP4))
            + Op.JUMPI(pc=0x384, condition=Op.EQ(0xFD, Op.DUP4))
            + Op.JUMPI(pc=0x34A, condition=Op.EQ(0xFE, Op.DUP4))
            + Op.JUMPI(pc=0x311, condition=Op.EQ(0xFF, Op.DUP4))
            + Op.JUMPI(pc=0x2EB, condition=Op.EQ(0xF0, Op.DUP4))
            + Op.JUMPI(pc=0x2C1, condition=Op.EQ(0xF5, Op.DUP4))
            + Op.POP
            + Op.JUMPI(pc=0x297, condition=Op.EQ(0xF0F1, Op.DUP3))
            + Op.JUMPI(pc=0x26B, condition=Op.EQ(0xF5F1, Op.DUP3))
            + Op.JUMPI(pc=0x248, condition=Op.EQ(0xF0F2, Op.DUP3))
            + Op.JUMPI(pc=0x223, condition=Op.EQ(0xF5F2, Op.DUP3))
            + Op.JUMPI(pc=0x201, condition=Op.EQ(0xF0F4, Op.DUP3))
            + Op.JUMPI(pc=0x1DD, condition=Op.EQ(0xF5F4, Op.DUP3))
            + Op.JUMPI(pc=0x1B4, condition=Op.EQ(0xF0FA, Op.DUP3))
            + Op.JUMPI(pc=0x189, condition=Op.EQ(0xF5FA, Op.DUP3))
            + Op.POP
            + Op.POP
            + Op.PUSH5[0x60BACCFA57]
            + Op.JUMPI(pc=0x16E, condition=Op.EQ)
            + Op.MSTORE(offset=0x0, value=0xBAD0BAD0BAD0)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x168, condition=Op.ISZERO)
            + Op.JUMPI(pc=0x168, condition=Op.ISZERO)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x0, value=0x3FF)
            + Op.CALL(
                gas=Op.GAS,
                address=0x60BACCFA57,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH2[0x5A17]
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.DUP3
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE2
            + Op.STATICCALL(
                gas=Op.GAS,
                address=Op.DUP5,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.DUP2
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.SWAP3
            + Op.POP
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE
            + Op.STATICCALL(
                gas=Op.GAS,
                address=Op.DUP5,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH2[0x5A17]
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.DUP3
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.CREATE2
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.DUP5,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.DUP2
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.SWAP3
            + Op.POP
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.CREATE
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.DUP5,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH2[0x5A17]
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.DUP3
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.CREATE2
            + Op.CALLCODE(
                gas=Op.GAS,
                address=Op.DUP6,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.DUP2
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.SWAP3
            + Op.POP
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.CREATE
            + Op.CALLCODE(
                gas=Op.GAS,
                address=Op.DUP6,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH2[0x5A17]
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.DUP3
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE2
            + Op.CALL(
                gas=Op.GAS,
                address=Op.DUP6,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.DUP2
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.SWAP3
            + Op.POP
            + Op.PUSH4[0xC0DEC0DE]
            + Op.EXTCODECOPY
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE
            + Op.CALL(
                gas=Op.GAS,
                address=Op.DUP6,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP3
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x5A17]
            + Op.SWAP3
            + Op.SWAP4
            + Op.POP
            + Op.EXTCODECOPY(
                address=0xC0DE,
                dest_offset=Op.DUP3,
                offset=0x0,
                size=Op.DUP2,
            )
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE2
            + Op.SWAP1
            + Op.EXTCODECOPY(
                address=Op.DUP5,
                dest_offset=0x0,
                offset=0x1,
                size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP4
            + Op.SWAP5
            + Op.POP
            + Op.SWAP2
            + Op.POP
            + Op.POP
            + Op.EXTCODECOPY(
                address=0xC0DE,
                dest_offset=Op.DUP3,
                offset=0x0,
                size=Op.DUP2,
            )
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE
            + Op.SWAP1
            + Op.EXTCODECOPY(
                address=Op.DUP5,
                dest_offset=0x0,
                offset=0x1,
                size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xDEADDEAD,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMPI(
                pc=0x156,
                condition=Op.EQ(Op.SLOAD(key=0x0), Op.MLOAD(offset=0x0)),
            )
            + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.POP(
                Op.CALL(
                    gas=0x61A8,
                    address=0x60006,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMPI(
                pc=0x156,
                condition=Op.EQ(Op.SLOAD(key=0x0), Op.MLOAD(offset=0x0)),
            )
            + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x60BACC,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMPI(
                pc=0x156,
                condition=Op.EQ(Op.SLOAD(key=0x0), Op.MLOAD(offset=0x0)),
            )
            + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.STATICCALL(
                gas=Op.GAS,
                address=0xCA1100FA,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA1100FA,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA1100FA,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xCA1100FA,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.STATICCALL(
                gas=Op.GAS,
                address=0xCA1100F4,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA1100F4,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA1100F4,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xCA1100F4,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.STATICCALL(
                gas=Op.GAS,
                address=0xCA1100F2,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA1100F2,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA1100F2,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xCA1100F2,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.STATICCALL(
                gas=Op.GAS,
                address=0xCA1100F1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA1100F1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA1100F1,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xCA1100F1,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.STATICCALL(
                gas=Op.GAS,
                address=0xCA11,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA11,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA11,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xCA11,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMP(pc=0x156)
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=4503599627370496,
        gas_price=2000,
        nonce=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
